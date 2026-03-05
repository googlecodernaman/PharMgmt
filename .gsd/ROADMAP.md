# ROADMAP.md

> **Current Phase**: Not started
> **Milestone**: v1.0 — MVP

## Must-Haves (from SPEC)

- [ ] PDF table extraction from 3+ bill formats
- [ ] Canonical schema mapping with ≥90% accuracy
- [ ] Local web dashboard with search/filter
- [ ] Expiry date monitoring with alerts
- [ ] Supplier price comparison
- [ ] Payment status tracking
- [ ] Offline operation on 4GB RAM Windows machines

## Phases

### Phase 1: Foundation & Data Layer
**Status**: ⬜ Not Started
**Objective**: Set up Python project structure, SQLite database with canonical schema, and FastAPI skeleton
**Deliverables**:
- Project scaffolding (src layout, dependencies, config)
- SQLite database models matching canonical document + line-item schema
- FastAPI app with health check endpoint
- Database migration/init script
- Basic CLI launcher

---

### Phase 2: PDF Parsing Engine
**Status**: ⬜ Not Started
**Objective**: Build the PDF ingestion pipeline that extracts tables from supplier bills and maps columns to the canonical schema
**Deliverables**:
- PDF table extraction using pdfplumber (primary)
- Column-mapping rules engine (maps diverse column headers → canonical fields)
- Support for 3 canonical bill types: Sales & Stock Statement, Batch-wise Stock Report, Short Sales & Stock Statement
- Ingestion API endpoint (upload PDF → parse → store)
- Parsing confidence/quality reporting
**Dependencies**: Phase 1

---

### Phase 3: Dashboard & Core UI
**Status**: ⬜ Not Started
**Objective**: Build the local web interface for viewing, searching, and managing ingested bills and inventory data
**Deliverables**:
- Dashboard home (recent bills, key stats, alerts)
- Bill list view with search, filter, sort
- Bill detail view (document metadata + line items table)
- Product/inventory view (aggregated across bills)
- Responsive design for varying screen sizes
- File upload UI for PDF ingestion
**Dependencies**: Phase 1, Phase 2

---

### Phase 4: Intelligence & Reporting
**Status**: ⬜ Not Started
**Objective**: Add supplier analytics, expiry monitoring, payment tracking, and report generation
**Deliverables**:
- Expiry alert system (30/60/90 day warnings)
- Supplier price comparison across bills
- Payment status tracking (paid/unpaid/partial per bill)
- Purchase reports and stock summaries
- Export to CSV / print-friendly views
**Dependencies**: Phase 3

---

### Phase 5: Polish & Distribution
**Status**: ⬜ Not Started
**Objective**: Performance optimization, error handling, packaging for easy distribution
**Deliverables**:
- Performance tuning for low-end hardware (lazy loading, query optimization)
- Graceful error handling for malformed PDFs
- User onboarding / first-run experience
- PyInstaller packaging (single executable or simple installer)
- User documentation
**Dependencies**: Phase 4
