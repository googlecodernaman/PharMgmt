---
phase: 2
plan: 4
wave: 2
---

# Plan 2.4: Wire Parser into Ingestion Pipeline & API

## Objective
Connect the parser to the existing ingestion service so uploaded PDFs are fully parsed and stored in both staging and canonical tables. Update the upload API to return real parse results.

## Context
- c:\PharMgmt\src\pharmgmt\services\ingestion.py — Existing ingestion service
- c:\PharMgmt\src\pharmgmt\parsing\table_parser.py — Parser with confidence (from Plans 2.2-2.3)
- c:\PharMgmt\src\pharmgmt\api\routes.py — Upload endpoint
- c:\PharMgmt\src\pharmgmt\models\ — All DB models

## Tasks

<task type="auto">
  <name>Update ingestion service to run parser and store results</name>
  <files>
    c:\PharMgmt\src\pharmgmt\services\ingestion.py
  </files>
  <action>
    Update `ingest_pdf()` to add parsing after text extraction:

    After step 6 (store extracted text), add:
    7. Call `parse_tables(pages)` to get parse_result
    8. Update Document record with metadata from parse_result (title, supplier, dates)
    9. Create StagedRow records for each parsed row:
       - raw_data = JSON of original row values
       - canonical_data = JSON of canonical field dict
       - status = 'pending'
    10. Create LineItem records from canonical rows (for documents with avg_confidence >= 0.75)
        For documents below threshold, only create StagedRows (not LineItems)
    11. Create ParsingRun record with all metrics
    12. Return full parse_result dict

    IMPORTANT:
    - If parsing fails, still keep the document (text was extracted successfully)
    - Log parse_result summary at INFO level
    - Set document.parser_version from parser meta
    - All in one transaction
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.services.ingestion import ingest_pdf; print('Updated ingestion imports OK')"
  </verify>
  <done>Ingestion pipeline runs full parse, stores results in staging + canonical tables</done>
</task>

<task type="auto">
  <name>Update upload API to return real parse results</name>
  <files>
    c:\PharMgmt\src\pharmgmt\api\routes.py
  </files>
  <action>
    Update `POST /api/upload`:
    - Instead of returning stub parse_result, return the real result from ingest_pdf()
    - The response should now contain actual rows, confidence scores, warnings

    Add new endpoint `GET /api/documents/{id}/parsing`:
    - Returns the ParsingRun records for a document
    - Includes rows_parsed, rows_flagged, avg_confidence, error_flags, needs_review

    Add new endpoint `GET /api/documents/{id}/staged`:
    - Returns staged rows for a document with their status
    - Used by the future staging review UI (Phase 3)
  </action>
  <verify>
    cd c:\PharMgmt && .venv\Scripts\python -c "from pharmgmt.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path')]; print(f'Routes: {routes}')"
  </verify>
  <done>Upload returns real parse results, new parsing/staged endpoints work</done>
</task>

## Success Criteria
- [ ] Uploading a PDF runs full parse pipeline end-to-end
- [ ] StagedRows created for all parsed rows
- [ ] LineItems created only for high-confidence documents
- [ ] ParsingRun record stores all metrics
- [ ] API returns real parse results with confidence/warnings
