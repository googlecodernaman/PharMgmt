"""Data normalization utilities for parsed bill data."""

import re
import unicodedata
from datetime import datetime


def normalize_date(raw: str) -> tuple[str | None, str]:
    """Normalize a date string to ISO YYYY-MM-DD format.

    Args:
        raw: Raw date string (e.g., "01/2025", "Jan 2025", "01-01-2025")

    Returns:
        Tuple of (iso_date or None, precision: 'day'|'month'|'year')
    """
    if not raw or not raw.strip():
        return None, "day"

    raw = raw.strip()

    # Try common date formats
    day_formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y",
        "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
        "%d.%m.%Y", "%d.%m.%y",
    ]
    for fmt in day_formats:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d"), "day"
        except ValueError:
            continue

    # Month formats (e.g., "01/2025", "Jan 2025", "01-2025")
    month_formats = [
        ("%m/%Y", "month"), ("%m-%Y", "month"), ("%b %Y", "month"),
        ("%B %Y", "month"), ("%m/%y", "month"), ("%m-%y", "month"),
        ("%b-%Y", "month"), ("%b-%y", "month"),
    ]
    for fmt, precision in month_formats:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-01"), precision
        except ValueError:
            continue

    # Year only
    if re.match(r"^\d{4}$", raw):
        return f"{raw}-01-01", "year"

    return None, "day"


def normalize_money(raw: str) -> int | None:
    """Convert a price string to integer paisa.

    Args:
        raw: Price string (e.g., "125.50", "₹1,250.00", "1250")

    Returns:
        Integer paisa (125.50 → 12550), or None if unparseable
    """
    if not raw or not raw.strip():
        return None

    # Remove currency symbols, commas, whitespace
    cleaned = re.sub(r"[₹$€,\s]", "", raw.strip())

    # Remove trailing text like "/-"
    cleaned = re.sub(r"/-$", "", cleaned)

    try:
        value = float(cleaned)
        return int(round(value * 100))
    except (ValueError, TypeError):
        return None


def normalize_text(raw: str) -> str:
    """Normalize text: lowercase, unicode-normalize, trim punctuation/whitespace.

    Args:
        raw: Raw text string

    Returns:
        Cleaned, normalized text
    """
    if not raw:
        return ""

    # Unicode normalize (NFC)
    text = unicodedata.normalize("NFC", raw)

    # Lowercase
    text = text.lower()

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def parse_quantity(raw: str) -> int | None:
    """Parse a quantity string to integer.

    Args:
        raw: Quantity string (e.g., "100", "1,000", "100.0")

    Returns:
        Integer quantity or None
    """
    if not raw or not raw.strip():
        return None

    cleaned = re.sub(r"[,\s]", "", raw.strip())

    try:
        value = float(cleaned)
        return int(value)
    except (ValueError, TypeError):
        return None
