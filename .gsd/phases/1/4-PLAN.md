---
phase: 1
plan: 4
wave: 2
---

# Plan 1.4: Staging Pipeline & CLI Launcher

## Objective
Implement the staging pipeline (raw PDF storage → text extraction → staged rows) and CLI commands for ingestion and migration. This enables PDF upload and text extraction without full parsing, and provides command-line access for automation.

## Context
- .gsd/SPEC.md — Staging pipeline, Parser contract
- c:\PharMgmt\src\pharmgmt\models\staging.py — Staging models (from Plan 1.2)
- c:\PharMgmt\src\pharmgmt\db.py — Database functions (from Plan 1.2)

## Tasks

<task type="auto">
  <name>Implement staging pipeline service</name>
  <files>
    c:\PharMgmt\src\pharmgmt\services\__init__.py
    c:\PharMgmt\src\pharmgmt\services\ingestion.py
    c:\PharMgmt\src\pharmgmt\services\text_extraction.py
  </files>
  <action>
    Create `services/` package.

    Create `services/text_extraction.py`:
    - `extract_text_from_pdf(file_path: str) -> list[dict]`: Uses pdfplumber to extract text from each page. Returns list of {page: int, text: str, tables: list[list[list[str]]]}. Tables extracted via pdfplumber's `page.extract_tables()`.
    - Handle errors gracefully: if a page fails, log warning and continue with next page
    - Return empty list if file is not a valid PDF

    Create `services/ingestion.py`:
    - `compute_file_hash(file_bytes: bytes) -> str`: SHA-256 hex digest
    - `ingest_pdf(db_session, file_path: str, file_name: str) -> dict`:
      1. Read file bytes, compute hash
      2. Check for duplicate via original_file_hash (return error if exists)
      3. Create Document record (id=uuid, file_name, original_file_hash, ingest_ts)
      4. Store raw bytes in RawFile
      5. Extract text using text_extraction.extract_text_from_pdf()
      6. Store extracted text in ExtractedText (one row per page)
      7. Return dict with document_id, pages_extracted, status
    - All operations in a single DB transaction (rollback on error)

    IMPORTANT:
    - File hash check BEFORE any storage to avoid partial writes
    - Log all operations to `pharmgmt.parsing` logger
    - Do NOT do row-level parsing yet (Phase 2) — just raw text + tables extraction
  </action>
  <verify>
    .venv\Scripts\python -c "from pharmgmt.services.ingestion import compute_file_hash; h = compute_file_hash(b'test'); print(f'Hash: {h[:16]}...'); assert len(h) == 64"
  </verify>
  <done>Ingestion service stores PDF, computes hash, extracts text per page, stores in staging tables</done>
</task>

<task type="auto">
  <name>Create CLI launcher with ingest and migrate commands</name>
  <files>
    c:\PharMgmt\src\pharmgmt\cli\__init__.py
    c:\PharMgmt\src\pharmgmt\cli\commands.py
  </files>
  <action>
    Create `cli/commands.py` using argparse (no external CLI framework dependency):
    - `main()` function as entry point
    - Subcommands:
      1. `migrate` — calls init_db() to create/update schema. Prints table count and schema version on success.
      2. `ingest <file_path>` — calls ingest_pdf() for a single PDF file. Prints document_id, pages extracted, and status. Errors shown clearly with file path.
      3. `serve` — starts uvicorn with the FastAPI app (host=0.0.0.0, port=8000, configurable)
      4. `version` — prints version and schema version (if DB exists)

    Update `cli/__init__.py`:
    - Export `main` function

    IMPORTANT:
    - All commands should set up logging first via setup_logging()
    - Commands that touch DB should ensure DB exists (auto-run init_db if needed)
    - Error messages should be user-friendly (not stack traces)
    - Exit codes: 0 for success, 1 for errors
  </action>
  <verify>
    .venv\Scripts\python -m pharmgmt.cli.commands version
    .venv\Scripts\python -m pharmgmt.cli.commands migrate
  </verify>
  <done>CLI has 4 subcommands working, migrate creates DB, ingest processes a PDF file</done>
</task>

## Success Criteria
- [ ] `python -m pharmgmt.cli.commands migrate` creates DB with all tables
- [ ] `python -m pharmgmt.cli.commands ingest <pdf>` stores file and extracts text
- [ ] Duplicate PDF upload detected and rejected via file hash
- [ ] Text extraction handles multi-page PDFs
- [ ] CLI prints user-friendly output and errors
