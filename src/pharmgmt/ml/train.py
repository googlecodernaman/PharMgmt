"""Training script for pharmacy bill parsing models.

Usage:
    python -m pharmgmt.ml.train --samples-dir ./samples --epochs 50 --device cuda

Trains both:
1. BillTypeClassifier — document-level bill type classification
2. FieldExtractor — token-level BIO field extraction (BiLSTM-CRF)

Exports trained models to ONNX for low-end device deployment.
"""

import argparse
import json
import logging
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# Ensure pharmgmt is importable
src_dir = str(Path(__file__).parent.parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from pharmgmt.ml.data_generator import (
    BIO_TAGS,
    BILL_TYPES,
    BILL_TYPE_TO_IDX,
    FIELD_LABELS,
    IDX_TO_TAG,
    TAG_TO_IDX,
    generate_token_features,
    generate_training_data_from_pdfs,
)
from pharmgmt.ml.models import BillTypeClassifier, FieldExtractor

logger = logging.getLogger("pharmgmt.ml.train")

MAX_SEQ_LEN = 64
MAX_CHAR_LEN = 20
MAX_DOC_TOKENS = 512

# ─── Datasets ────────────────────────────────────────────────────────


class TokenTagDataset(Dataset):
    """Dataset for BiLSTM-CRF token tagging."""

    def __init__(self, samples: list[dict], max_seq_len: int = MAX_SEQ_LEN,
                 max_char_len: int = MAX_CHAR_LEN):
        self.samples = samples
        self.max_seq_len = max_seq_len
        self.max_char_len = max_char_len

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        tokens = sample["tokens"][:self.max_seq_len]
        tags = sample["tags"][:self.max_seq_len]
        seq_len = len(tokens)

        # Token features
        feats = generate_token_features(tokens)
        feat_tensor = torch.zeros(self.max_seq_len, len(feats[0]) if feats else 11)
        for i, f in enumerate(feats):
            feat_tensor[i] = torch.tensor(f, dtype=torch.float32)

        # Tag indices
        tag_ids = torch.zeros(self.max_seq_len, dtype=torch.long)
        for i, t in enumerate(tags):
            tag_ids[i] = TAG_TO_IDX.get(t, 0)

        # Character IDs
        char_ids = torch.zeros(self.max_seq_len, self.max_char_len, dtype=torch.long)
        for i, tok in enumerate(tokens):
            for j, ch in enumerate(tok[:self.max_char_len]):
                char_ids[i, j] = min(ord(ch), 255)

        # Mask
        mask = torch.zeros(self.max_seq_len, dtype=torch.bool)
        mask[:seq_len] = True

        return feat_tensor, char_ids, tag_ids, mask


class BillTypeDataset(Dataset):
    """Dataset for bill type classification."""

    def __init__(self, samples: list[dict], vocab: dict, max_tokens: int = MAX_DOC_TOKENS):
        self.samples = samples
        self.vocab = vocab
        self.max_tokens = max_tokens

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        text = sample["text"].lower()
        tokens = text.split()[:self.max_tokens]

        token_ids = torch.zeros(self.max_tokens, dtype=torch.long)
        for i, tok in enumerate(tokens):
            token_ids[i] = self.vocab.get(tok, 1)  # 1 = UNK

        label = BILL_TYPE_TO_IDX.get(sample["bill_type"], len(BILL_TYPES) - 1)
        return token_ids, torch.tensor(label, dtype=torch.long)


# ─── Vocabulary ──────────────────────────────────────────────────────


def build_vocab(samples: list[dict], min_freq: int = 2, max_vocab: int = 10000) -> dict:
    """Build vocabulary from document samples.

    Args:
        samples: List of {text, bill_type} dicts.
        min_freq: Minimum word frequency for inclusion.
        max_vocab: Maximum vocabulary size.

    Returns:
        Dict mapping word → index.
    """
    freq = {}
    for s in samples:
        for tok in s["text"].lower().split():
            freq[tok] = freq.get(tok, 0) + 1

    # Sort by frequency descending
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])

    vocab = {"<PAD>": 0, "<UNK>": 1}
    for word, count in sorted_words:
        if count < min_freq:
            break
        vocab[word] = len(vocab)
        if len(vocab) >= max_vocab:
            break

    logger.info("Built vocab: %d words (min_freq=%d)", len(vocab), min_freq)
    return vocab


