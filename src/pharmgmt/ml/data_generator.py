"""Training data generation — extract labeled samples from PDFs using existing parser."""

import json
import logging
import os
import re
from pathlib import Path

import pdfplumber

logger = logging.getLogger("pharmgmt.ml")

# Canonical field labels for BIO tagging
FIELD_LABELS = [
    "product_name_raw", "packing", "batch_no", "expiry",
    "opening_qty", "receipt_qty", "total_qty", "issue_qty",
    "closing_qty", "price_paise", "near_expiry_qty",
]

# BIO tag set: O + B-field + I-field for each field
BIO_TAGS = ["O"]
for f in FIELD_LABELS:
    BIO_TAGS.append(f"B-{f}")
    BIO_TAGS.append(f"I-{f}")

TAG_TO_IDX = {t: i for i, t in enumerate(BIO_TAGS)}
IDX_TO_TAG = {i: t for t, i in TAG_TO_IDX.items()}

# Bill type labels
BILL_TYPES = ["batch_stock", "sales_stock", "short_sales", "unknown"]
BILL_TYPE_TO_IDX = {t: i for i, t in enumerate(BILL_TYPES)}


def extract_pdf_text(pdf_path: str) -> list[dict]:
    """Extract text and tables from PDF pages.

    Args:
        pdf_path: Path to PDF file.

    Returns:
        List of {page, text, tables} dicts.
    """
    results = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_data = {"page": i + 1, "text": "", "tables": []}
                try:
                    page_data["text"] = page.extract_text() or ""
                except Exception:
                    pass
                try:
                    page_data["tables"] = page.extract_tables() or []
                except Exception:
                    pass
                results.append(page_data)
    except Exception as e:
        logger.warning("Failed to read PDF %s: %s", pdf_path, e)
    return results


def _tokenize_line(line: str) -> list[str]:
    """Split a text line into tokens for BIO tagging."""
    return line.split()


def _is_numeric(s: str) -> bool:
    """Check if a string is numeric (allowing commas and decimals)."""
    cleaned = s.replace(",", "").replace("-", "")
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _is_date_like(s: str) -> bool:
    """Check if a string looks like a date."""
    return bool(re.match(
        r"^\d{1,2}[/\-\.]\d{1,2}([/\-\.]\d{2,4})?$|"
        r"^\d{1,2}[/\-]\d{2,4}$|"
        r"^[A-Za-z]{3,9}[/\-\s]\d{2,4}$",
        s.strip()
    ))


def _assign_bio_tags(tokens: list[str], fields: dict) -> list[str]:
    """Assign BIO tags to tokens based on resolved canonical fields.

    Uses a heuristic alignment strategy:
    - Product name tokens → B-product_name_raw / I-product_name_raw
    - Packing tokens → B-packing / I-packing
    - Numeric tokens at end → matched to quantity/price fields by position
    """
    n = len(tokens)
    tags = ["O"] * n

    if not fields or not tokens:
        return tags

    product_name = str(fields.get("product_name_raw", "") or "")
    packing = str(fields.get("packing", "") or "")

    # Phase 1: Tag product name by matching tokens from the start
    if product_name:
        prod_tokens = product_name.split()
        matched = 0
        for i, tok in enumerate(tokens):
            if matched < len(prod_tokens):
                if tok.lower() == prod_tokens[matched].lower():
                    tags[i] = f"B-product_name_raw" if matched == 0 else f"I-product_name_raw"
                    matched += 1
                elif matched == 0:
                    continue
                else:
                    break
            else:
                break

    # Phase 2: Tag packing tokens
    if packing:
        pack_tokens = packing.split()
        for i, tok in enumerate(tokens):
            if tags[i] != "O":
                continue
            for j, ptok in enumerate(pack_tokens):
                if tok.lower() == ptok.lower() or (re.match(r"\d+\*\d+", tok) and re.match(r"\d+\*\d+", ptok)):
                    tags[i] = f"B-packing" if j == 0 else f"I-packing"
                    break

    # Phase 3: Tag numeric tokens from the end based on field mapping
    # Identify which numeric fields have values
    numeric_fields = []
    for f in ["opening_qty", "receipt_qty", "total_qty", "issue_qty",
              "closing_qty", "price_paise", "near_expiry_qty"]:
        val = fields.get(f)
        if val is not None:
            numeric_fields.append(f)

    # Find numeric token positions (untagged)
    numeric_positions = []
    for i in range(n - 1, -1, -1):
        if tags[i] == "O" and (_is_numeric(tokens[i]) or tokens[i] == "-"):
            numeric_positions.insert(0, i)

    # Phase 4: Tag date/expiry tokens
    batch_no = str(fields.get("batch_no", "") or "")
    expiry = str(fields.get("expiry", "") or "")

    for i, tok in enumerate(tokens):
        if tags[i] != "O":
            continue
        if expiry and (_is_date_like(tok) or tok == expiry):
            tags[i] = "B-expiry"
        elif batch_no and tok == batch_no:
            tags[i] = "B-batch_no"

    # Phase 5: Map remaining numeric tokens to fields by position
    # Numeric fields are typically in a fixed order matching column layout
    untagged_numeric = [i for i in numeric_positions if tags[i] == "O"]

    if len(untagged_numeric) >= len(numeric_fields):
        # Align from the end (rightmost numeric = last field)
        offset = len(untagged_numeric) - len(numeric_fields)
        for j, f in enumerate(numeric_fields):
            idx = untagged_numeric[offset + j]
            tags[idx] = f"B-{f}"
    elif untagged_numeric and numeric_fields:
        # Fewer numeric tokens than fields — align from the end
        offset = len(numeric_fields) - len(untagged_numeric)
        for j, idx in enumerate(untagged_numeric):
            if offset + j < len(numeric_fields):
                tags[idx] = f"B-{numeric_fields[offset + j]}"

    return tags


