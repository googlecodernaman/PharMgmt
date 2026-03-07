---
phase: 2
plan: 5
wave: 3
---

# Plan 2.5: Parser Tests & Accuracy Validation

## Objective
Write comprehensive tests for the parsing engine. Validate against 3 sample PDFs with gold data. This is the Phase 2 acceptance gate — target ≥90% field-level accuracy.

## Context
- c:\PharMgmt\tests\conftest.py — Existing fixtures
- c:\PharMgmt\tests\fixtures\generate_samples.py — Sample PDF generators (from Plan 2.2)
- c:\PharMgmt\src\pharmgmt\parsing\ — All parsing modules

## Tasks

<task type="auto">
  <name>Create parser unit tests</name>
  <files>
    c:\PharMgmt\tests\test_parser.py
    c:\PharMgmt\tests\test_column_resolver.py
    c:\PharMgmt\tests\test_confidence.py
  </files>
  <action>
    Create `test_column_resolver.py`:
    - Test normalize_header with various whitespace/case
    - Test match_headers with exact matches
    - Test match_headers with partial/substring matches
    - Test match_headers returns correct confidence
    - Test resolve_row applies normalizers correctly (dates→ISO, money→paisa, qty→int)
    - Test resolve_row handles None/empty cells

    Create `test_confidence.py`:
    - Test score_row returns 0-1 range
    - Test score_row with all fields → high confidence
    - Test score_row with missing fields → lower confidence
    - Test score_document averages correctly
    - Test needs_review threshold
    - Test check_row catches negative qty
    - Test check_row catches arithmetic mismatch
    - Test check_document flags high_flag_rate

    Create `test_parser.py`:
    - Test parse_tables with sample_sales_stock.pdf → correct bill type detection
    - Test parse_tables with sample_batch_stock.pdf → correct column mapping
    - Test parse_tables with sample_short_sales.pdf → correct row count
    - Test parse_tables returns valid parse_result contract
    - Test metadata extraction (supplier name, GSTIN, dates)
    - Test skip rows (subtotals) are excluded
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -m pytest tests/test_parser.py tests/test_column_resolver.py tests/test_confidence.py -v --tb=short
  </verify>
  <done>All parser unit tests pass</done>
</task>

<task type="auto">
  <name>Create accuracy validation tests</name>
  <files>
    c:\PharMgmt\tests\test_accuracy.py
  </files>
  <action>
    Create `test_accuracy.py`:
    - For each of the 3 sample PDFs:
      1. Generate the PDF using generate_samples.py
      2. Run full ingestion pipeline
      3. Compare parsed canonical output with gold JSON
      4. Calculate field-level accuracy: matched_fields / total_fields
      5. Assert accuracy >= 0.90 (90%)
    
    - Test end-to-end upload flow:
      1. Upload sample PDF via API
      2. Verify parse_result response has rows
      3. Verify ParsingRun record created in DB
      4. Verify StagedRows created
      5. Verify LineItems created (if confidence >= 0.75)

    - Performance test:
      1. Time the parsing of each sample PDF
      2. Assert < 3 seconds per PDF

    Accuracy metric:
    For each row, compare each canonical field with gold data.
    `matched = sum(1 for field in canonical_fields if parsed[field] == gold[field] or (parsed[field] is None and gold[field] is None))`
    `accuracy = matched / total_fields`
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -m pytest tests/test_accuracy.py -v --tb=short
  </verify>
  <done>All 3 bill types achieve ≥90% accuracy, end-to-end flow verified, parsing < 3s</done>
</task>

## Success Criteria
- [ ] Parser unit tests pass (column resolver, confidence, sanity checks)
- [ ] 3 sample PDFs parsed with ≥90% field-level accuracy vs gold data
- [ ] End-to-end API upload → parse → store verified
- [ ] Parsing performance < 3s per PDF
- [ ] All previous tests still pass (no regressions)
