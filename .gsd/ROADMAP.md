# ROADMAP.md

> **Current Phase**: Not started
> **Milestone**: v1.0 — MVP

## Must-Haves (from SPEC)

- [ ] PDF table extraction from 3+ bill formats
- [ ] Canonical schema mapping with ≥90% field-level accuracy
- [ ] Staging/QA pipeline (raw → extracted → staged → canonical)
- [ ] Local web dashboard with search/filter
- [ ] Expiry date monitoring with alerts (30/60/90d)
- [ ] Supplier price comparison
- [ ] Payment status tracking
- [ ] Offline operation on 4GB RAM Windows machines

## Phases

### Phase 1: Foundation & Data Layer
**Status**: ⬜ Not Started
**Objective**: Project scaffolding, canonical schema implementation, staging pipeline, FastAPI skeleton, and parser contract definition

**Deliverables**:
1. **Repo scaffold** — src layout, license, README, code style rules, `.gitignore`
2. **Schema freeze document** — `SPEC/schema.md` with field definitions, types, nullability, indices
3. **SQLite DB + ORM models** — SQLAlchemy models for all 8 canonical tables + 3 staging tables + `schema_meta`
4. **Indices** — All performance indices from SPEC
5. **Staging pipeline** — `raw_files` (binary PDF) + `extracted_text` (raw text JSON) + `staged_rows` (QA)
6. **Parser contract** — `parse_result` JSON contract committed to repo (used for API responses and testing)
7. **Migration/versioning** — `schema_version` integer in DB, migration script, `migrate` CLI command
8. **FastAPI skeleton** — `/health`, stub upload endpoint returning `parse_result` contract, `/documents` GET
9. **CLI launcher** — `ingest` subcommand (stores PDF in `raw_files`, extracts text), `migrate` command
10. **Logging** — Parser error details and counts written to disk (not stdout)
11. **Tests** — Unit tests for normalizers; integration test: 3 example PDFs → extraction pipeline
12. **Developer runbook** — Local setup instructions

**Acceptance**: Dev can clone repo, run migrations, upload a PDF, and see it recorded in `documents` with raw text stored.

---

### Phase 2: PDF Parsing Engine
**Status**: ⬜ Not Started
**Objective**: Build the PDF ingestion pipeline that extracts tables, maps columns to canonical schema, and reports parsing confidence

**Deliverables**:
1. PDF table extraction using pdfplumber (primary), camelot-py (fallback)
2. Column-mapping rules engine (maps diverse column headers → canonical fields)
3. Supplier-specific mapping configs (YAML/JSON) with auto-detect versioning
4. Support for 3 canonical bill types: Sales & Stock Statement, Batch-wise Stock Report, Short Sales & Stock Statement
5. Ingestion API endpoint (upload PDF → parse → store in canonical + staging)
6. Parsing confidence aggregation: per-document weighted `avg_confidence`, per-row confidence
7. Human review flag: `avg_confidence < 0.75` → `needs_review = 1`
8. Parsing metrics: `rows_parsed`, `rows_flagged`, `avg_confidence`, `parse_duration_ms`
9. Automatic sanity checks: totals consistency, negative qty detection, arithmetic mismatches
10. OCR fallback: Tesseract when text extraction fails or confidence low (`max_page_width=1600px`)

**Acceptance**:
- Unit tests for date/numeric normalization, header mapping — >80% coverage
- Integration tests: 10 labeled sample PDFs × 3 bill types; ≥90% field-level match vs gold data
- Average bill processed in 1–3s on target hardware (text-based)
- Parsing failures flagged and recorded without crashing

**Dependencies**: Phase 1

---

### Phase 3: Dashboard & Core UI
**Status**: ⬜ Not Started
**Objective**: Build the local web interface for viewing, searching, managing ingested bills, and reviewing flagged documents

**Deliverables**:
1. Dashboard home (recent bills, key stats, active alerts)
2. Bill list view with search, filter, sort
3. Bill detail view (document metadata + line items table)
4. Product/inventory view (aggregated across bills)
5. **Staging review UI** — flagged documents with raw text side-by-side with parsed rows; accept/override/reject controls
6. File upload UI for PDF ingestion (drag & drop)
7. CSV import/export for corrections (feeds back into parser improvement)
8. Responsive design for varying screen sizes

**Dependencies**: Phase 1, Phase 2

---

### Phase 4: Intelligence & Reporting
**Status**: ⬜ Not Started
**Objective**: Add supplier analytics, expiry monitoring, payment tracking, and report generation

**Deliverables**:
1. Expiry alert system (30/60/90 day warnings)
2. Supplier price comparison across bills
3. Payment status tracking (paid/unpaid/partial per bill)
4. Purchase reports and stock summaries
5. Export to CSV / print-friendly views
6. Automatic sanity reports (flagged mismatches)

**Dependencies**: Phase 3

---

### Phase 5: Polish & Distribution
**Status**: ⬜ Not Started
**Objective**: Performance optimization, error handling, security, backup, and packaging

**Deliverables**:
1. Performance tuning for low-end hardware (lazy loading, query optimization, SQLite WAL)
2. Graceful error handling for malformed PDFs
3. User onboarding / first-run experience
4. **Local backup/export** — manual or scheduled export of DB and raw files
5. **Retention policy** — configurable retention for raw PDFs and OCR data
6. PyInstaller packaging (single executable or simple installer)
7. User documentation

**Dependencies**: Phase 4
