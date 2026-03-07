---
phase: 4
plan: 3
wave: 2
---

# Plan 4.3: Payment Status Tracking

## Objective
Add payment tracking per document — paid/unpaid/partial status, payment date, and amount. Update the bills list and detail pages to show payment status.

## Context
- c:\PharMgmt\src\pharmgmt\models\ — Payment model exists with status/amount fields
- Document model can link to payments

## Tasks

<task type="auto">
  <name>Payment tracking API endpoints</name>
  <files>
    c:\PharMgmt\src\pharmgmt\api\routes.py
    c:\PharMgmt\src\pharmgmt\api\schemas.py
  </files>
  <action>
    Add API endpoints:
    `GET /api/documents/{id}/payments` — list payments for a doc
    `POST /api/documents/{id}/payments` — record a payment
      - Body: {amount_paise, payment_date, method, notes}
      - Creates Payment record linked to document
      - Updates document payment status (paid/partial/unpaid)
    `GET /api/payments/summary` — overall payment stats
      - total_paid, total_unpaid, total_partial, total_amount

    Auto-calculate bill total from line items (sum of price_paise × issue_qty)
    Compare against payments to determine status
  </action>
  <verify>
    .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>Payment API creates/lists payments and calculates status</done>
</task>

<task type="auto">
  <name>Payment UI on bill detail</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\bill-detail.js
    c:\PharMgmt\src\pharmgmt\static\js\pages\bills.js
  </files>
  <action>
    Update bill detail page:
    - New tab: "Payments"
    - Shows bill total (calculated from line items)
    - Payment history list with date, amount, method
    - "Record Payment" button → modal with amount, date, method, notes
    - Payment status badge on header (paid=green, partial=yellow, unpaid=red)

    Update bills list:
    - Add payment status badge column
    - Filter option: "Paid" / "Unpaid" / "Partial"
  </action>
  <verify>
    Navigate to bill detail → Payments tab → record a payment → status updates
  </verify>
  <done>Payment recording and status tracking working on bill detail</done>
</task>

## Success Criteria
- [ ] Payment records created via API
- [ ] Bill total auto-calculated from line items
- [ ] Payment status (paid/unpaid/partial) computed
- [ ] Payments tab on bill detail with recording modal
- [ ] Bills list shows payment status badges
