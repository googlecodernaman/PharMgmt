"""Core table parser — extract, map, and score canonical rows from PDF pages.

Hybrid approach: uses ML models when available for bill-type classification,
token-level field extraction, and low-confidence row re-extraction.
Falls back to rule-based parsing when models are not present.
"""

import logging
import re
import time

from pharmgmt.parsing.column_resolver import match_headers, resolve_row
from pharmgmt.parsing.confidence import score_row, score_document, needs_review
from pharmgmt.parsing.mapping_config import MappingConfig, detect_bill_type, load_all_mappings
from pharmgmt.parsing.sanity_checks import check_row, check_document

logger = logging.getLogger("pharmgmt.parsing")

# ML predictor (lazy-loaded, graceful fallback)
_ml_predictor = None


def _get_ml_predictor():
    """Get ML predictor singleton, or None if unavailable."""
    global _ml_predictor
    if _ml_predictor is not None:
        return _ml_predictor if _ml_predictor.available else None
    try:
        from pharmgmt.ml.predict import get_predictor
        _ml_predictor = get_predictor()
        if _ml_predictor.available:
            _ml_predictor.load()
            logger.info("ML predictor loaded for hybrid parsing")
            return _ml_predictor
        else:
            logger.info("ML models not found — using rule-based parsing only")
            return None
    except Exception as e:
        logger.debug("ML predictor unavailable: %s", e)
        return None


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

        # ML-assisted bill type detection when keyword matching fails or is uncertain
        if mapping is None:
            mapping = _ml_detect_bill_type(full_text)

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

    # ─── Fallback: text-line parser when no tables found ───
    if row_index_global == 0:
        logger.info("No tables found — falling back to text-line parser")
        # Try ML extraction first, then fall back to rule-based
        predictor = _get_ml_predictor()
        if predictor is not None:
            all_rows, row_index_global = _parse_text_lines_ml(pages, predictor)
        if row_index_global == 0:
            all_rows, row_index_global = _parse_text_lines(pages, mapping)

    # ─── ML re-extraction for low-confidence rows ───
    all_rows = _ml_reextract_low_confidence(all_rows)

    duration_ms = int((time.time() - start_time) * 1000)

    # Compute aggregate metrics
    rows_parsed = len(all_rows)
    avg_conf = score_document(all_rows)
    rows_flagged = sum(1 for r in all_rows if r["confidence"] < 0.5)
    doc_warnings = check_document(all_rows)
    review_needed = needs_review(avg_conf)

    # Count ML-parsed and re-extracted rows
    ml_parsed = sum(1 for r in all_rows if r.get("parse_method") == "ml")
    ml_reextracted = sum(1 for r in all_rows if r.get("parse_method") == "ml_reextract")

    return {
        "document": doc_metadata,
        "rows": all_rows,
        "meta": {
            "parser_version": "0.3.0",
            "duration_ms": duration_ms,
            "rows_parsed": rows_parsed,
            "rows_flagged": rows_flagged,
            "avg_confidence": round(avg_conf, 3),
            "error_flags": doc_warnings,
            "needs_review": review_needed,
            "bill_type": mapping.bill_type if mapping else None,
            "ml_assisted": ml_parsed + ml_reextracted > 0,
            "ml_parsed_rows": ml_parsed,
            "ml_reextracted_rows": ml_reextracted,
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
            "parser_version": "0.3.0",
            "duration_ms": duration_ms,
            "rows_parsed": 0,
            "rows_flagged": 0,
            "avg_confidence": 0.0,
            "error_flags": error_flags,
            "needs_review": True,
            "bill_type": None,
        },
    }


