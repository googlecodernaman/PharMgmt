---
phase: 3
plan: 3
wave: 2
---

# Plan 3.3: Bill List & Bill Detail Views

## Objective
Build the bill list page (search, filter, sort, pagination) and the bill detail page (document metadata, parsed line items table, raw text view). These are the core data browsing pages.

## Context
- c:\PharMgmt\src\pharmgmt\api\routes.py — GET /api/documents, GET /api/documents/{id}
- Plan 3.1: Design system, router, API client

## Tasks

<task type="auto">
  <name>Build bill list page</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\bills.js
  </files>
  <action>
    Bill list page (`bills.js`):
    - Search bar at top (searches file_name, supplier)
    - Filter pills: All / Needs Review / High Confidence
    - Sort dropdown: Newest First, Oldest First, Confidence ↑, Confidence ↓
    - Results table with columns:
      - File Name (linked to detail)
      - Bill Type badge
      - Date
      - Rows parsed
      - Confidence (color-coded bar)
      - Status (review/accepted badge)
    - Pagination controls (prev/next, page indicator)
    - Empty state if no documents
    - Skeleton loading states
    - Click row → navigate to #/bills/:id

    IMPORTANT:
    - Client-side search/filter for loaded data (server-side pagination)
    - Smooth table row hover animations
    - Responsive: cards layout on mobile, table on desktop
  </action>
  <verify>
    Navigate to #/bills → see list of uploaded documents, search/filter works, click opens detail
  </verify>
  <done>Bill list shows all documents with working search, filter, sort, and pagination</done>
</task>

<task type="auto">
  <name>Build bill detail page</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\bill-detail.js
  </files>
  <action>
    Bill detail page (`bill-detail.js`):
    - Header: file name, bill type badge, confidence score, status
    - Metadata card: supplier, GSTIN, report dates, ingest date, pages
    - Tabs: Line Items | Raw Text
    - Line Items tab:
      - Full-width table with all canonical fields
      - Columns: #, Product, Pack, Batch, Expiry, Open, Rcpt, Total, Sales, Close, MRP, Confidence
      - Color-coded confidence per row (green ≥0.8, yellow ≥0.5, red <0.5)
      - Rows with warnings show ⚠️ icon with tooltip
      - Sortable columns
    - Raw Text tab:
      - Pre-formatted extracted text
      - Page numbers indicated
    - Back button to #/bills
    - Export CSV button (downloads line items as CSV)

    CSV export:
    - Generate CSV from line items data
    - Download as `{file_name}_export.csv`
    - Headers match canonical field names

    IMPORTANT:
    - Table scrolls horizontally on mobile
    - Sticky header on table
    - No pagination on line items (typically <100 rows per bill)
  </action>
  <verify>
    Upload a sample PDF, navigate to its detail → see metadata, line items table, toggle raw text, export CSV
  </verify>
  <done>Bill detail shows metadata, interactive line items table with confidence coloring, raw text tab, and CSV export</done>
</task>

## Success Criteria
- [ ] Bill list page with search, filter, sort, pagination
- [ ] Bill detail page with metadata, line items table, raw text
- [ ] Confidence color-coding on rows
- [ ] CSV export downloads correctly
- [ ] Responsive layout on both views
