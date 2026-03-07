---
phase: 3
plan: 2
wave: 1
---

# Plan 3.2: Dashboard Home & File Upload Page

## Objective
Build the dashboard home page (stats, recent bills, alerts) and the PDF upload page with drag-and-drop. These are the two most-used pages and establish the interaction patterns.

## Context
- Plan 3.1: App shell, design system, API client
- c:\PharMgmt\src\pharmgmt\api\routes.py — Existing /health, /api/documents, /api/upload endpoints

## Tasks

<task type="auto">
  <name>Create additional API endpoints for dashboard stats</name>
  <files>
    c:\PharMgmt\src\pharmgmt\api\routes.py
  </files>
  <action>
    Add new API endpoint:
    `GET /api/stats` — Returns dashboard statistics:
    - total_documents: count of all documents
    - total_line_items: count of all line items
    - documents_needing_review: count where parsing_run.needs_review = 1
    - recent_uploads: last 5 documents (id, file_name, ingest_ts, avg_confidence)
    - bill_type_breakdown: {sales_stock: N, batch_stock: N, short_sales: N}
    - avg_confidence_overall: average across all parsing runs

    Add Pydantic schema `StatsResponse` to schemas.py.
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path')]; print(routes)"
  </verify>
  <done>/api/stats endpoint returns dashboard statistics</done>
</task>

<task type="auto">
  <name>Build dashboard home page and upload page</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\dashboard.js
    c:\PharMgmt\src\pharmgmt\static\js\pages\upload.js
  </files>
  <action>
    Dashboard page (`dashboard.js`):
    - Hero stat cards row: Total Bills, Total Products, Needs Review, Avg Confidence
    - Each stat card has icon (emoji or SVG), value, label, and subtle gradient background
    - Recent uploads table: file_name, date, bill_type badge, confidence bar, view action
    - "Bills Needing Review" alert section with warning styling if count > 0
    - Loading skeleton while fetching
    - Empty state with upload CTA if no documents

    Upload page (`upload.js`):
    - Large drag-and-drop zone (.file-drop) with:
      - Dashed border, animated on hover
      - Icon + "Drop PDF here or click to browse"
      - File input hidden, triggered by click
    - File validation: PDF only, max 50MB
    - Upload progress bar (animated)
    - Parse result display after upload:
      - Bill type detected badge
      - Rows parsed, confidence bar, warnings list
      - Success/error toast notification
    - Recent uploads list below the drop zone

    IMPORTANT:
    - Both pages fetch data from API on load
    - Smooth transitions between loading → loaded states
    - Error states handled gracefully with retry option
  </action>
  <verify>
    Start server, navigate to dashboard → see stats, navigate to upload → upload a sample PDF → see parse result
  </verify>
  <done>Dashboard shows live stats and recent uploads, upload page ingests PDFs with real-time feedback</done>
</task>

## Success Criteria
- [ ] /api/stats endpoint returns real statistics
- [ ] Dashboard shows stat cards, recent uploads table, review alerts
- [ ] Upload page has working drag-and-drop PDF ingestion
- [ ] Parse results displayed after upload (rows, confidence, warnings)
