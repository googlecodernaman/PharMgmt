---
phase: 4
plan: 4
wave: 2
---

# Plan 4.4: Reports & Export

## Objective
Build report generation: purchase reports, stock summaries, and automatic sanity reports. All exportable as CSV and print-friendly.

## Context
- Existing CSV export on bill detail
- LineItem, Document, ParsingRun models available
- Dashboard page needs report links

## Tasks

<task type="auto">
  <name>Report generation endpoints</name>
  <files>
    c:\PharMgmt\src\pharmgmt\services\reports.py
    c:\PharMgmt\src\pharmgmt\api\routes.py
  </files>
  <action>
    Create `reports.py` service:
    - `purchase_report(session, date_from, date_to)` → all line items in date range
      - Group by supplier, then product
      - Total quantities and amounts per product and supplier
    - `stock_summary(session)` → current stock snapshot
      - Per product: latest closing_qty, latest price, total across bills
    - `sanity_report(session)` → all flagged issues
      - Documents with warnings, rows with arithmetic mismatches, low confidence

    Add API endpoints:
    `GET /api/reports/purchases?from=&to=` — purchase report data
    `GET /api/reports/stock` — stock summary
    `GET /api/reports/sanity` — sanity report
    `GET /api/reports/purchases/csv` — download as CSV
    `GET /api/reports/stock/csv` — download as CSV
  </action>
  <verify>
    .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>Report APIs return structured data and CSV downloads</done>
</task>

<task type="auto">
  <name>Reports UI page</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\reports.js
    c:\PharMgmt\src\pharmgmt\static\index.html
  </files>
  <action>
    Create reports page (`reports.js`):
    - Three report sections as cards:

    1. Purchase Report:
       - Date range picker (from/to inputs)
       - Generate button → table with supplier × product × qty × amount
       - "Export CSV" and "Print" buttons
       - Print: open in new window with clean white theme for printing

    2. Stock Summary:
       - Table: Product, Pack, Current Stock, Latest Price, Value
       - Total row at bottom
       - Export CSV button

    3. Sanity Report:
       - Flagged documents with error details
       - Rows with arithmetic mismatches or missing data
       - Severity color coding

    Add sidebar: "📋 Reports" nav item
    Add router: /reports route

    Print stylesheet:
    - @media print rules in CSS for clean printing
    - Hide sidebar, header, buttons when printing
  </action>
  <verify>
    Navigate to #/reports → generate purchase report → export CSV → verify print view
  </verify>
  <done>Reports page generates, displays, exports, and prints all report types</done>
</task>

## Success Criteria
- [ ] Purchase report with date range and grouping
- [ ] Stock summary with current quantities and values
- [ ] Sanity report with flagged issues
- [ ] CSV export for all reports
- [ ] Print-friendly views
