---
phase: 4
plan: 1
wave: 1
---

# Plan 4.1: Expiry Alert System & Monitoring

## Objective
Build the backend logic and API endpoint for expiry monitoring (30/60/90 day warnings) and a dashboard alerts page showing products nearing or past expiry.

## Context
- c:\PharMgmt\src\pharmgmt\models\ — LineItem model has `expiry` field (stored as string, e.g. "03/2027")
- c:\PharMgmt\src\pharmgmt\api\routes.py — existing endpoints
- c:\PharMgmt\src\pharmgmt\static\js\pages\dashboard.js — dashboard page

## Tasks

<task type="auto">
  <name>Expiry alert backend service and API</name>
  <files>
    c:\PharMgmt\src\pharmgmt\services\alerts.py
    c:\PharMgmt\src\pharmgmt\api\routes.py
  </files>
  <action>
    Create `alerts.py` service:
    - `get_expiry_alerts(session, days_ahead=[30,60,90])` → scans LineItem expiry dates
    - Parse expiry strings into dates (handle "MM/YYYY", "DD/MM/YYYY", "YYYY-MM-DD" formats)
    - Categorize: expired, expiring_30d, expiring_60d, expiring_90d
    - Return list: {product, batch, expiry_date, days_remaining, severity, document_id}
    - Sort by days_remaining ascending (most urgent first)

    Add API endpoint:
    `GET /api/alerts/expiry` — returns expiry alerts grouped by severity
    - Query params: days=90 (configurable lookahead)
    - Response: {expired: [...], warning_30d: [...], warning_60d: [...], warning_90d: [...], total_alerts: N}
  </action>
  <verify>
    .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>Expiry alerts API returns products grouped by urgency</done>
</task>

<task type="auto">
  <name>Expiry alerts UI page</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\alerts.js
    c:\PharMgmt\src\pharmgmt\static\index.html
  </files>
  <action>
    Create alerts page (`alerts.js`):
    - Summary cards: Expired (red), <30 Days (orange), <60 Days (yellow), <90 Days (blue)
    - Table below grouped by severity with color-coded rows:
      - Product Name, Batch No, Expiry Date, Days Remaining, Bill File, Action (View Bill →)
    - Expired section highlighted prominently at top
    - Empty state if no alerts

    Update sidebar: add "⚠️ Alerts" nav item between Staging Review and version
    Update router: add /alerts route
    Update dashboard: show alert count in a card if alerts > 0 (with link to /alerts)
  </action>
  <verify>
    Navigate to #/alerts → see expiry warnings grouped by severity
  </verify>
  <done>Alerts page shows expiry warnings with color-coded severity</done>
</task>

## Success Criteria
- [ ] Expiry dates parsed from multiple formats
- [ ] Alerts grouped into expired/30d/60d/90d buckets
- [ ] API endpoint returns structured alert data
- [ ] UI page shows alerts with severity color-coding
- [ ] Dashboard shows alert count
