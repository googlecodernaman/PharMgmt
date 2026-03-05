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
**Rationale**: Simplifies architecture, eliminates sync complexity, and ensures offline independence. Multi-location sync can be considered in a future version.
