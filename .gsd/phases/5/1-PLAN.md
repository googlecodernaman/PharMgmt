---
phase: 5
plan: 1
wave: 1
---

# Plan 5.1: Performance Tuning & SQLite WAL

## Objective
Optimize for low-end hardware: enable SQLite WAL mode, add query indexes, implement lazy loading on frontend lists, and optimize pdfplumber extraction.

## Tasks

<task type="auto">
  <name>Database and backend performance</name>
  <files>
    c:\PharMgmt\src\pharmgmt\db.py
    c:\PharMgmt\src\pharmgmt\models\base.py
    c:\PharMgmt\src\pharmgmt\api\routes.py
  </files>
  <action>
    1. Enable SQLite WAL mode in db.py on connection:
       - `connection.execute("PRAGMA journal_mode=WAL")`
       - `connection.execute("PRAGMA synchronous=NORMAL")`
    2. Add database indexes to models:
       - LineItem: index on (document_id), (product_name_raw)
       - Document: index on (ingest_ts), (file_name)
       - StagedRow: index on (document_id, status)
    3. Optimize heavy queries in routes.py:
       - /api/stats: use COUNT queries instead of loading all objects
       - /api/products: ensure GROUP BY uses indexed columns
    4. Add pagination to all list endpoints that don't have it
  </action>
  <verify>
    .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>WAL mode enabled, indexes added, queries optimized</done>
</task>

<task type="auto">
  <name>Frontend lazy loading and performance</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\bills.js
    c:\PharMgmt\src\pharmgmt\static\js\pages\products.js
    c:\PharMgmt\src\pharmgmt\static\js\pages\reports.js
  </files>
  <action>
    1. Bills page: load only 20 items initially, "Load More" button or scroll pagination
    2. Products page: paginate product list (20 per page with server-side pagination)
    3. Reports: limit initial display to 50 rows, "Show All" toggle
    4. Add debounce (300ms) to all search inputs to reduce API calls
    5. Cache API responses in a simple JS object for 30s to avoid re-fetching on route back-navigation
  </action>
  <verify>
    Navigate through pages — verify smooth performance and pagination
  </verify>
  <done>Lazy loading and pagination on all heavy list pages</done>
</task>

## Success Criteria
- [ ] SQLite WAL mode active
- [ ] DB indexes on hot columns
- [ ] Pagination on all list pages
- [ ] Search inputs debounced
