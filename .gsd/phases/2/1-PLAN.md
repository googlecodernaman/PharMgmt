---
phase: 2
plan: 1
wave: 1
---

# Plan 2.1: Column Mapping Rules Engine & Bill Type Detection

## Objective
Build a configurable column-mapping engine that maps diverse column headers from different supplier bill formats to canonical schema fields. Include bill type auto-detection to select the right mapping config.

## Context
- .gsd/SPEC.md — Bill Types table, canonical schema fields
- c:\PharMgmt\src\pharmgmt\parsing\normalizers.py — Existing normalizers
- c:\PharMgmt\src\pharmgmt\models\line_item.py — Canonical LineItem fields

## Tasks

<task type="auto">
  <name>Create column mapping configuration format and loader</name>
  <files>
    c:\PharMgmt\src\pharmgmt\parsing\mapping_config.py
    c:\PharMgmt\src\pharmgmt\parsing\mappings\__init__.py
    c:\PharMgmt\src\pharmgmt\parsing\mappings\sales_stock.yaml
    c:\PharMgmt\src\pharmgmt\parsing\mappings\batch_stock.yaml
    c:\PharMgmt\src\pharmgmt\parsing\mappings\short_sales.yaml
  </files>
  <action>
    Create `mapping_config.py`:
    - Define `MappingConfig` dataclass with:
      - `bill_type`: str (identifier)
      - `display_name`: str
      - `detect_keywords`: list[str] — keywords in PDF text/headers that identify this bill type
      - `header_aliases`: dict[str, list[str]] — maps canonical field name → list of possible column header strings
        Example: {"product_name_raw": ["Product", "Product Name", "Item", "Description"]}
      - `skip_patterns`: list[str] — regex patterns for rows to skip (totals, subtotals, blank)
      - `date_columns`: list[str] — which canonical fields are dates (for auto-normalization)
      - `money_columns`: list[str] — which canonical fields are money (for paisa conversion)
      - `qty_columns`: list[str] — which canonical fields are quantities
    - `load_mapping(bill_type: str) -> MappingConfig`: loads from YAML file
    - `load_all_mappings() -> list[MappingConfig]`: loads all available mappings
    - `detect_bill_type(text: str, tables: list) -> MappingConfig | None`: scans text/headers for detect_keywords, returns best match

    Create 3 YAML mapping files in `mappings/` directory:

    `sales_stock.yaml` — Sales & Stock Statement:
    - detect_keywords: ["Sales & Stock", "Stock Statement", "Sales Statement", "Stock & Sales"]
    - header_aliases mapping Op Bal→opening_qty, Pur→receipt_qty, Total→total_qty, Sales→issue_qty, Cl Bal→closing_qty, etc.

    `batch_stock.yaml` — Batch-wise Stock Report:
    - detect_keywords: ["Batch-wise", "Batch wise", "Batchwise", "Batch Stock"]
    - header_aliases mapping Pack→packing, Batch→batch_no, Expiry→expiry, Stock→closing_qty, MRP→price_paise, etc.

    `short_sales.yaml` — Short Sales & Stock Statement:
    - detect_keywords: ["Short Sales", "Short Stock"]  
    - header_aliases mapping Op Bal→opening_qty, Pur→receipt_qty, Total→total_qty, Sales→issue_qty, Cl Bal→closing_qty, CP→price_paise

    IMPORTANT:
    - Header matching should be case-insensitive and whitespace-tolerant
    - Each YAML file must be self-contained and loadable independently
    - Use PyYAML (already installed as dependency of uvicorn)
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.parsing.mapping_config import load_all_mappings; ms = load_all_mappings(); print(f'{len(ms)} mappings loaded: {[m.bill_type for m in ms]}')"
  </verify>
  <done>3 mapping configs loaded, each with detect_keywords and header_aliases</done>
</task>

<task type="auto">
  <name>Create header matching and column resolver</name>
  <files>
    c:\PharMgmt\src\pharmgmt\parsing\column_resolver.py
  </files>
  <action>
    Create `column_resolver.py`:
    - `normalize_header(raw: str) -> str`: lowercase, strip whitespace, collapse spaces
    - `match_headers(table_headers: list[str], mapping: MappingConfig) -> dict[int, str]`:
      Takes a list of raw column headers from a PDF table and a MappingConfig.
      Returns dict mapping column_index → canonical_field_name.
      Uses fuzzy matching: exact match first, then substring containment, then fallback to unmatched.
      Returns confidence score (0-1) for the overall match quality.
    - `resolve_row(row: list[str], column_map: dict[int, str], mapping: MappingConfig) -> dict`:
      Takes a raw row (list of cell values) and column mapping.
      Returns dict of canonical field → value, applying normalizers:
        - date_columns → normalize_date()
        - money_columns → normalize_money()  
        - qty_columns → parse_quantity()
        - others → normalize_text()
      Store raw_row_text as joined original values.
      Compute per-row confidence based on: non-null fields / expected fields.

    IMPORTANT:
    - Must handle None/empty cells gracefully
    - Must handle columns that don't match any canonical field (ignore them)
    - Must handle rows that are subtotals or blank (skip via skip_patterns)
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.parsing.column_resolver import normalize_header, match_headers; print('Column resolver imports OK')"
  </verify>
  <done>Header matching works with fuzzy matching, row resolver applies correct normalizers per column type</done>
</task>

## Success Criteria
- [ ] 3 YAML mapping configs created and loadable
- [ ] Bill type auto-detection works from PDF text
- [ ] Header matching resolves columns to canonical fields
- [ ] Row resolver applies date/money/qty normalizers correctly