def _parse_text_lines(pages: list[dict], mapping) -> tuple[list[dict], int]:
    """Parse product data from plaintext lines when no tables are found.

    Handles the common Stock & Sales format:
      PRODUCT_NAME PACKING QTY VALUE  QTY VALUE  QTY VALUE  QTY VALUE  ...

    Args:
        pages: List of page dicts with 'text' key
        mapping: MappingConfig (for bill_type context)

    Returns:
        Tuple of (rows list, row count)
    """
    all_rows = []
    row_idx = 0

    # Regex: a line that contains a product name followed by numeric values
    # Pattern: text prefix, then groups of (qty value) or (- 0.00)
    # A data line starts with text and then has at least 4 numeric-like tokens
    num_token = re.compile(r'^[\d,]+\.?\d*$|^-$')

    for page_data in pages:
        text = page_data.get("text", "") or ""
        page_num = page_data.get("page", 0)

        for line in text.split("\n"):
            line = line.strip()
            if not line or len(line) < 10:
                continue

            # Skip separator lines (all dashes)
            if re.match(r'^[\-=]+$', line):
                continue

            # Skip known header/footer patterns
            lower = line.lower()
            if any(kw in lower for kw in ['total', 'item description', 'opening', 'receipt', 'issue',
                                           'closing', 'dump', 'phone', 'gstin', 'gst', 'tin :',
                                           'cst no', 'e-mail', 'stock & sales', 'page ', 'printed']):
                continue

            # Split into tokens
            tokens = line.split()
            if len(tokens) < 5:
                continue

            # Find where numeric data starts by scanning from the end
            # Data lines have numeric/dash tokens at the end
            numeric_end = []
            for t in reversed(tokens):
                if num_token.match(t.replace(',', '')):
                    numeric_end.insert(0, t)
                else:
                    break

            if len(numeric_end) < 4:
                continue  # Not enough numeric columns

            # Everything before the numeric tokens is the product description
            text_part_count = len(tokens) - len(numeric_end)
            text_tokens = tokens[:text_part_count]

            if not text_tokens:
                continue

            # Try to split text into product name and packing
            # Packing patterns: 1*14, 1*30, 1*10, etc.
            product_name = ""
            packing = ""
            packing_unit = ""

            for i, t in enumerate(text_tokens):
                if re.match(r'^\d+\*\d+', t):
                    product_name = " ".join(text_tokens[:i]).strip()
                    packing = t
                    # Unit might follow (PCS, Pcs, TAB, etc.)
                    if i + 1 < len(text_tokens):
                        packing_unit = " ".join(text_tokens[i+1:])
                    break
            else:
                # No packing pattern found — entire text is product name
                product_name = " ".join(text_tokens).strip()

            if not product_name:
                continue

            pack_str = f"{packing} {packing_unit}".strip() if packing else ""

            # Map numeric values based on count
            # Stock & Sales format: OPEN_QTY OPEN_VAL RECV_QTY RECV_VAL ISSUE_QTY ISSUE_VAL CLOSE_QTY CLOSE_VAL [DUMP_QTY MAY N_EXP]
            vals = []
            for v in numeric_end:
                v_clean = v.replace(',', '')
                if v_clean == '-':
                    vals.append(0)
                else:
                    try:
                        vals.append(float(v_clean))
                    except ValueError:
                        vals.append(0)

            canonical = {
                "product_name_raw": product_name,
                "packing": pack_str,
            }

            if len(vals) >= 8:
                canonical["opening_qty"] = int(vals[0]) if vals[0] == int(vals[0]) else vals[0]
                canonical["opening_value"] = vals[1]
                canonical["receipt_qty"] = int(vals[2]) if vals[2] == int(vals[2]) else vals[2]
                canonical["receipt_value"] = vals[3]
                canonical["issue_qty"] = int(vals[4]) if vals[4] == int(vals[4]) else vals[4]
                canonical["issue_value"] = vals[5]
                canonical["closing_qty"] = int(vals[6]) if vals[6] == int(vals[6]) else vals[6]
                canonical["closing_value"] = vals[7]
                # Derive price from closing: value / qty
                if canonical["closing_qty"] and canonical["closing_qty"] > 0:
                    canonical["price_paise"] = int(canonical["closing_value"] / canonical["closing_qty"] * 100)
            elif len(vals) >= 4:
                canonical["opening_qty"] = int(vals[0]) if vals[0] == int(vals[0]) else vals[0]
                canonical["closing_qty"] = int(vals[1]) if vals[1] == int(vals[1]) else vals[1]
                canonical["price_paise"] = int(vals[2] * 100) if vals[2] else None

            # Apply confidence and sanity checks
            row_confidence = score_row(canonical)
            row_warnings = check_row(canonical)

            all_rows.append({
                "page": page_num,
                "row_index": row_idx,
                "raw_text": line,
                "fields": canonical,
                "confidence": round(row_confidence, 3),
                "warnings": row_warnings,
            })
            row_idx += 1

    logger.info("Text-line parser extracted %d rows", row_idx)
    return all_rows, row_idx


# ─── ML-assisted helpers ───────────────────────────────────────────────


