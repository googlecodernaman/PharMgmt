"""Confidence scoring for parsed rows and documents."""

import logging

logger = logging.getLogger("pharmgmt.parsing")

# Fields expected in a well-parsed row
EXPECTED_FIELDS = [
    "product_name_raw", "packing", "opening_qty", "receipt_qty",
    "total_qty", "issue_qty", "closing_qty", "price_paise",
    "batch_no", "expiry",
]

# Minimum fields that should be present for a reasonable row
CORE_FIELDS = ["product_name_raw"]


def score_row(row_fields: dict, expected: list[str] | None = None) -> float:
    """Compute confidence score for a single parsed row.

    Score = (non-null canonical fields) / (total expected fields)
    Bonus for product_name_raw presence.

    Args:
        row_fields: Dict of canonical field → value
        expected: List of expected field names (default: EXPECTED_FIELDS)

    Returns:
        Confidence score 0.0–1.0
    """
    if expected is None:
        # Use only the fields that are actually mapped in this row
        expected = [f for f in EXPECTED_FIELDS if f in row_fields]

    if not expected:
        return 0.0

    non_null = sum(
        1 for f in expected
        if row_fields.get(f) is not None
    )

    base_score = non_null / len(expected) if expected else 0.0

    # Bonus for having product name
    if row_fields.get("product_name_raw"):
        base_score = min(1.0, base_score + 0.1)

    return round(min(1.0, base_score), 3)


def score_document(rows: list[dict]) -> float:
    """Compute aggregate confidence for a document.

    Weighted average — rows with product_name get 2x weight.

    Args:
        rows: List of parse_result rows (each with 'confidence' and 'fields')

    Returns:
        Document-level confidence 0.0–1.0
    """
    if not rows:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for row in rows:
        confidence = row.get("confidence", 0.0)
        weight = 2.0 if row.get("fields", {}).get("product_name_raw") else 1.0
        weighted_sum += confidence * weight
        total_weight += weight

    return round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.0


def needs_review(avg_confidence: float, threshold: float = 0.75) -> bool:
    """Check if a document needs human review.

    Args:
        avg_confidence: Document-level average confidence
        threshold: Review threshold (default 0.75)

    Returns:
        True if document should be flagged for review
    """
    return avg_confidence < threshold
