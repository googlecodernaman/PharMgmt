"""Column resolver — map raw PDF table headers to canonical fields."""

import logging
import re

from pharmgmt.parsing.mapping_config import MappingConfig
from pharmgmt.parsing.normalizers import (
    normalize_date,
    normalize_money,
    normalize_text,
    parse_quantity,
)

logger = logging.getLogger("pharmgmt.parsing")


def normalize_header(raw: str) -> str:
    """Normalize a column header for matching.

    Args:
        raw: Raw header string from PDF table

    Returns:
        Lowercase, stripped, space-collapsed header
    """
    if not raw:
        return ""
    return re.sub(r"\s+", " ", raw.strip().lower())


def match_headers(
    table_headers: list[str | None], mapping: MappingConfig
) -> tuple[dict[int, str], float]:
    """Match raw table column headers to canonical field names.

    Uses a two-pass strategy:
    1. Exact match (normalized header == alias)
    2. Substring containment (alias in normalized header or vice versa)

    Args:
        table_headers: List of raw header strings from a PDF table row
        mapping: MappingConfig with header_aliases

    Returns:
        Tuple of (column_map: {col_index: canonical_field}, confidence: 0-1)
    """
    column_map = {}
    matched_fields = set()

    normalized = [normalize_header(h or "") for h in table_headers]

    # Pass 1: Exact matches
    for idx, header in enumerate(normalized):
        if not header:
            continue
        for field_name, aliases in mapping.header_aliases.items():
            if field_name in matched_fields:
                continue
            for alias in aliases:
                if header == alias.lower():
                    column_map[idx] = field_name
                    matched_fields.add(field_name)
                    break
            if idx in column_map:
                break

    # Pass 2: Substring matches for unmatched columns
    for idx, header in enumerate(normalized):
        if idx in column_map or not header:
            continue
        for field_name, aliases in mapping.header_aliases.items():
            if field_name in matched_fields:
                continue
            for alias in aliases:
                alias_lower = alias.lower()
                if alias_lower in header or header in alias_lower:
                    column_map[idx] = field_name
                    matched_fields.add(field_name)
                    break
            if idx in column_map:
                break

    # Confidence: matched fields / total available aliases
    total_possible = len(mapping.header_aliases)
    confidence = len(matched_fields) / total_possible if total_possible > 0 else 0.0

    logger.debug(
        "Header match: %d/%d fields matched (confidence: %.2f)",
        len(matched_fields), total_possible, confidence,
    )

    return column_map, confidence


def resolve_row(
    row: list[str | None],
    column_map: dict[int, str],
    mapping: MappingConfig,
) -> tuple[dict, float]:
    """Map a raw table row to canonical field values using normalizers.

    Args:
        row: List of cell values from a table row
        column_map: Mapping of column index → canonical field name
        mapping: MappingConfig for normalization rules

    Returns:
        Tuple of (canonical_dict, row_confidence)
    """
    canonical = {}
    non_null_count = 0
    total_mapped = len(column_map)

    # Store raw row text
    raw_parts = [str(cell) if cell else "" for cell in row]
    canonical["raw_row_text"] = " | ".join(raw_parts)

    for col_idx, field_name in column_map.items():
        if col_idx >= len(row):
            canonical[field_name] = None
            continue

        raw_value = row[col_idx]
        if raw_value is None or str(raw_value).strip() == "":
            canonical[field_name] = None
            continue

        raw_str = str(raw_value).strip()

        # Apply appropriate normalizer based on column type
        if field_name in mapping.date_columns:
            date_val, precision = normalize_date(raw_str)
            canonical[field_name] = raw_str  # Keep original for display
            canonical[f"{field_name}_normalized"] = date_val
            canonical[f"{field_name}_precision"] = precision
            if date_val:
                non_null_count += 1
        elif field_name in mapping.money_columns:
            paise = normalize_money(raw_str)
            canonical[field_name] = paise
            if paise is not None:
                non_null_count += 1
        elif field_name in mapping.qty_columns:
            qty = parse_quantity(raw_str)
            canonical[field_name] = qty
            if qty is not None:
                non_null_count += 1
        else:
            canonical[field_name] = raw_str
            non_null_count += 1

    # Row confidence: non-null mapped fields / total mapped fields
    row_confidence = non_null_count / total_mapped if total_mapped > 0 else 0.0

    # Boost if product_name_raw is present
    if canonical.get("product_name_raw"):
        row_confidence = min(1.0, row_confidence + 0.1)

    return canonical, row_confidence
