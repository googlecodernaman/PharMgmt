---
phase: 2
plan: 3
wave: 2
---

# Plan 2.3: Confidence Scoring & Sanity Checks

## Objective
Add parsing confidence aggregation, automatic sanity checks (arithmetic consistency, negative quantities), and human review flagging for low-confidence documents.

## Context
- c:\PharMgmt\src\pharmgmt\parsing\table_parser.py — Core parser (from Plan 2.2)
- c:\PharMgmt\src\pharmgmt\models\parsing_run.py — ParsingRun model
- .gsd/SPEC.md — Confidence threshold 0.75

## Tasks

<task type="auto">
  <name>Implement confidence scoring and sanity checker</name>
  <files>
    c:\PharMgmt\src\pharmgmt\parsing\confidence.py
    c:\PharMgmt\src\pharmgmt\parsing\sanity_checks.py
  </files>
  <action>
    Create `confidence.py`:
    - `score_row(row_dict: dict, expected_fields: list[str]) -> float`:
      Row confidence = (non-null canonical fields) / (total expected fields).
      Bonus: +0.1 if product_name_raw is present, +0.05 if quantities are parseable.
      Cap at 1.0.
    - `score_document(rows: list[dict]) -> float`:
      Weighted average of row confidences. Rows with product_name get higher weight.
    - `needs_review(avg_confidence: float, threshold: float = 0.75) -> bool`:
      Returns True if avg_confidence < threshold.

    Create `sanity_checks.py`:
    - `check_row(row_dict: dict) -> list[str]`:
      Returns list of warning flags for a single row:
      - "negative_qty": any quantity field < 0
      - "missing_product": product_name_raw is None
      - "arithmetic_mismatch": opening + receipt != total (if all 3 present, allow ±1 tolerance)
      - "closing_mismatch": total - issue != closing (if all present, allow ±1)
    - `check_document(rows: list[dict]) -> list[str]`:
      Aggregate document-level warnings:
      - "no_rows": zero rows parsed
      - "low_row_count": fewer than 2 rows
      - "high_flag_rate": >50% of rows have warnings
    - Both functions return error_flags lists that go into ParsingRun.error_flags
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.parsing.confidence import score_row, score_document, needs_review; from pharmgmt.parsing.sanity_checks import check_row, check_document; print('All imports OK')"
  </verify>
  <done>Confidence scoring and sanity checks produce correct flags and scores</done>
</task>

<task type="auto">
  <name>Integrate confidence and sanity into table parser</name>
  <files>
    c:\PharMgmt\src\pharmgmt\parsing\table_parser.py
  </files>
  <action>
    Update `parse_tables()` to:
    1. After resolving each row, call `score_row()` and `check_row()`
    2. Attach `confidence` and `warnings` to each row in the result
    3. After all rows, call `score_document()` for avg_confidence
    4. Call `check_document()` for document-level error_flags
    5. Set `needs_review` flag based on threshold
    6. Include all metrics in the meta section of parse_result

    The parse_result should now have fully populated meta:
    {parser_version, duration_ms, rows_parsed, rows_flagged, avg_confidence, error_flags, needs_review}
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.parsing.table_parser import parse_tables; print('Parser with confidence OK')"
  </verify>
  <done>parse_result includes per-row confidence/warnings and document-level metrics</done>
</task>

## Success Criteria
- [ ] Per-row confidence scores between 0.0–1.0
- [ ] Sanity checks catch negative qty, arithmetic mismatches
- [ ] Documents with avg_confidence < 0.75 flagged for review
- [ ] error_flags populated in parse_result meta
