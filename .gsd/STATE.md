# STATE.md — Project State

> **Last Updated**: 2026-03-05
> **Current Phase**: Not started
> **Session**: Initial setup

## Active Context
- Project initialized with `/new-project`
- SPEC.md finalized
- ROADMAP.md created with 5 phases
- Next step: `/plan 1` to plan Phase 1

## Recent Decisions
- Python + FastAPI + SQLite stack chosen
- pdfplumber for PDF table extraction
- Local web app served via FastAPI (no Electron)
- Each pharmacy location runs independently
- No OCR — PDFs have extractable text

## Blockers
None

## Working Memory
- Canonical schema defined in SPEC.md
- 3 bill types identified as parsing targets
- Target: 10-20 bills/day, low-end Windows hardware
