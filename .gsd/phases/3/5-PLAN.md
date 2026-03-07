---
phase: 3
plan: 5
wave: 3
---

# Plan 3.5: Polish, Responsive, & Integration Testing

## Objective
Final polish pass: ensure responsive design on all pages, add micro-animations, fix edge cases, and run end-to-end browser tests. This is the Phase 3 acceptance gate.

## Context
- Plans 3.1-3.4: All pages built
- c:\PharMgmt\tests\ — Existing test suite

## Tasks

<task type="auto">
  <name>Responsive polish and micro-animations</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\css\index.css
    c:\PharMgmt\src\pharmgmt\static\css\components.css
    c:\PharMgmt\src\pharmgmt\static\css\responsive.css
  </files>
  <action>
    Create `responsive.css`:
    - Mobile (<768px): sidebar collapses to hamburger, tables scroll horizontally, stat cards stack vertically, staging review stacks vertically (raw text above, parsed below)
    - Tablet (768-1024px): sidebar narrows to icons, 2-column stat cards
    - Desktop (>1024px): full sidebar, full tables

    Polish all pages:
    - Page transition fade animations
    - Card hover lift effect (transform + shadow)
    - Button press feedback (scale down briefly)
    - Table row hover highlight
    - Loading → loaded skeleton-to-content transition
    - Toast slide-in from top-right with auto-dismiss
    - File drop zone pulse animation while dragging
    - Confidence bars animate on load
    - Modal fade-in with backdrop blur
    - Sidebar active indicator slide animation

    Accessibility:
    - Focus visible outlines on all interactive elements
    - aria-labels on icon-only buttons
    - Keyboard navigation (Tab, Enter, Escape for modals)

    IMPORTANT:
    - All animations respect prefers-reduced-motion
    - No animation exceeds 300ms
    - Touch targets ≥44px on mobile
  </action>
  <verify>
    Resize browser to mobile/tablet/desktop → all layouts adapt correctly
    Tab through interactive elements → focus is visible
  </verify>
  <done>All pages responsive, micro-animations smooth, accessible keyboard navigation</done>
</task>

<task type="auto">
  <name>End-to-end flow testing</name>
  <files>
    c:\PharMgmt\tests\test_e2e.py
  </files>
  <action>
    Update API tests to cover new endpoints:
    - GET /api/stats → returns correct counts
    - GET /api/products → returns aggregated products
    - GET /api/staging → returns flagged documents
    - POST /api/staging/{id}/accept → creates line items
    - POST /api/staging/{id}/reject → updates status

    End-to-end flow test:
    1. Upload 3 sample PDFs (one per bill type)
    2. Verify /api/stats shows total_documents=3
    3. Verify /api/documents lists all 3
    4. Verify /api/documents/{id} shows line items
    5. Verify /api/products shows aggregated products
    6. If any need review → accept via /api/staging/{id}/accept → verify line items created

    Run all tests: `.venv\Scripts\python -m pytest tests/ -v`
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>All tests pass including new API endpoints and E2E flow</done>
</task>

## Success Criteria
- [ ] All pages responsive at mobile/tablet/desktop breakpoints
- [ ] Micro-animations smooth and respect reduced-motion
- [ ] Keyboard navigation works on all interactive elements
- [ ] End-to-end API tests cover all new endpoints
- [ ] Full upload → view → review → accept flow verified
- [ ] All previous tests still pass (no regressions)
