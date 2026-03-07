---
phase: 4
plan: 5
wave: 3
---

# Plan 4.5: Integration Tests & Phase 4 Verification

## Objective
Write tests for all Phase 4 features (expiry alerts, analytics, payments, reports) and ensure full E2E flow works. Phase 4 acceptance gate.

## Context
- c:\PharMgmt\tests\ — existing test suite (45 tests passing)
- New endpoints: /api/alerts, /api/analytics, /api/payments, /api/reports

## Tasks

<task type="auto">
  <name>Write Phase 4 API tests</name>
  <files>
    c:\PharMgmt\tests\test_phase4.py
  </files>
  <action>
    Test file covering:

    Expiry alerts:
    - Test expiry date parsing (MM/YYYY, DD/MM/YYYY, ISO)
    - Test alert categorization (expired vs 30/60/90d)
    - Test GET /api/alerts/expiry returns structured response

    Analytics:
    - Test price history retrieval
    - Test price change detection
    - Test GET /api/analytics/price-changes

    Payments:
    - Test POST /api/documents/{id}/payments creates payment
    - Test payment status computation (paid/partial/unpaid)
    - Test GET /api/payments/summary

    Reports:
    - Test GET /api/reports/purchases returns data
    - Test GET /api/reports/stock returns aggregated data
    - Test GET /api/reports/sanity returns flagged issues

    E2E flow:
    1. Upload 3 sample PDFs
    2. Verify stats endpoint
    3. Check expiry alerts
    4. Record a payment
    5. Generate purchase report
    6. Verify stock summary

    All tests should use the existing test fixtures (sample PDFs + in-memory SQLite).

    Run: `.venv\Scripts\python -m pytest tests/ -v --tb=short`
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>All Phase 4 tests pass, full E2E flow verified</done>
</task>

## Success Criteria
- [ ] Expiry alert tests pass
- [ ] Analytics tests pass
- [ ] Payment tests pass
- [ ] Report tests pass
- [ ] E2E flow test passes
- [ ] All previous tests still pass (no regressions)
