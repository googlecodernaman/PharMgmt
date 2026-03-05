# STATE.md — Project State

> **Last Updated**: 2026-03-05
> **Current Phase**: Not started
> **Session**: Post-review refinement

## Active Context
- Project initialized with `/new-project`
- SPEC.md finalized with expanded canonical schema (8 tables + 3 staging tables)
- ROADMAP.md updated with detailed Phase 1 (12 deliverables)
- DECISIONS.md has 7 ADRs
- Next step: `/plan 1` to plan Phase 1 execution

## Recent Decisions
- Python + FastAPI + SQLite + SQLAlchemy stack
- pdfplumber primary, camelot-py fallback, Tesseract OCR optional
- Local web app served via FastAPI
- Money stored as integer paisa
- Staging pipeline: raw → extracted → staged → canonical
- SHA-256 file hash for deduplication
- Parser confidence threshold 0.75 for human review flag

## Blockers
None

## Working Memory
- 8 canonical tables + 3 staging tables defined in SPEC.md
- Parser contract JSON defined
- 3 bill types: Sales & Stock Statement, Batch-wise Stock, Short Sales & Stock
- Target: 10-20 bills/day, low-end Windows hardware
- Acceptance: ≥90% field-level match on labeled gold data
