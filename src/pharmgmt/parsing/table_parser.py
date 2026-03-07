"""Core table parser — extract, map, and score canonical rows from PDF pages."""

import logging
import re
import time

from pharmgmt.parsing.column_resolver import match_headers, resolve_row
from pharmgmt.parsing.confidence import score_row, score_document, needs_review
from pharmgmt.parsing.mapping_config import MappingConfig, detect_bill_type, load_all_mappings
from pharmgmt.parsing.sanity_checks import check_row, check_document

logger = logging.getLogger("pharmgmt.parsing")


def parse_tables(
    pages: list[dict],
    mapping: MappingConfig | None = None,
) -> dict:
    """Parse extracted PDF pages into canonical rows.

    Takes the output of extract_text_from_pdf() and produces a parse_result
    matching the SPEC contract.

    Args:
        pages: List of {page: int, text: str, tables: list[list[list[str]]]}
        mapping: Optional mapping config (auto-detected if None)

    Returns:
        parse_result dict: {document: {...}, rows: [...], meta: {...}}
    """
    start_time = time.time()

    # Concatenate all page text for detection and metadata
    full_text = "\n".join(p.get("text", "") or "" for p in pages)

    # Auto-detect bill type if not provided
    if mapping is None:
        # Try using first table headers for better detection
        first_headers = None
        for page in pages:
            for table in (page.get("tables") or []):
                if table and len(table) > 0 and table[0]:
                    first_headers = [str(h) if h else "" for h in table[0]]
                    break
            if first_headers:
                break

        mapping = detect_bill_type(full_text, first_headers)

    if mapping is None:
        logger.warning("No bill type detected — using first available mapping as fallback")
        all_mappings = load_all_mappings()
        mapping = all_mappings[0] if all_mappings else None

    if mapping is None:
        duration_ms = int((time.time() - start_time) * 1000)
        return _empty_result(duration_ms, ["no_mapping_available"])

    # Extract document metadata from header text
    doc_metadata = _extract_document_metadata(full_text)
    doc_metadata["bill_type"] = mapping.bill_type

    # Parse all tables across all pages
    all_rows = []
    row_index_global = 0

    for page_data in pages:
        page_num = page_data.get("page", 0)
        tables = page_data.get("tables") or []

        for table in tables:
            if not table or len(table) < 2:
                continue  # Need at least header + 1 data row

            # Find the header row
            header_row_idx = _find_header_row(table, mapping)
            if header_row_idx is None:
                continue

            headers = [str(h) if h else "" for h in table[header_row_idx]]
            column_map, header_confidence = match_headers(headers, mapping)

            if not column_map:
                logger.debug("No columns matched for table on page %d", page_num)
                continue

            # Parse data rows (after header)
            for data_row_idx in range(header_row_idx + 1, len(table)):
                raw_row = table[data_row_idx]
                if not raw_row:
                    continue

                # Convert all cells to strings
                str_row = [str(cell) if cell else "" for cell in raw_row]

                # Check skip patterns
                if _is_skip_row(str_row, mapping.skip_patterns):
                    continue

                # Check if this is another header row (repeated headers)
                if _looks_like_header(str_row, headers):
                    continue

                # Resolve to canonical
                canonical, row_confidence = resolve_row(str_row, column_map, mapping)
                canonical["page"] = page_num
                canonical["row_index"] = row_index_global

                # Apply sanity checks
                row_warnings = check_row(canonical)

                # Compute confidence using scorer
                final_confidence = score_row(canonical)

                all_rows.append({
                    "page": page_num,
                    "row_index": row_index_global,
                    "raw_text": canonical.pop("raw_row_text", ""),
                    "fields": canonical,
                    "confidence": round(final_confidence, 3),
                    "warnings": row_warnings,
                })

                row_index_global += 1

    duration_ms = int((time.time() - start_time) * 1000)

    # Compute aggregate metrics
    rows_parsed = len(all_rows)
    avg_conf = score_document(all_rows)
    rows_flagged = sum(1 for r in all_rows if r["confidence"] < 0.5)
    doc_warnings = check_document(all_rows)
    review_needed = needs_review(avg_conf)

    return {
        "document": doc_metadata,
        "rows": all_rows,
        "meta": {
            "parser_version": "0.2.0",
            "duration_ms": duration_ms,
            "rows_parsed": rows_parsed,
            "rows_flagged": rows_flagged,
            "avg_confidence": round(avg_conf, 3),
            "error_flags": doc_warnings,
            "needs_review": review_needed,
            "bill_type": mapping.bill_type if mapping else None,
        },
    }


