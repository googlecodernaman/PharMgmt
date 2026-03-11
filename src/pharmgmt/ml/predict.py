"""ML inference for pharmacy bill parsing — production-ready predictor.

Loads trained models (PyTorch or ONNX) and provides:
1. Bill type classification from document text
2. Token-level field extraction from text lines

Designed for low-end CPU inference. Falls back to rule-based parser
if models are unavailable.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger("pharmgmt.ml")

# Try importing optional dependencies
_HAS_TORCH = False
_HAS_ONNX = False

try:
    import torch
    _HAS_TORCH = True
except ImportError:
    pass

try:
    import onnxruntime as ort
    _HAS_ONNX = True
except ImportError:
    pass

from pharmgmt.ml.data_generator import (
    BIO_TAGS,
    BILL_TYPES,
    BILL_TYPE_TO_IDX,
    IDX_TO_TAG,
    TAG_TO_IDX,
    generate_token_features,
)

MODELS_DIR = Path(__file__).parent / "trained_models"


class MLPredictor:
    """Unified ML predictor for bill type classification and field extraction.

    Loads models lazily on first use. Supports both PyTorch and ONNX backends.
    ONNX is preferred for deployment (no PyTorch dependency needed).
    """

    def __init__(self, models_dir: str | Path | None = None):
        self.models_dir = Path(models_dir) if models_dir else MODELS_DIR
        self._field_extractor = None
        self._bill_classifier = None
        self._vocab = None
        self._crf_params = None
        self._onnx_emissions = None
        self._onnx_classifier = None
        self._loaded = False

    @property
    def available(self) -> bool:
        """Check if trained models exist."""
        if self._loaded:
            return True
        fe_pt = self.models_dir / "field_extractor.pt"
        fe_onnx = self.models_dir / "field_extractor_emissions.onnx"
        return fe_pt.exists() or fe_onnx.exists()

    def load(self):
        """Load models. Prefers ONNX for lightweight inference."""
        if self._loaded:
            return

        # Try ONNX first
        onnx_emissions = self.models_dir / "field_extractor_emissions.onnx"
        onnx_classifier = self.models_dir / "bill_classifier.onnx"
        crf_path = self.models_dir / "field_extractor_crf_params.json"

        if _HAS_ONNX and onnx_emissions.exists():
            logger.info("Loading ONNX models from %s", self.models_dir)
            self._onnx_emissions = ort.InferenceSession(
                str(onnx_emissions),
                providers=["CPUExecutionProvider"],
            )
            if crf_path.exists():
                with open(crf_path) as f:
                    self._crf_params = json.load(f)

            if onnx_classifier.exists():
                self._onnx_classifier = ort.InferenceSession(
                    str(onnx_classifier),
                    providers=["CPUExecutionProvider"],
                )

            # Load vocab for classifier
            classifier_pt = self.models_dir / "bill_classifier.pt"
            if _HAS_TORCH and classifier_pt.exists():
                data = torch.load(classifier_pt, map_location="cpu", weights_only=False)
                self._vocab = data.get("vocab", {})

            self._loaded = True
            logger.info("ONNX models loaded successfully")
            return

        # Fall back to PyTorch
        if _HAS_TORCH:
            fe_path = self.models_dir / "field_extractor.pt"
            cl_path = self.models_dir / "bill_classifier.pt"

            if fe_path.exists():
                from pharmgmt.ml.models import FieldExtractor
                data = torch.load(fe_path, map_location="cpu", weights_only=False)
                self._field_extractor = FieldExtractor(num_tags=data["num_tags"])
                self._field_extractor.load_state_dict(data["model_state"])
                self._field_extractor.eval()
                logger.info("Loaded PyTorch field extractor")

            if cl_path.exists():
                from pharmgmt.ml.models import BillTypeClassifier
                data = torch.load(cl_path, map_location="cpu", weights_only=False)
                self._vocab = data.get("vocab", {})
                self._bill_classifier = BillTypeClassifier(
                    vocab_size=len(self._vocab),
                    num_classes=len(BILL_TYPES),
                )
                self._bill_classifier.load_state_dict(data["model_state"])
                self._bill_classifier.eval()
                logger.info("Loaded PyTorch bill classifier")

            self._loaded = True

    def classify_bill_type(self, text: str) -> tuple[str, float]:
        """Classify bill type from document text.

        Args:
            text: Full document text (first ~2000 chars recommended).

        Returns:
            Tuple of (bill_type_string, confidence_score).
        """
        if not self._loaded:
            self.load()

        tokens = text.lower().split()[:512]

        if self._onnx_classifier and self._vocab:
            token_ids = np.zeros((1, 512), dtype=np.int64)
            for i, tok in enumerate(tokens):
                token_ids[0, i] = self._vocab.get(tok, 1)

            outputs = self._onnx_classifier.run(None, {"token_ids": token_ids})
            logits = outputs[0][0]

            # Softmax
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / exp_logits.sum()

            idx = int(np.argmax(probs))
            return BILL_TYPES[idx], float(probs[idx])

        if _HAS_TORCH and self._bill_classifier and self._vocab:
            token_ids = torch.zeros(1, 512, dtype=torch.long)
            for i, tok in enumerate(tokens):
                token_ids[0, i] = self._vocab.get(tok, 1)

            with torch.no_grad():
                logits = self._bill_classifier(token_ids)
                probs = torch.softmax(logits, dim=1)
                conf, idx = probs.max(dim=1)
                return BILL_TYPES[idx.item()], conf.item()

        return "unknown", 0.0

    def extract_fields(self, text_line: str) -> dict:
        """Extract fields from a single text line using ML model.

        Args:
            text_line: A single line of text from a PDF.

        Returns:
            Dict with extracted canonical fields and confidence.
        """
        if not self._loaded:
            self.load()

        tokens = text_line.split()
        if not tokens:
            return {"fields": {}, "confidence": 0.0, "tags": []}

        # Prepare features
        features = generate_token_features(tokens)
        seq_len = min(len(tokens), 64)

        # Prepare char IDs
        max_char = 20
        char_ids = np.zeros((1, seq_len, max_char), dtype=np.int64)
        feat_array = np.zeros((1, seq_len, 11), dtype=np.float32)

        for i in range(seq_len):
            feat_array[0, i] = features[i]
            for j, ch in enumerate(tokens[i][:max_char]):
                char_ids[0, i, j] = min(ord(ch), 255)

        tags = self._predict_tags(feat_array, char_ids, seq_len)

        # Convert tags to fields
        fields = self._tags_to_fields(tokens[:seq_len], tags)
        confidence = sum(1 for t in tags if t != "O") / max(len(tags), 1)

        return {
            "fields": fields,
            "confidence": round(confidence, 3),
            "tags": tags,
        }

    def _predict_tags(
        self, features: np.ndarray, char_ids: np.ndarray, seq_len: int
    ) -> list[str]:
        """Run model inference to get BIO tag sequence."""

        if self._onnx_emissions is not None:
            emissions = self._onnx_emissions.run(
                None, {"features": features, "char_ids": char_ids}
            )[0]  # [1, seq_len, num_tags]

            if self._crf_params:
                tag_indices = self._viterbi_decode(
                    emissions[0, :seq_len],
                    np.array(self._crf_params["transitions"]),
                    np.array(self._crf_params["start_transitions"]),
                    np.array(self._crf_params["end_transitions"]),
                )
            else:
                tag_indices = np.argmax(emissions[0, :seq_len], axis=1).tolist()

            return [IDX_TO_TAG.get(i, "O") for i in tag_indices]

        if _HAS_TORCH and self._field_extractor is not None:
            with torch.no_grad():
                feat_t = torch.from_numpy(features)
                char_t = torch.from_numpy(char_ids)
                mask = torch.zeros(1, features.shape[1], dtype=torch.bool)
                mask[0, :seq_len] = True

                preds = self._field_extractor.predict(feat_t, char_t, mask)
                return [IDX_TO_TAG.get(i, "O") for i in preds[0]]

        return ["O"] * seq_len

    @staticmethod
    def _viterbi_decode(
        emissions: np.ndarray,
        transitions: np.ndarray,
        start_trans: np.ndarray,
        end_trans: np.ndarray,
    ) -> list[int]:
        """Numpy-based Viterbi decoding (no PyTorch needed)."""
        seq_len, num_tags = emissions.shape
        score = start_trans + emissions[0]
        history = []

        for t in range(1, seq_len):
            broadcast_score = score[:, np.newaxis]  # [tags, 1]
            broadcast_emission = emissions[t][np.newaxis, :]  # [1, tags]
            next_score = broadcast_score + transitions + broadcast_emission
            indices = np.argmax(next_score, axis=0)
            history.append(indices)
            score = next_score[indices, np.arange(num_tags)]

        score += end_trans
        best_last = int(np.argmax(score))
        best_tags = [best_last]

        for hist in reversed(history):
            best_tags.append(int(hist[best_tags[-1]]))
        best_tags.reverse()

        return best_tags

    @staticmethod
    def _tags_to_fields(tokens: list[str], tags: list[str]) -> dict:
        """Convert BIO tags to canonical field dict.

        Concatenates consecutive B/I tagged tokens into field values.
        """
        fields = {}
        current_field = None
        current_tokens = []

        for tok, tag in zip(tokens, tags):
            if tag.startswith("B-"):
                # Save previous field
                if current_field and current_tokens:
                    fields[current_field] = _format_field_value(
                        current_field, " ".join(current_tokens)
                    )
                current_field = tag[2:]
                current_tokens = [tok]
            elif tag.startswith("I-") and current_field == tag[2:]:
                current_tokens.append(tok)
            else:
                if current_field and current_tokens:
                    fields[current_field] = _format_field_value(
                        current_field, " ".join(current_tokens)
                    )
                current_field = None
                current_tokens = []

        # Last field
        if current_field and current_tokens:
            fields[current_field] = _format_field_value(
                current_field, " ".join(current_tokens)
            )

        return fields


def _format_field_value(field_name: str, raw_value: str):
    """Convert raw extracted text to the appropriate data type."""
    from pharmgmt.parsing.normalizers import normalize_date, normalize_money, parse_quantity

    if field_name == "expiry":
        date_val, _ = normalize_date(raw_value)
        return raw_value if date_val is None else raw_value
    elif field_name == "price_paise":
        return normalize_money(raw_value)
    elif field_name.endswith("_qty"):
        return parse_quantity(raw_value)
    else:
        return raw_value


# Singleton instance
_predictor: Optional[MLPredictor] = None


def get_predictor(models_dir: str | Path | None = None) -> MLPredictor:
    """Get or create the singleton ML predictor."""
    global _predictor
    if _predictor is None:
        _predictor = MLPredictor(models_dir)
    return _predictor
