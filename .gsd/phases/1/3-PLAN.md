---
phase: 1
plan: 3
wave: 2
---

# Plan 1.3: FastAPI Application & API Endpoints

## Objective
Build the FastAPI application skeleton with health check, document listing, and stub upload endpoint returning the parser contract JSON. This enables frontend development and API testing.

## Context
- .gsd/SPEC.md — Parser contract JSON, tech stack
- c:\PharMgmt\src\pharmgmt\models\ — ORM models (from Plan 1.2)
- c:\PharMgmt\src\pharmgmt\db.py — Database initialization (from Plan 1.2)
- c:\PharMgmt\src\pharmgmt\config.py — Settings (from Plan 1.1)

## Tasks

<task type="auto">
  <name>Create FastAPI application with routes</name>
  <files>
    c:\PharMgmt\src\pharmgmt\main.py
    c:\PharMgmt\src\pharmgmt\api\routes.py
    c:\PharMgmt\src\pharmgmt\api\schemas.py
    c:\PharMgmt\src\pharmgmt\api\dependencies.py
    c:\PharMgmt\src\pharmgmt\api\__init__.py
  </files>
  <action>
    Create `api/dependencies.py`:
    - `get_db()` dependency that yields a DB session using db.get_db_session()

    Create `api/schemas.py` (Pydantic response models):
    - `HealthResponse`: status, version, schema_version
    - `DocumentResponse`: id, file_name, supplier_name (nullable), title, report_from, report_to, ingest_ts, page_count (nullable)
    - `DocumentListResponse`: items (list of DocumentResponse), total (int)
    - `ParseResultRow`: page, row_index, raw_text, fields (dict), confidence (float), warnings (list[str])
    - `ParseResultMeta`: parser_version, duration_ms, rows_parsed, rows_flagged, avg_confidence, error_flags (list[str])
    - `ParseResultResponse`: document (dict), rows (list of ParseResultRow), meta (ParseResultMeta)

    Create `api/routes.py`:
    - `GET /health` → returns HealthResponse with version from __init__.py and schema_version from DB
    - `GET /api/documents` → returns DocumentListResponse from DB (paginated: skip, limit query params)
    - `GET /api/documents/{id}` → returns single DocumentResponse with line_items
    - `POST /api/upload` → accepts file upload (multipart), returns stub ParseResultResponse (no actual parsing yet — placeholder for Phase 2). For now: store file, extract basic metadata, return stub response.

    Create/update `main.py`:
    - Create FastAPI app with title="PharMgmt", version from __init__
    - Include router from routes.py
    - Add startup event: call init_db()
    - Serve static files from `static/` directory (for future frontend)
    - Add CORS middleware (allow localhost origins)

    IMPORTANT:
    - All endpoints must handle errors gracefully with proper HTTP status codes
    - Use async where appropriate for file I/O
    - File uploads should be saved to UPLOAD_DIR from config
  </action>
  <verify>
    .venv\Scripts\python -c "from pharmgmt.main import app; print(f'App: {app.title}, routes: {len(app.routes)}')"
  </verify>
  <done>FastAPI app with 4 endpoints importable, router registered, startup event wired</done>
</task>

<task type="auto">
  <name>Create logging infrastructure</name>
  <files>
    c:\PharMgmt\src\pharmgmt\logging_config.py
  </files>
  <action>
    Create `logging_config.py`:
    - Configure Python logging to write to LOG_DIR from config
    - Two handlers: file handler (rotating, 5MB max, 3 backups) + console handler (minimal)
    - Log format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
    - Named loggers: `pharmgmt.api`, `pharmgmt.parsing`, `pharmgmt.db`
    - `setup_logging(log_dir, log_level)` function called at app startup

    IMPORTANT: Logs MUST go to disk files, not just stdout. This is a SPEC requirement.
  </action>
  <verify>
    .venv\Scripts\python -c "from pharmgmt.logging_config import setup_logging; setup_logging('./test_logs', 'INFO'); import logging; logging.getLogger('pharmgmt.api').info('test'); print('Logging OK')"
  </verify>
  <done>Logging writes to rotating file in LOG_DIR, console handler also active</done>
</task>

## Success Criteria
- [ ] `GET /health` returns version and schema_version
- [ ] `GET /api/documents` returns paginated list (empty initially)
- [ ] `POST /api/upload` accepts PDF and returns stub ParseResultResponse
- [ ] Logging writes to disk files in LOG_DIR
- [ ] App starts with `uvicorn pharmgmt.main:app`