def _find_header_row(table: list[list], mapping: MappingConfig) -> int | None:
    """Find the row index that contains table headers.

    Tries each row as a potential header and picks the one with the best match.

    Args:
        table: List of rows (each row is a list of cell values)
        mapping: MappingConfig with header_aliases

    Returns:
        Row index of the best header match, or None
    """
    best_idx = None
    best_score = 0

    # Only check first 5 rows as potential headers
    for idx in range(min(5, len(table))):
        row = table[idx]
        if not row:
            continue
        headers = [str(h) if h else "" for h in row]
        _, confidence = match_headers(headers, mapping)
        if confidence > best_score:
            best_score = confidence
            best_idx = idx

    # Require at least 20% of fields matched to count as a header
    if best_score >= 0.2:
        return best_idx
    return None


def _is_skip_row(row: list[str], patterns: list[str]) -> bool:
    """Check if a row should be skipped based on skip patterns.

    Args:
        row: List of cell strings
        patterns: Regex patterns — if first non-empty cell matches, skip

    Returns:
        True if row should be skipped
    """
    # Check if row is entirely empty
    if all(not cell.strip() for cell in row):
        return True

    # Check first non-empty cell against patterns
    first_cell = ""
    for cell in row:
        if cell.strip():
            first_cell = cell.strip()
            break

    if not first_cell:
        return True

    for pattern in patterns:
        try:
            if re.match(pattern, first_cell, re.IGNORECASE):
                return True
        except re.error:
            continue

    return False


def _looks_like_header(row: list[str], original_headers: list[str]) -> bool:
    """Check if a row looks like a repeated header row.

    Args:
        row: Current row cells
        original_headers: The original header row cells

    Returns:
        True if this looks like a duplicate header
    """
    if len(row) != len(original_headers):
        return False

    # If >60% of non-empty cells match the original headers exactly, it's a repeated header
    matches = 0
    total = 0
    for cell, header in zip(row, original_headers):
        if cell.strip() and header.strip():
            total += 1
            if cell.strip().lower() == header.strip().lower():
                matches += 1

    return total > 0 and (matches / total) > 0.6


def _extract_document_metadata(full_text: str) -> dict:
    """Extract supplier name, GSTIN, and report dates from PDF header text.

    Args:
        full_text: Concatenated text from all pages

    Returns:
        Dict with extracted metadata fields
    """
    metadata = {
        "supplier_name": None,
        "supplier_gstin": None,
        "report_date_from": None,
        "report_date_to": None,
        "report_title": None,
    }

    if not full_text:
        return metadata

    lines = full_text.split("\n")

    # Try to extract supplier/title from first few non-empty lines
    non_empty_lines = [l.strip() for l in lines[:10] if l.strip()]
    if non_empty_lines:
        metadata["report_title"] = non_empty_lines[0]
        # If first line has a dash, split into supplier and title
        if " - " in non_empty_lines[0]:
            parts = non_empty_lines[0].split(" - ", 1)
            metadata["supplier_name"] = parts[0].strip()
            metadata["report_title"] = parts[1].strip()

    # GSTIN pattern: 2 digits + 5 chars + 4 digits + 1 char + 1 digit + 1 char + 1 alphanum
    gstin_match = re.search(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z][A-Z\d])\b", full_text)
    if gstin_match:
        metadata["supplier_gstin"] = gstin_match.group(1)

    # Date range patterns
    period_match = re.search(
        r"(?:period|from|date)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s*(?:to|-)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        full_text,
        re.IGNORECASE,
    )
    if period_match:
        metadata["report_date_from"] = period_match.group(1)
        metadata["report_date_to"] = period_match.group(2)

    return metadata


def _empty_result(duration_ms: int, error_flags: list[str]) -> dict:
    """Return an empty parse result with error flags."""
    return {
        "document": {},
        "rows": [],
        "meta": {
            "parser_version": "0.2.0",
            "duration_ms": duration_ms,
            "rows_parsed": 0,
            "rows_flagged": 0,
            "avg_confidence": 0.0,
            "error_flags": error_flags,
            "needs_review": True,
            "bill_type": None,
        },
    }
