---
phase: 4
plan: 2
wave: 1
---

# Plan 4.2: Supplier Price Comparison

## Objective
Build supplier analytics: compare prices across bills for the same product, detect price changes, and show price history on the products page.

## Context
- LineItem has: product_name_raw, price_paise, document_id
- Document has: file_name, supplier_name (from metadata), ingest_ts

## Tasks

<task type="auto">
  <name>Price comparison backend and API</name>
  <files>
    c:\PharMgmt\src\pharmgmt\services\analytics.py
    c:\PharMgmt\src\pharmgmt\api\routes.py
  </files>
  <action>
    Create `analytics.py` service:
    - `get_price_history(session, product_name)` → returns all price points for a product across bills
      - [{date, price_paise, document_id, file_name, supplier}]
    - `get_price_changes(session)` → products with price changes between bills
      - [{product, old_price, new_price, change_pct, dates}]
    - `get_supplier_comparison(session)` → same product at different supplier prices

    Add API endpoints:
    `GET /api/analytics/prices?product=<name>` — price history for a product
    `GET /api/analytics/price-changes` — all products with price changes
  </action>
  <verify>
    .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>Price comparison API returns history and change detection</done>
</task>

<task type="auto">
  <name>Price analytics UI</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\analytics.js
    c:\PharMgmt\src\pharmgmt\static\index.html
  </files>
  <action>
    Create analytics page (`analytics.js`):
    - Tab 1: Price Changes — table of products with price changes
      - Product, Previous MRP, Current MRP, Change %, Date, Trend indicator (↑↓)
      - Color: green for decrease, red for increase
    - Tab 2: Supplier Comparison — same product prices from different suppliers
    - Click product → expandable section with full price history timeline

    Add to sidebar: "📈 Analytics" nav item
    Add to router: /analytics route
  </action>
  <verify>
    Navigate to #/analytics → see price changes and supplier comparison
  </verify>
  <done>Analytics page shows price trends and supplier comparison</done>
</task>

## Success Criteria
- [ ] Price history tracked per product across bills
- [ ] Price change detection with percentage
- [ ] Analytics page with price trends table
- [ ] Supplier comparison view
