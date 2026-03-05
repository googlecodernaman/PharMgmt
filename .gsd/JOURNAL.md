# JOURNAL.md — Development Journal

## 2026-03-05 — Project Initialized
- Ran `/install` to set up GSD framework
- Ran `/new-project` with deep questioning phase
- Defined canonical schema for document and line-item extraction
- Identified 3+ bill types as parsing targets
- Created SPEC.md (FINALIZED) and ROADMAP.md (5 phases)
- Stack: Python / FastAPI / SQLite / pdfplumber

## 2026-03-05 — Post-Review Refinement
- Incorporated detailed user review feedback
- Expanded schema: 8 canonical tables + 3 staging tables + schema_meta
- Added staging pipeline (raw → extracted → staged → canonical)
- Added parser contract JSON format
- Added data normalization rules (paisa for money, ISO dates, SHA-256 hashes)
- Added performance indices
- Added risk register (5 risks)
- Expanded Phase 1 from 5 deliverables to 12
- Added 4 new ADRs (ADR-004 through ADR-007)
- Enhanced acceptance criteria with measurable targets
