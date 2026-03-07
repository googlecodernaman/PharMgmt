"""Expiry alert system — monitors product expiry dates."""

import logging
import re
from datetime import datetime, date

logger = logging.getLogger("pharmgmt.alerts")

# Expiry date parsing patterns
EXPIRY_PATTERNS = [
    (r"^(\d{1,2})[/\-](\d{4})$", "MY"),           # MM/YYYY or MM-YYYY
    (r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", "DMY"),  # DD/MM/YYYY
    (r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$", "YMD"),  # YYYY-MM-DD
    (r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{2})$", "DMY2"),  # DD/MM/YY
    (r"^(\d{1,2})[/\-](\d{2})$", "MY2"),           # MM/YY
]


def parse_expiry_date(expiry_str: str) -> date | None:
    """Parse an expiry string into a date.

    Supports: MM/YYYY, DD/MM/YYYY, YYYY-MM-DD, DD/MM/YY, MM/YY

    Args:
        expiry_str: Raw expiry string

    Returns:
        date object or None if unparseable
    """
    if not expiry_str or not isinstance(expiry_str, str):
        return None

    s = expiry_str.strip()
    for pattern, fmt in EXPIRY_PATTERNS:
        m = re.match(pattern, s)
        if not m:
            continue
        try:
            if fmt == "MY":
                return date(int(m.group(2)), int(m.group(1)), 28)
            elif fmt == "DMY":
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            elif fmt == "YMD":
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            elif fmt == "DMY2":
                yr = int(m.group(3))
                yr = yr + 2000 if yr < 100 else yr
                return date(yr, int(m.group(2)), int(m.group(1)))
            elif fmt == "MY2":
                yr = int(m.group(2))
                yr = yr + 2000 if yr < 100 else yr
                return date(yr, int(m.group(1)), 28)
        except (ValueError, OverflowError):
            continue
    return None


def get_expiry_alerts(session, days_ahead: int = 90) -> dict:
    """Scan all line items for expiry alerts.

    Args:
        session: SQLAlchemy session
        days_ahead: How many days ahead to look

    Returns:
        Dict with expired, warning_30d, warning_60d, warning_90d lists
    """
    from pharmgmt.models import LineItem, Document

    items = session.query(LineItem).filter(LineItem.expiry.isnot(None)).all()
    today = date.today()

    result = {"expired": [], "warning_30d": [], "warning_60d": [], "warning_90d": [], "total_alerts": 0}

    for li in items:
        exp_date = parse_expiry_date(li.expiry)
        if exp_date is None:
            continue

        days_remaining = (exp_date - today).days

        if days_remaining > days_ahead:
            continue

        doc = session.query(Document).filter_by(id=li.document_id).first()

        alert = {
            "product_name": li.product_name_raw,
            "batch_no": li.batch_no,
            "expiry_date": li.expiry,
            "expiry_parsed": exp_date.isoformat(),
            "days_remaining": days_remaining,
            "document_id": li.document_id,
            "file_name": doc.file_name if doc else None,
        }

        if days_remaining < 0:
            alert["severity"] = "expired"
            result["expired"].append(alert)
        elif days_remaining <= 30:
            alert["severity"] = "critical"
            result["warning_30d"].append(alert)
        elif days_remaining <= 60:
            alert["severity"] = "warning"
            result["warning_60d"].append(alert)
        else:
            alert["severity"] = "info"
            result["warning_90d"].append(alert)

    # Sort each bucket by days_remaining
    for key in ["expired", "warning_30d", "warning_60d", "warning_90d"]:
        result[key].sort(key=lambda x: x["days_remaining"])

    result["total_alerts"] = sum(len(result[k]) for k in ["expired", "warning_30d", "warning_60d", "warning_90d"])
    return result