def _ml_detect_bill_type(full_text: str) -> MappingConfig | None:
    """Use ML classifier to detect bill type, then return matching MappingConfig."""
    predictor = _get_ml_predictor()
    if predictor is None:
        return None

    bill_type, confidence = predictor.classify_bill_type(full_text[:2000])
    if confidence < 0.5 or bill_type == "unknown":
        logger.debug("ML bill-type confidence too low (%.2f) — skipping", confidence)
        return None

    # Find the MappingConfig that matches the ML-detected bill type
    all_mappings = load_all_mappings()
    for m in all_mappings:
        if m.bill_type == bill_type:
            logger.info(
                "ML detected bill type: %s (confidence: %.2f)", bill_type, confidence
            )
            return m

    logger.debug("ML detected bill type '%s' has no mapping config", bill_type)
    return None


def _parse_text_lines_ml(pages: list[dict], predictor) -> tuple[list[dict], int]:
    """Parse text lines using ML field extraction instead of regex heuristics.

    Each non-empty line is run through the BiLSTM-CRF field extractor which
    assigns BIO tags to every token, then groups them into canonical fields.

    Args:
        pages: List of page dicts with 'text' key
        predictor: Loaded MLPredictor instance

    Returns:
        Tuple of (rows list, row count)
    """
    all_rows = []
    row_idx = 0

    for page_data in pages:
        text = page_data.get("text", "") or ""
        page_num = page_data.get("page", 0)

        for line in text.split("\n"):
            line = line.strip()
            if not line or len(line) < 10:
                continue

            # Skip separator and header/footer lines
            if re.match(r'^[\-=]+$', line):
                continue
            lower = line.lower()
            if any(kw in lower for kw in [
                'total', 'item description', 'page ', 'printed',
                'phone', 'gstin', 'e-mail', 'stock & sales',
            ]):
                continue

            tokens = line.split()
            if len(tokens) < 3:
                continue

            result = predictor.extract_fields(line)
            fields = result.get("fields", {})
            ml_confidence = result.get("confidence", 0.0)

            # Must have product_name_raw AND at least one numeric field to be a data row
            # (filters out header/metadata lines that only match product_name)
            if not fields.get("product_name_raw"):
                continue
            numeric_fields = [
                "opening_qty", "receipt_qty", "total_qty", "issue_qty",
                "closing_qty", "price_paise", "near_expiry_qty",
            ]
            has_numeric = any(fields.get(f) is not None for f in numeric_fields)
            if not has_numeric:
                continue

            # Apply sanity checks and row scoring
            row_confidence = max(score_row(fields), ml_confidence)
            row_warnings = check_row(fields)

            all_rows.append({
                "page": page_num,
                "row_index": row_idx,
                "raw_text": line,
                "fields": fields,
                "confidence": round(row_confidence, 3),
                "warnings": row_warnings,
                "parse_method": "ml",
            })
            row_idx += 1

    logger.info("ML text-line parser extracted %d rows", row_idx)
    return all_rows, row_idx


def _ml_reextract_low_confidence(rows: list[dict]) -> list[dict]:
    """Re-extract fields for low-confidence rows using ML model.

    Rows with confidence < 0.5 get a second pass through the ML extractor.
    The ML result replaces the original only if it produces higher confidence.

    Args:
        rows: List of parsed row dicts

    Returns:
        Updated rows list (modified in-place for efficiency)
    """
    predictor = _get_ml_predictor()
    if predictor is None:
        return rows

    reextracted = 0
    for row in rows:
        if row.get("confidence", 1.0) >= 0.5:
            continue
        if row.get("parse_method") == "ml":
            continue  # Already ML-parsed, don't re-run

        raw_text = row.get("raw_text", "")
        if not raw_text or len(raw_text) < 10:
            continue

        ml_result = predictor.extract_fields(raw_text)
        ml_fields = ml_result.get("fields", {})
        ml_confidence = ml_result.get("confidence", 0.0)

        if not ml_fields.get("product_name_raw"):
            continue

        # Merge: prefer ML value when original is missing or ML confidence is better
        original_fields = row.get("fields", {})
        merged = dict(original_fields)
        for key, val in ml_fields.items():
            if val is not None and (merged.get(key) is None or row["confidence"] < 0.3):
                merged[key] = val

        new_confidence = max(score_row(merged), ml_confidence)
        if new_confidence > row["confidence"]:
            row["fields"] = merged
            row["confidence"] = round(new_confidence, 3)
            row["warnings"] = check_row(merged)
            row["parse_method"] = "ml_reextract"
            reextracted += 1

    if reextracted:
        logger.info("ML re-extracted %d low-confidence rows", reextracted)
    return rows

