---
phase: 5
plan: 5
wave: 3
---

# Plan 5.5: Documentation & Final Verification

## Objective
Write user documentation (README, usage guide), run full E2E validation, and confirm all 5 phases are complete.

## Tasks

<task type="auto">
  <name>User documentation</name>
  <files>
    c:\PharMgmt\README.md
    c:\PharMgmt\docs\USER_GUIDE.md
  </files>
  <action>
    Update README.md:
    - Project description and screenshot
    - Quick start (install, run, open browser)
    - Features list with screenshots
    - Tech stack overview
    - Development setup

    Create USER_GUIDE.md:
    - Getting started: first upload
    - Understanding the dashboard
    - How parsing works (bill types, confidence)
    - Reviewing staged documents
    - Using reports and exports
    - Backup and restore
    - Troubleshooting common issues
    - CLI commands reference
  </action>
  <verify>
    Read through docs for accuracy and completeness
  </verify>
  <done>Comprehensive README and user guide</done>
</task>

<task type="auto">
  <name>Final E2E validation</name>
  <files>
    c:\PharMgmt\tests\test_e2e.py
  </files>
  <action>
    Full end-to-end test:
    1. Start fresh (empty DB)
    2. Upload 3 sample PDFs
    3. Verify dashboard stats
    4. Check bill list and detail
    5. Verify products aggregation
    6. Check expiry alerts
    7. Record a payment
    8. Generate purchase report
    9. Export CSV
    10. Create backup
    11. Run cleanup
    12. Verify all 45+ existing tests still pass

    Run: `.venv\Scripts\python -m pytest tests/ -v --tb=short`
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>All tests pass, E2E flow verified, project complete</done>
</task>

## Success Criteria
- [ ] README.md with clear quick start
- [ ] USER_GUIDE.md covering all features
- [ ] All tests pass (no regressions)
- [ ] E2E flow verified
