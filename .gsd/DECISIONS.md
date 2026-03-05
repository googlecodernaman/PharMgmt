# DECISIONS.md — Architecture Decision Records

## ADR-001: Python + FastAPI + SQLite Stack
**Date**: 2026-03-05
**Status**: Accepted
**Context**: Need offline-first system on low-end Windows. Must parse PDF tables without paid APIs.
**Decision**: Python backend with FastAPI, SQLite database, pdfplumber for PDF extraction, local web UI.
**Rationale**: Python has the best PDF parsing ecosystem. SQLite is zero-config and file-based. FastAPI is lightweight and fast. All free and offline-capable.

## ADR-002: Local Web App (not Desktop App)
**Date**: 2026-03-05
**Status**: Accepted
**Context**: Need a user interface accessible to non-technical pharmacy staff.
**Decision**: Serve a web app locally via FastAPI, accessed through the browser.
**Rationale**: Simpler to build and maintain than Electron/Tauri. No need for desktop framework overhead. Browser provides consistent rendering. Staff are familiar with web interfaces.

## ADR-003: Independent Instances per Location
**Date**: 2026-03-05
**Status**: Accepted
**Context**: System used across multiple pharmacy locations.
**Decision**: Each location runs its own independent instance with local data.
**Rationale**: Simplifies architecture, eliminates sync complexity, and ensures offline independence.

## ADR-004: Money Stored as Integer Paisa
**Date**: 2026-03-05
**Status**: Accepted
**Context**: Need to store MRP, prices without floating-point precision issues.
**Decision**: All monetary values stored as integer paisa (1 INR = 100 paise).
**Rationale**: Avoids float rounding errors in price comparison and aggregation. Standard practice for financial data in SQLite.

## ADR-005: Staging Pipeline for QA
**Date**: 2026-03-05
**Status**: Accepted
**Context**: Parser accuracy will vary across supplier formats. Need ability to review and correct extractions.
**Decision**: Three-stage pipeline: `raw_files` → `extracted_text` → `staged_rows` → canonical tables. Staged rows can be accepted/rejected/corrected before promotion.
**Rationale**: Allows re-parsing without overwriting canonical data. Enables human-in-the-loop QA. Corrections feed back into parser improvement.

## ADR-006: File Deduplication via SHA-256
**Date**: 2026-03-05
**Status**: Accepted
**Context**: Same PDF may be uploaded multiple times.
**Decision**: Compute SHA-256 hash of raw PDF bytes; enforce UNIQUE constraint on `original_file_hash`.
**Rationale**: Prevents duplicate ingestion. Cheap to compute even on low-end hardware.

## ADR-007: Parser Confidence & Human Review Threshold
**Date**: 2026-03-05
**Status**: Accepted
**Context**: Need to surface low-quality extractions for human review.
**Decision**: Each row gets a `parser_confidence` (0.0–1.0). Documents with `avg_confidence < 0.75` auto-flagged `needs_review = 1`.
**Rationale**: Prevents bad data from entering canonical tables silently. Threshold is adjustable.
