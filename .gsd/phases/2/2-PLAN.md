---
phase: 2
plan: 2
wave: 1
---

# Plan 2.2: Parser Core — Table Extraction to Canonical Rows

## Objective
Build the core PDF parser that takes extracted tables, applies bill type detection, maps columns via the rules engine, and produces a list of canonical rows with confidence scores.

## Context
- c:\PharMgmt\src\pharmgmt\parsing\mapping_config.py — Mapping configs (from Plan 2.1)
- c:\PharMgmt\src\pharmgmt\parsing\column_resolver.py — Column resolver (from Plan 2.1)
- c:\PharMgmt\src\pharmgmt\services\text_extraction.py — PDF text/table extraction
- .gsd/SPEC.md — Parser contract JSON format

## Tasks

<task type="auto">
  <name>Create the core table parser</name>
  <files>
    c:\PharMgmt\src\pharmgmt\parsing\table_parser.py
  </files>
  <action>
    Create `table_parser.py`:
    - `parse_tables(pages: list[dict], mapping: MappingConfig | None = None) -> dict`:
      Main entry point. Takes the output from `extract_text_from_pdf()` (list of {page, text, tables}).
      
      Algorithm:
      1. If no mapping provided, concatenate all page text and call `detect_bill_type()` to auto-detect
      2. For each page, for each table on that page:
         a. Extract the first row as headers
         b. Call `match_headers()` to get column mapping
         c. For each subsequent row:
            - Skip if matches skip_patterns (totals, subtotals, blank rows)
            - Call `resolve_row()` to get canonical dict
            - Assign page number and row_index
            - Compute per-row confidence
         d. Collect all canonical rows
      3. Compute aggregate metrics: rows_parsed, rows_flagged (confidence < 0.5), avg_confidence
      4. Return `parse_result` dict matching the SPEC contract:
         {document: {...}, rows: [...], meta: {...}}

    - `_is_header_row(row: list[str]) -> bool`: Heuristic to detect if a row is a table header (all text, no numbers)
    - `_is_skip_row(row: list[str], patterns: list[str]) -> bool`: Check against skip_patterns
    - `_extract_document_metadata(full_text: str) -> dict`: Extract supplier name, GSTIN, report dates from header text using regex patterns

    IMPORTANT:
    - Some PDFs have multiple tables per page with repeated headers — handle gracefully
    - Some tables span multiple pages — consecutive tables with same column structure should be merged
    - Handle the case where pdfplumber returns None for a table cell
    - Log parsing progress at INFO level
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.parsing.table_parser import parse_tables; print('Table parser imports OK')"
  </verify>
  <done>parse_tables() produces parse_result dict matching SPEC contract from extracted page data</done>
</task>

<task type="auto">
  <name>Create sample PDF generators for testing</name>
  <files>
    c:\PharMgmt\tests\fixtures\generate_samples.py
  </files>
  <action>
    Create `tests/fixtures/generate_samples.py` — a script that generates 3 sample PDFs using reportlab, one per bill type:

    1. `sample_sales_stock.pdf` — Sales & Stock Statement:
       - Header: "SUPPLIER ABC - Sales & Stock Statement"
       - Sub-header: "Period: 01/01/2025 to 31/01/2025", "GSTIN: 29AABCU9603R1ZM"
       - Table with columns: Product, Pack, Op Bal, Pur, Total, Sales, Cl Bal
       - 5-8 product rows with realistic pharma data
       - A subtotal row at the end

    2. `sample_batch_stock.pdf` — Batch-wise Stock Report:
       - Header: "Batch-wise Stock Report"
       - Table with columns: Product, Pack, Batch, Expiry, Stock, MRP, Distributor
       - 5-8 rows with batch/expiry data
       
    3. `sample_short_sales.pdf` — Short Sales & Stock Statement:
       - Header: "Short Sales & Stock Statement"
       - Table with columns: Product, Op Bal, Pur, Total, Sales, Cl Bal, CP
       - 5-8 rows

    Each PDF should use simple drawString and drawTable to create parseable text+tables.
    Add a `generate_all()` function and a `if __name__ == "__main__"` block.
    
    Also create `tests/fixtures/expected/` directory with JSON files containing the expected canonical output for each sample PDF (gold data for accuracy testing).
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python tests/fixtures/generate_samples.py && dir tests\fixtures\*.pdf
  </verify>
  <done>3 sample PDFs generated, matching gold JSON files created</done>
</task>

## Success Criteria
- [ ] parse_tables() processes extracted pages and returns parse_result contract
- [ ] Bill type auto-detection selects correct mapping
- [ ] Multi-table and multi-page PDFs handled
- [ ] 3 sample PDFs with gold data for accuracy testing