# ─── Data Augmentation ───────────────────────────────────────────────


def augment_token_samples(samples: list[dict], factor: int = 3) -> list[dict]:
    """Augment training data with perturbations.

    Augmentation strategies:
    - Random token dropout (replace with <UNK>)
    - Token swap within numeric/text regions
    - Add noise tokens

    Args:
        samples: Original token samples.
        factor: Number of augmented copies per sample.

    Returns:
        Augmented sample list (original + augmented).
    """
    augmented = list(samples)

    for _ in range(factor):
        for sample in samples:
            tokens = list(sample["tokens"])
            tags = list(sample["tags"])
            n = len(tokens)
            if n < 4:
                continue

            new_tokens = list(tokens)
            new_tags = list(tags)

            # Strategy 1: Random token dropout (5% chance per token)
            for i in range(n):
                if random.random() < 0.05 and tags[i] == "O":
                    new_tokens[i] = ""

            # Strategy 2: Add spacing variations
            for i in range(min(2, n)):
                idx = random.randint(0, n - 1)
                if new_tags[idx] == "O" and new_tokens[idx]:
                    # Add or remove trailing period
                    if new_tokens[idx].endswith("."):
                        new_tokens[idx] = new_tokens[idx][:-1]
                    elif random.random() < 0.3:
                        new_tokens[idx] += "."

            # Strategy 3: Number format variations (commas)
            for i in range(n):
                tok = new_tokens[i]
                if tok and tok.replace(",", "").replace(".", "").isdigit():
                    if "," in tok and random.random() < 0.3:
                        new_tokens[i] = tok.replace(",", "")
                    elif "," not in tok and len(tok) > 3 and random.random() < 0.2:
                        # Add Indian comma format
                        clean = tok.replace(",", "")
                        if "." not in clean and len(clean) > 3:
                            new_tokens[i] = clean[:-3] + "," + clean[-3:]

            # Filter out empty tokens
            filtered = [(t, g) for t, g in zip(new_tokens, new_tags) if t]
            if len(filtered) >= 3:
                augmented.append({
                    "tokens": [t for t, _ in filtered],
                    "tags": [g for _, g in filtered],
                    "confidence": sample.get("confidence", 0.5),
                    "bill_type": sample["bill_type"],
                    "file": sample.get("file", "augmented"),
                })

    logger.info("Augmented: %d → %d samples", len(samples), len(augmented))
    return augmented


# ─── Training Logic ──────────────────────────────────────────────────


