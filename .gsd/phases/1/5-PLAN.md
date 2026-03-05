---
phase: 1
plan: 5
wave: 3
---

# Plan 1.5: Tests & Developer Runbook

## Objective
Write unit and integration tests that validate the data layer, staging pipeline, and API endpoints. Create the developer runbook for local setup. This is the Phase 1 acceptance gate.

## Context
- c:\PharMgmt\src\pharmgmt\ — All source code from Plans 1.1–1.4
- .gsd/SPEC.md — Acceptance criteria for Phase 1
- c:\PharMgmt\tests\conftest.py — Test fixtures (from Plan 1.1)

## Tasks

<task type="auto">
  <name>Create test fixtures and unit tests</name>
  <files>
    c:\PharMgmt\tests\conftest.py
    c:\PharMgmt\tests\test_models.py
    c:\PharMgmt\tests\test_services.py
    c:\PharMgmt\tests\test_normalizers.py
  </files>
  <action>
    Update `tests/conftest.py`:
    - Fixture `db_session`: creates in-memory SQLite DB, calls init_db, yields session, cleans up
    - Fixture `sample_pdf_path`: path to a test PDF fixture (create a minimal valid PDF using reportlab or use a static fixture file)
    - Fixture `test_client`: FastAPI TestClient using httpx

    Create `tests/test_models.py`:
    - Test Document creation with all required fields
    - Test Supplier creation
    - Test Product creation with raw_names JSON
    - Test LineItem with FK to Document
    - Test Batch with expiry_precision
    - Test Payment status defaults
    - Test SchemaMeta version inserted on init_db
    - Test unique constraint on original_file_hash (duplicate should raise)

    Create `tests/test_services.py`:
    - Test compute_file_hash returns 64-char hex string
    - Test compute_file_hash deterministic (same input → same output)
    - Test ingest_pdf with a sample PDF → document created, raw_file stored, extracted_text rows created
    - Test ingest_pdf duplicate detection → returns error on second ingest of same file

    Create `tests/test_normalizers.py`:
    - Test date normalization: various formats → ISO YYYY-MM-DD
    - Test money normalization: float string → integer paisa
    - Test text normalization: Unicode, whitespace, punctuation handling
    - NOTE: Create `src/pharmgmt/parsing/normalizers.py` with these utility functions:
      - `normalize_date(raw: str) -> tuple[str|None, str]` returns (iso_date, precision)
      - `normalize_money(raw: str) -> int|None` returns paisa
      - `normalize_text(raw: str) -> str` returns cleaned text

    IMPORTANT:
    - Use pytest fixtures for DB session, not global state
    - Each test should be independent (no test ordering dependencies)
    - For the sample PDF, create a minimal PDF in conftest or use a fixture file in tests/fixtures/
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>All tests pass, >80% coverage on models and services</done>
</task>

<task type="auto">
  <name>Create integration tests for API endpoints</name>
  <files>
    c:\PharMgmt\tests\test_api.py
    c:\PharMgmt\tests\fixtures\sample_bill.pdf
  </files>
  <action>
    Create `tests/fixtures/` directory with a minimal sample PDF.
    To create a sample PDF without external dependencies, write a small Python script that uses reportlab (add to dev dependencies) or create a minimal valid PDF byte string.

    Create `tests/test_api.py`:
    - Test `GET /health` returns 200, status="ok", version matches __init__
    - Test `GET /api/documents` returns 200, empty list initially
    - Test `POST /api/upload` with sample PDF returns 200, parse_result structure correct
    - Test `POST /api/upload` duplicate returns 409 (conflict)
    - Test `GET /api/documents` after upload returns 1 document
    - Test `GET /api/documents/{id}` returns document details

    Use FastAPI TestClient (httpx) from conftest fixture.
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -m pytest tests/test_api.py -v --tb=short
  </verify>
  <done>All API endpoint tests pass, upload→list→detail flow verified end-to-end</done>
</task>

<task type="auto">
  <name>Create developer runbook</name>
  <files>
    c:\PharMgmt\docs\dev-runbook.md
  </files>
  <action>
    Create `docs/dev-runbook.md` with:

    1. **Prerequisites**: Python 3.10+, git
    2. **Setup**:
       ```
       git clone <repo>
       cd PharMgmt
       python -m venv .venv
       .venv\Scripts\activate  (Windows)
       pip install -e ".[dev]"
       ```
    3. **Initialize database**:
       ```
       python -m pharmgmt.cli.commands migrate
       ```
    4. **Start server**:
       ```
       python -m pharmgmt.cli.commands serve
       ```
       Then open http://localhost:8000/health
    5. **Ingest a PDF**:
       ```
       python -m pharmgmt.cli.commands ingest path/to/bill.pdf
       ```
    6. **Run tests**:
       ```
       pytest tests/ -v
       ```
    7. **Project structure** — brief description of each package
    8. **Database** — location, schema version, how to reset
  </action>
  <verify>
    Test-Path "c:\PharMgmt\docs\dev-runbook.md"
  </verify>
  <done>Developer runbook covers setup through testing, all steps verified working</done>
</task>

## Success Criteria
- [ ] All unit tests pass (models, services, normalizers)
- [ ] All API integration tests pass (health, documents, upload)
- [ ] Sample PDF fixture exists and is usable in tests
- [ ] Developer runbook covers clone → migrate → serve → ingest → test
- [ ] End-to-end: clone, install, migrate, upload PDF, see it in /api/documents