def generate_training_data_from_pdfs(
    samples_dir: str,
    output_path: str,
    use_existing_parser: bool = True,
) -> dict:
    """Process all sample PDFs to generate BIO-tagged training data.

    Args:
        samples_dir: Directory containing sample PDF files.
        output_path: Path to write the training JSON file.
        use_existing_parser: Whether to use the rule-based parser for labels.

    Returns:
        Stats dict with counts.
    """
    from pharmgmt.parsing.table_parser import parse_tables

    samples_dir = Path(samples_dir)
    pdfs = sorted(samples_dir.glob("*.pdf")) + sorted(samples_dir.glob("*.PDF"))
    # Deduplicate (case-insensitive on Windows)
    seen = set()
    unique_pdfs = []
    for p in pdfs:
        key = str(p).lower()
        if key not in seen:
            seen.add(key)
            unique_pdfs.append(p)
    pdfs = unique_pdfs

    all_samples = []
    doc_samples = []  # For bill type classification
    stats = {"total_pdfs": len(pdfs), "successful": 0, "failed": 0,
             "total_rows": 0, "total_tokens": 0}

    for pdf_path in pdfs:
        logger.info("Processing: %s", pdf_path.name)
        try:
            pages = extract_pdf_text(str(pdf_path))
            if not pages:
                stats["failed"] += 1
                continue

            # Use existing parser for labels
            if use_existing_parser:
                parse_result = parse_tables(pages)
                bill_type = parse_result.get("meta", {}).get("bill_type", "unknown") or "unknown"
                rows = parse_result.get("rows", [])

                # Store document-level sample for bill type classifier
                full_text = "\n".join(p.get("text", "") for p in pages)
                doc_samples.append({
                    "file_name": pdf_path.name,
                    "text": full_text[:2000],  # First 2000 chars
                    "bill_type": bill_type,
                })

                # Convert parsed rows to BIO-tagged token sequences
                for row in rows:
                    raw_text = row.get("raw_text", "")
                    if not raw_text:
                        continue

                    tokens = _tokenize_line(raw_text)
                    if len(tokens) < 3:
                        continue

                    fields = row.get("fields", {})
                    bio_tags = _assign_bio_tags(tokens, fields)
                    confidence = row.get("confidence", 0.0)

                    all_samples.append({
                        "file": pdf_path.name,
                        "tokens": tokens,
                        "tags": bio_tags,
                        "confidence": confidence,
                        "bill_type": bill_type,
                    })
                    stats["total_rows"] += 1
                    stats["total_tokens"] += len(tokens)

            stats["successful"] += 1

        except Exception as e:
            logger.warning("Failed to process %s: %s", pdf_path.name, e)
            stats["failed"] += 1

    # Write output
    output = {
        "token_samples": all_samples,
        "doc_samples": doc_samples,
        "bio_tags": BIO_TAGS,
        "tag_to_idx": TAG_TO_IDX,
        "bill_types": BILL_TYPES,
        "bill_type_to_idx": BILL_TYPE_TO_IDX,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(
        "Generated training data: %d PDFs → %d token sequences, %d tokens",
        stats["successful"], stats["total_rows"], stats["total_tokens"],
    )
    return stats


def generate_token_features(tokens: list[str]) -> list[list[float]]:
    """Compute hand-crafted features for each token (used alongside embeddings).

    Features per token (11-dim):
        0: is_numeric (0/1)
        1: is_date_like (0/1)
        2: has_star (packing pattern like 1*10)
        3: token_length (normalized)
        4: relative_position (0-1)
        5: has_comma (common in Indian numbers)
        6: is_all_caps
        7: has_period
        8: starts_with_digit
        9: is_dash (-)
        10: num_digits / token_length

    Args:
        tokens: List of token strings.

    Returns:
        List of feature vectors (one per token).
    """
    n = len(tokens) if tokens else 1
    features = []
    for i, tok in enumerate(tokens):
        f = [
            1.0 if _is_numeric(tok) else 0.0,
            1.0 if _is_date_like(tok) else 0.0,
            1.0 if re.match(r"\d+\*\d+", tok) else 0.0,
            min(len(tok) / 20.0, 1.0),
            i / max(n - 1, 1),
            1.0 if "," in tok else 0.0,
            1.0 if tok.isupper() and tok.isalpha() else 0.0,
            1.0 if "." in tok else 0.0,
            1.0 if tok and tok[0].isdigit() else 0.0,
            1.0 if tok.strip() == "-" else 0.0,
            sum(c.isdigit() for c in tok) / max(len(tok), 1),
        ]
        features.append(f)
    return features


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    # Add src to path for imports
    src_dir = str(Path(__file__).parent.parent.parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    project_root = Path(__file__).parent.parent.parent.parent
    samples = project_root / "samples"
    output = project_root / "src" / "pharmgmt" / "ml" / "training_data.json"

    print(f"Samples dir: {samples}")
    print(f"Output: {output}")
    print(f"PDFs found: {len(list(samples.glob('*.pdf')) + list(samples.glob('*.PDF')))}")

    stats = generate_training_data_from_pdfs(str(samples), str(output))
    print(f"\nStats: {json.dumps(stats, indent=2)}")
