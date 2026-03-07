---
phase: 3
plan: 4
wave: 2
---

# Plan 3.4: Product/Inventory View & Staging Review

## Objective
Build the product aggregation view (all products across bills with stock summaries) and the staging review UI for flagged documents (accept/override/reject controls).

## Context
- c:\PharMgmt\src\pharmgmt\models\ — Product, LineItem, StagedRow models
- c:\PharMgmt\src\pharmgmt\api\routes.py — Need new endpoints for products and staging

## Tasks

<task type="auto">
  <name>Add API endpoints for products and staging</name>
  <files>
    c:\PharMgmt\src\pharmgmt\api\routes.py
    c:\PharMgmt\src\pharmgmt\api\schemas.py
  </files>
  <action>
    New endpoints:

    `GET /api/products` — Aggregated product view:
    - Query line items, group by product_name_raw (normalized)
    - For each product: name, total_opening, total_closing, latest_price, bill_count, latest_expiry
    - Support search by product name
    - Pagination

    `GET /api/staging` — Documents needing review:
    - List all documents where parsing_run.needs_review = 1
    - Include doc metadata and row count

    `GET /api/staging/{doc_id}` — Staged rows for a document:
    - Return staged rows with raw_data and canonical_data
    - Include document raw_text for side-by-side view

    `POST /api/staging/{doc_id}/accept` — Accept all staged rows:
    - Move staged_rows status → 'accepted'
    - Create LineItem records from canonical_data
    - Update parsing_run.needs_review → 0

    `POST /api/staging/{doc_id}/reject` — Reject a document:
    - Move staged_rows status → 'rejected'
    - Update parsing_run.needs_review → 0

    `PATCH /api/staging/{doc_id}/rows/{row_id}` — Override a staged row:
    - Update canonical_data with user corrections
    - Set status → 'corrected'

    Add Pydantic schemas for all new endpoints.
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.main import app; print([r.path for r in app.routes if hasattr(r, 'path')])"
  </verify>
  <done>All new API endpoints registered and functional</done>
</task>

<task type="auto">
  <name>Build product view and staging review pages</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\products.js
    c:\PharMgmt\src\pharmgmt\static\js\pages\staging.js
  </files>
  <action>
    Product view (`products.js`):
    - Search bar for product name
    - Table: Product Name, Pack, Latest Stock, Latest Price, Bill Count, Latest Expiry
    - Expiry cells highlighted: red if expired, yellow if <30 days
    - Click product → expandable row showing all bills containing that product
    - Pagination

    Staging review (`staging.js`):
    - List of flagged documents with confidence bars and warning counts
    - Click document → opens review panel:
      - Left: raw extracted text (scrollable, page-numbered)
      - Right: parsed rows table (editable cells)
      - Top: document metadata + overall confidence
    - Action buttons per document:
      - Accept All (green) — creates line items from staged data
      - Reject (red) — discards staged data
    - Per-row actions:
      - Edit cell → inline edit with save
    - After accept/reject → document removed from staging list with animation
    - Confirmation modal before accept/reject

    IMPORTANT:
    - Staging review is optimized for side-by-side comparison
    - Inline editing saves to API immediately
    - Visual feedback (toasts) for all actions
  </action>
  <verify>
    Upload a low-confidence PDF → appears in staging review → edit fields → accept → verify line items created
  </verify>
  <done>Products page shows aggregated inventory, staging review works with accept/reject/edit</done>
</task>

## Success Criteria
- [ ] Products view shows aggregated inventory across all bills
- [ ] Product search and expiry highlighting works
- [ ] Staging review shows side-by-side raw text vs parsed data
- [ ] Accept/reject/edit controls function correctly
- [ ] Line items created from accepted staged rows
