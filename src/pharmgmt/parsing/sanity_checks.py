"""Sanity checks for parsed rows and documents."""

import logging

logger = logging.getLogger("pharmgmt.parsing")


def check_row(row_fields: dict) -> list[str]:
    """Run sanity checks on a single parsed row.

    Returns list of warning flags.

    Args:
        row_fields: Dict of canonical field → value

    Returns:
        List of warning strings
    """
    warnings = []

    # Check: missing product name
    if not row_fields.get("product_name_raw"):
        warnings.append("missing_product")

    # Check: negative quantities
    qty_fields = [
        "opening_qty", "receipt_qty", "total_qty",
        "issue_qty", "closing_qty", "breakage_qty",
        "reorder_qty", "near_expiry_qty",
    ]
    for field in qty_fields:
        val = row_fields.get(field)
        if val is not None and isinstance(val, (int, float)) and val < 0:
            warnings.append(f"negative_qty:{field}")
            break  # One flag is enough

    # Check: arithmetic — opening + receipt should equal total
    opening = row_fields.get("opening_qty")
    receipt = row_fields.get("receipt_qty")
    total = row_fields.get("total_qty")

    if all(v is not None for v in [opening, receipt, total]):
        if isinstance(opening, (int, float)) and isinstance(receipt, (int, float)) and isinstance(total, (int, float)):
            expected_total = opening + receipt
            if abs(expected_total - total) > 1:
                warnings.append("arithmetic_mismatch:opening+receipt!=total")

    # Check: closing — total - issue should equal closing
    issue = row_fields.get("issue_qty")
    closing = row_fields.get("closing_qty")

    if all(v is not None for v in [total, issue, closing]):
        if isinstance(total, (int, float)) and isinstance(issue, (int, float)) and isinstance(closing, (int, float)):
            expected_closing = total - issue
            if abs(expected_closing - closing) > 1:
                warnings.append("arithmetic_mismatch:total-issue!=closing")

    # Check: negative price
    price = row_fields.get("price_paise")
    if price is not None and isinstance(price, (int, float)) and price < 0:
        warnings.append("negative_price")

    return warnings


def check_document(rows: list[dict]) -> list[str]:
    """Run document-level sanity checks.

    Args:
        rows: List of parse_result rows

    Returns:
        List of document-level warning strings
    """
    warnings = []

    # No rows parsed
    if not rows:
        warnings.append("no_rows")
        return warnings

    # Low row count
    if len(rows) < 2:
        warnings.append("low_row_count")

    # High flag rate
    flagged_rows = sum(
        1 for r in rows if r.get("warnings") and len(r["warnings"]) > 0
    )
    if len(rows) > 0 and (flagged_rows / len(rows)) > 0.5:
        warnings.append("high_flag_rate")

    return warnings