def train_field_extractor(
    train_data: list[dict],
    val_data: list[dict],
    device: torch.device,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 1e-3,
    patience: int = 10,
) -> FieldExtractor:
    """Train the BiLSTM-CRF field extractor.

    Args:
        train_data: Training token samples.
        val_data: Validation token samples.
        device: torch device.
        epochs: Maximum training epochs.
        batch_size: Batch size.
        lr: Learning rate.
        patience: Early stopping patience.

    Returns:
        Trained FieldExtractor model.
    """
    num_tags = len(BIO_TAGS)
    model = FieldExtractor(num_tags=num_tags).to(device)

    train_ds = TokenTagDataset(train_data)
    val_ds = TokenTagDataset(val_data)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    best_val_loss = float("inf")
    best_state = None
    no_improve = 0

    for epoch in range(1, epochs + 1):
        # Train
        model.train()
        train_loss = 0.0
        for feats, chars, tags, mask in train_loader:
            feats, chars, tags, mask = (
                feats.to(device), chars.to(device),
                tags.to(device), mask.to(device),
            )
            optimizer.zero_grad()
            loss = model(feats, chars, tags, mask)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            train_loss += loss.item()

        train_loss /= max(len(train_loader), 1)

        # Validate
        model.eval()
        val_loss = 0.0
        correct_tags = 0
        total_tags = 0

        with torch.no_grad():
            for feats, chars, tags, mask in val_loader:
                feats, chars, tags, mask = (
                    feats.to(device), chars.to(device),
                    tags.to(device), mask.to(device),
                )
                loss = model(feats, chars, tags, mask)
                val_loss += loss.item()

                # Accuracy
                preds = model.predict(feats, chars, mask)
                for b, pred_seq in enumerate(preds):
                    length = int(mask[b].sum().item())
                    gt = tags[b, :length].cpu().tolist()
                    for p, g in zip(pred_seq, gt):
                        total_tags += 1
                        if p == g:
                            correct_tags += 1

        val_loss /= max(len(val_loader), 1)
        accuracy = correct_tags / max(total_tags, 1)
        scheduler.step(val_loss)

        logger.info(
            "Epoch %d/%d — train_loss: %.4f, val_loss: %.4f, accuracy: %.3f",
            epoch, epochs, train_loss, val_loss, accuracy,
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                logger.info("Early stopping at epoch %d", epoch)
                break

    if best_state:
        model.load_state_dict(best_state)

    return model


def train_bill_classifier(
    train_data: list[dict],
    val_data: list[dict],
    vocab: dict,
    device: torch.device,
    epochs: int = 30,
    batch_size: int = 16,
    lr: float = 1e-3,
) -> BillTypeClassifier:
    """Train the bill type classifier.

    Args:
        train_data: Training document samples.
        val_data: Validation document samples.
        vocab: Word → index vocabulary.
        device: torch device.
        epochs: Maximum epochs.
        batch_size: Batch size.
        lr: Learning rate.

    Returns:
        Trained BillTypeClassifier.
    """
    model = BillTypeClassifier(
        vocab_size=len(vocab),
        num_classes=len(BILL_TYPES),
    ).to(device)

    train_ds = BillTypeDataset(train_data, vocab)
    val_ds = BillTypeDataset(val_data, vocab)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    optimizer = optim.AdamW(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    best_acc = 0.0
    best_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for token_ids, labels in train_loader:
            token_ids, labels = token_ids.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(token_ids)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        train_loss /= max(len(train_loader), 1)

        # Validate
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for token_ids, labels in val_loader:
                token_ids, labels = token_ids.to(device), labels.to(device)
                logits = model(token_ids)
                preds = logits.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        acc = correct / max(total, 1)
        logger.info("ClassifierEpoch %d/%d — loss: %.4f, val_acc: %.3f", epoch, epochs, train_loss, acc)

        if acc > best_acc:
            best_acc = acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_state:
        model.load_state_dict(best_state)

    return model


# ─── Evaluation ──────────────────────────────────────────────────────


def evaluate_field_extractor(model: FieldExtractor, data: list[dict], device: torch.device) -> dict:
    """Evaluate field extractor on a dataset.

    Returns per-field precision, recall, F1.
    """
    model.eval()
    ds = TokenTagDataset(data)
    loader = DataLoader(ds, batch_size=32)

    # Collect predictions
    all_preds = []
    all_golds = []

    with torch.no_grad():
        for feats, chars, tags, mask in loader:
            feats, chars, mask = feats.to(device), chars.to(device), mask.to(device)
            preds = model.predict(feats, chars, mask)

            for b, pred_seq in enumerate(preds):
                length = int(mask[b].sum().item())
                gold = tags[b, :length].tolist()
                all_preds.extend(pred_seq[:length])
                all_golds.extend(gold)

    # Compute per-field metrics
    metrics = {}
    for field in FIELD_LABELS:
        b_tag = TAG_TO_IDX.get(f"B-{field}", -1)
        i_tag = TAG_TO_IDX.get(f"I-{field}", -1)
        tags_set = {b_tag, i_tag}

        tp = sum(1 for p, g in zip(all_preds, all_golds) if p in tags_set and g in tags_set and p == g)
        fp = sum(1 for p, g in zip(all_preds, all_golds) if p in tags_set and g not in tags_set)
        fn = sum(1 for p, g in zip(all_preds, all_golds) if p not in tags_set and g in tags_set)

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-8)
        metrics[field] = {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}

    # Overall accuracy
    correct = sum(1 for p, g in zip(all_preds, all_golds) if p == g)
    metrics["_overall"] = {
        "accuracy": round(correct / max(len(all_golds), 1), 3),
        "total_tokens": len(all_golds),
    }

    return metrics


# ─── ONNX Export ─────────────────────────────────────────────────────


def export_field_extractor_onnx(model: FieldExtractor, output_path: str):
    """Export field extractor to ONNX for CPU inference.

    NOTE: CRF decode is not directly exportable to ONNX.
    We export the emission layer only, and implement Viterbi decode in Python.
    The CRF transition parameters are saved separately.
    """
    model.eval()
    model.cpu()

    # Export emissions-only variant
    class EmissionsModel(nn.Module):
        def __init__(self, extractor):
            super().__init__()
            self.char_embedding = extractor.char_embedding
            self.char_lstm = extractor.char_lstm
            self.lstm = extractor.lstm
            self.dropout = extractor.dropout
            self.hidden2tag = extractor.hidden2tag

        def forward(self, features, char_ids):
            batch, seq_len, max_char = char_ids.shape
            flat = char_ids.view(batch * seq_len, max_char)
            emb = self.char_embedding(flat)
            _, (h, _) = self.char_lstm(emb)
            h = torch.cat([h[0], h[1]], dim=1)
            char_enc = h.view(batch, seq_len, -1)
            combined = torch.cat([features, char_enc], dim=2)
            lstm_out, _ = self.lstm(combined)
            return self.hidden2tag(lstm_out)

    emissions_model = EmissionsModel(model)
    emissions_model.eval()

    dummy_features = torch.zeros(1, MAX_SEQ_LEN, 11)
    dummy_chars = torch.zeros(1, MAX_SEQ_LEN, MAX_CHAR_LEN, dtype=torch.long)

    onnx_path = output_path.replace(".pt", "_emissions.onnx")
    torch.onnx.export(
        emissions_model,
        (dummy_features, dummy_chars),
        onnx_path,
        input_names=["features", "char_ids"],
        output_names=["emissions"],
        dynamic_axes={
            "features": {0: "batch", 1: "seq_len"},
            "char_ids": {0: "batch", 1: "seq_len"},
            "emissions": {0: "batch", 1: "seq_len"},
        },
        opset_version=14,
    )

    # Save CRF parameters separately
    crf_path = output_path.replace(".pt", "_crf_params.json")
    crf_params = {
        "transitions": model.crf.transitions.detach().cpu().numpy().tolist(),
        "start_transitions": model.crf.start_transitions.detach().cpu().numpy().tolist(),
        "end_transitions": model.crf.end_transitions.detach().cpu().numpy().tolist(),
    }
    with open(crf_path, "w") as f:
        json.dump(crf_params, f)

    logger.info("Exported emissions ONNX: %s", onnx_path)
    logger.info("Exported CRF params: %s", crf_path)


def export_classifier_onnx(model: BillTypeClassifier, output_path: str):
    """Export bill type classifier to ONNX."""
    model.eval()
    model.cpu()

    dummy = torch.zeros(1, MAX_DOC_TOKENS, dtype=torch.long)
    onnx_path = output_path.replace(".pt", ".onnx")

    torch.onnx.export(
        model,
        dummy,
        onnx_path,
        input_names=["token_ids"],
        output_names=["logits"],
        dynamic_axes={
            "token_ids": {0: "batch", 1: "seq_len"},
            "logits": {0: "batch"},
        },
        opset_version=14,
    )
    logger.info("Exported classifier ONNX: %s", onnx_path)


# ─── Main ────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Train pharmacy bill parsing models")
    parser.add_argument("--samples-dir", type=str, required=True, help="Path to samples/ directory")
    parser.add_argument("--output-dir", type=str, default=None, help="Model output directory")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--device", type=str, default="auto", help="Device: cuda, cpu, or auto")
    parser.add_argument("--augment", type=int, default=3, help="Data augmentation factor")
    parser.add_argument("--export-onnx", action="store_true", help="Export to ONNX after training")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    logger.info("Using device: %s", device)

    # Output directory
    if args.output_dir is None:
        args.output_dir = str(Path(__file__).parent / "trained_models")
    os.makedirs(args.output_dir, exist_ok=True)

    # Step 1: Generate training data
    logger.info("=" * 60)
    logger.info("STEP 1: Generating training data from PDFs...")
    logger.info("=" * 60)

    training_data_path = os.path.join(args.output_dir, "training_data.json")
    stats = generate_training_data_from_pdfs(
        args.samples_dir, training_data_path
    )
    logger.info("Data stats: %s", json.dumps(stats))

    with open(training_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    token_samples = data["token_samples"]
    doc_samples = data["doc_samples"]

    if not token_samples:
        logger.error("No training data generated! Check samples directory.")
        return

    # Step 2: Augment data
    logger.info("=" * 60)
    logger.info("STEP 2: Augmenting training data (factor=%d)...", args.augment)
    logger.info("=" * 60)

    augmented = augment_token_samples(token_samples, factor=args.augment)

    # Step 3: Train/val split (80/20)
    random.seed(42)
    random.shuffle(augmented)
    split = int(len(augmented) * 0.8)
    train_tokens = augmented[:split]
    val_tokens = augmented[split:]
    logger.info("Token data: %d train, %d val", len(train_tokens), len(val_tokens))

    # Step 4: Train Field Extractor
    logger.info("=" * 60)
    logger.info("STEP 3: Training FieldExtractor (BiLSTM-CRF)...")
    logger.info("=" * 60)

    field_model = train_field_extractor(
        train_tokens, val_tokens, device,
        epochs=args.epochs, batch_size=args.batch_size, lr=args.lr,
    )

    # Evaluate
    eval_metrics = evaluate_field_extractor(field_model, val_tokens, device)
    logger.info("Field extractor metrics: %s", json.dumps(eval_metrics, indent=2))

    # Save
    field_model_path = os.path.join(args.output_dir, "field_extractor.pt")
    torch.save({
        "model_state": field_model.state_dict(),
        "num_tags": len(BIO_TAGS),
        "bio_tags": BIO_TAGS,
        "tag_to_idx": TAG_TO_IDX,
        "metrics": eval_metrics,
    }, field_model_path)
    logger.info("Saved field extractor: %s", field_model_path)

    # Step 5: Train Bill Type Classifier
    if doc_samples:
        logger.info("=" * 60)
        logger.info("STEP 4: Training BillTypeClassifier...")
        logger.info("=" * 60)

        vocab = build_vocab(doc_samples, min_freq=1)

        random.shuffle(doc_samples)
        doc_split = int(len(doc_samples) * 0.8)
        train_docs = doc_samples[:doc_split]
        val_docs = doc_samples[doc_split:]

        classifier = train_bill_classifier(
            train_docs, val_docs, vocab, device,
            epochs=30, batch_size=min(16, len(train_docs)),
        )

        classifier_path = os.path.join(args.output_dir, "bill_classifier.pt")
        torch.save({
            "model_state": classifier.state_dict(),
            "vocab": vocab,
            "bill_types": BILL_TYPES,
        }, classifier_path)
        logger.info("Saved classifier: %s", classifier_path)
    else:
        logger.warning("No document samples for classifier training")

    # Step 6: Export ONNX
    if args.export_onnx:
        logger.info("=" * 60)
        logger.info("STEP 5: Exporting to ONNX...")
        logger.info("=" * 60)

        export_field_extractor_onnx(field_model, field_model_path)

        if doc_samples:
            export_classifier_onnx(classifier, classifier_path)
            vocab_json_path = os.path.join(args.output_dir, "vocab.json")
            with open(vocab_json_path, "w") as f:
                json.dump(vocab, f)
            logger.info("Saved vocab JSON: %s", vocab_json_path)

    # Save training config
    config_path = os.path.join(args.output_dir, "training_config.json")
    with open(config_path, "w") as f:
        json.dump({
            "samples_dir": args.samples_dir,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "augment_factor": args.augment,
            "device": str(device),
            "token_samples": len(token_samples),
            "augmented_samples": len(augmented),
            "doc_samples": len(doc_samples),
            "bio_tags": BIO_TAGS,
            "bill_types": BILL_TYPES,
            "eval_metrics": eval_metrics,
            "stats": stats,
        }, f, indent=2)

    logger.info("=" * 60)
    logger.info("Training complete! Models saved to: %s", args.output_dir)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
