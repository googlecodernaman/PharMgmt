# SPEC.md — Project Specification

> **Status**: `FINALIZED`

## Vision

PharMgmt is an offline-first pharmacy bill management system that ingests supplier PDF bills in varying formats, extracts structured data from their tables, and maps everything to a canonical schema. It provides pharmacy staff with a centralized web dashboard to track inventory movements, compare supplier pricing, monitor expiry dates, and manage payments — all running locally on low-end Windows machines with zero cloud dependency.

## Goals

1. **PDF Table Extraction** — Parse supplier PDF bills (sales & stock statements, batch-wise reports, short stock statements) and extract tabular data reliably across different layouts
2. **Canonical Schema Mapping** — Normalize extracted data from diverse bill formats into a unified document + line-item schema
3. **Centralized Dashboard** — Provide a local web UI for viewing, searching, filtering, and managing all ingested bills and inventory data
4. **Supplier & Pricing Intelligence** — Compare prices across suppliers, track purchase patterns, surface best deals
5. **Expiry & Inventory Monitoring** — Alert on near-expiry stock, track opening/closing balances, reconcile inventory
6. **Payment Tracking** — Track paid/unpaid bills, payment status per supplier
7. **Reporting** — Generate purchase reports, stock summaries, supplier analytics

## Non-Goals (Out of Scope)

- Cloud hosting or SaaS deployment
- Multi-location data sync (each location runs independently)
- Integration with POS or accounting software (v1)
- Mobile app
- Real-time collaboration between users

## Users

**Primary**: Pharmacy store staff and owners operating independent retail pharmacies in India. Users range from moderately tech-savvy to basic computer literacy. They currently use a mix of manual registers and basic software for bill tracking.

**Usage pattern**: 10–20 bills ingested per day from multiple distributors covering daily supply replenishment, emergency restocking, and category-specific suppliers.

---

## Canonical Schema

### Top-Level Objects

| Table | Purpose |
|-------|---------|
| `documents` | Metadata for each uploaded PDF |
| `suppliers` | Normalized supplier/vendor records |
| `products` | Normalized product catalog (name variants, normalized_name) |
| `line_items` | Invoice rows — one per product/batch on the bill |
| `batches` | Batch-level records (product, batch_no, expiry, mrp) |
| `parsing_runs` | Ingestion metadata (parser_version, confidence, errors) |
| `alerts` | Expiry and stock alerts |
| `payments` | Status per document (paid/unpaid/partial) |

### Staging Pipeline

| Table | Purpose |
|-------|---------|
| `raw_files` | Binary PDF storage |
| `extracted_text` | Raw text JSON per page |
| `staged_rows` | Pre-canonical rows for QA review |

Staging allows re-parsing without overwriting canonical data.

### SQL Schema

```sql
-- Core tables

CREATE TABLE documents (
  id TEXT PRIMARY KEY,
  file_name TEXT NOT NULL,
  original_file_hash TEXT UNIQUE,
  supplier_id TEXT NULL REFERENCES suppliers(id),
  title TEXT,
  report_from DATE,
  report_to DATE,
  report_generated DATE,
  raw_text TEXT,
  is_scanned INTEGER DEFAULT 0,
  parser_version TEXT,
  schema_version INTEGER DEFAULT 1,
  ingest_ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE suppliers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT,
  gstin TEXT
);

CREATE TABLE products (
  id TEXT PRIMARY KEY,
  normalized_name TEXT NOT NULL,
  raw_names TEXT,            -- JSON array of aliases
  unit TEXT,                 -- strip/pack/ML etc
  primary_pack_size INTEGER,
  drug_code TEXT,            -- nullable SKU
  created_ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE batches (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL REFERENCES products(id),
  batch_no TEXT NOT NULL,
  expiry_normalized DATE,
  expiry_precision TEXT,     -- 'day' | 'month' | 'year'
  mrp_paise INTEGER         -- price in paisa (avoids float rounding)
);

CREATE TABLE line_items (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id),
  page INTEGER,
  row_index INTEGER,
  product_id TEXT NULL REFERENCES products(id),
  product_name_raw TEXT,
  packing TEXT,
  batch_no TEXT,
  expiry TEXT,
  opening_qty INTEGER,
  receipt_qty INTEGER,
  total_qty INTEGER,
  issue_qty INTEGER,
  breakage_qty INTEGER,
  closing_qty INTEGER,
  reorder_qty INTEGER,
  near_expiry_qty INTEGER,
  price_paise INTEGER,
  parser_confidence REAL,    -- 0.0–1.0
  raw_row_text TEXT,
  source_coords TEXT         -- JSON: {x1, y1, x2, y2} when available
);

CREATE TABLE parsing_runs (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id),
  parser_version TEXT,
  duration_ms INTEGER,
  rows_parsed INTEGER,
  rows_flagged INTEGER,
  error_flags TEXT,          -- JSON: e.g. ["missing_totals", "negative_qty"]
  avg_confidence REAL,
  needs_review INTEGER DEFAULT 0,
  run_ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alerts (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,        -- 'expiry_30d' | 'expiry_60d' | 'expiry_90d' | 'low_stock'
  product_id TEXT REFERENCES products(id),
  batch_id TEXT REFERENCES batches(id),
  due_date DATE,
  is_dismissed INTEGER DEFAULT 0,
  created_ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payments (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id),
  status TEXT DEFAULT 'unpaid', -- 'paid' | 'unpaid' | 'partial'
  amount_paise INTEGER,
  paid_amount_paise INTEGER DEFAULT 0,
  paid_date DATE,
  notes TEXT
);

-- Staging tables

CREATE TABLE raw_files (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id),
  file_blob BLOB
);

CREATE TABLE extracted_text (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id),
  page INTEGER,
  text_json TEXT             -- raw extracted text as JSON
);

CREATE TABLE staged_rows (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id),
  page INTEGER,
  row_index INTEGER,
  raw_data TEXT,             -- JSON of raw extracted row
  canonical_data TEXT,       -- JSON mapped to canonical fields
  status TEXT DEFAULT 'pending', -- 'pending' | 'accepted' | 'rejected' | 'corrected'
  reviewer_notes TEXT
);

-- Schema versioning
CREATE TABLE schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT
);
INSERT INTO schema_meta(key, value) VALUES ('schema_version', '1');

-- Indices
CREATE INDEX idx_documents_hash ON documents(original_file_hash);
CREATE INDEX idx_line_items_product ON line_items(product_id);
CREATE INDEX idx_line_items_document ON line_items(document_id);
CREATE INDEX idx_batches_product_batch ON batches(product_id, batch_no);
CREATE INDEX idx_batches_expiry ON batches(expiry_normalized);
CREATE INDEX idx_products_name ON products(normalized_name);
CREATE INDEX idx_alerts_due ON alerts(due_date);
CREATE INDEX idx_alerts_type ON alerts(type, is_dismissed);
CREATE INDEX idx_staged_rows_status ON staged_rows(status);
```

### Data Type & Normalization Rules

| Data | Rule |
|------|------|
| **Dates** | ISO `YYYY-MM-DD`. Store `expiry_precision` (day/month/year) where full date unavailable |
| **Money** | Integer paisa (₹1.00 = 100 paise) — avoids float rounding |
| **Quantities** | Integer for count-based units; decimal only for fractional units |
| **Text** | Store raw text AND normalized text separately. Normalized = lowercased, unicode-normalized, punctuation-trimmed |
| **Hashes** | SHA-256 of raw PDF file bytes for deduplication |

### Parser Contract (`parse_result` JSON)

```json
{
  "document": {
    "file_name": "string",
    "file_hash": "sha256",
    "supplier_name": "string|null",
    "supplier_gstin": "string|null",
    "report_title": "string|null",
    "report_from": "YYYY-MM-DD|null",
    "report_to": "YYYY-MM-DD|null"
  },
  "rows": [
    {
      "page": 1,
      "row_index": 0,
      "raw_text": "string",
      "fields": { "...canonical field map..." },
      "confidence": 0.95,
      "warnings": ["missing_batch"]
    }
  ],
  "meta": {
    "parser_version": "string",
    "duration_ms": 1234,
    "rows_parsed": 50,
    "rows_flagged": 3,
    "avg_confidence": 0.91,
    "error_flags": []
  }
}
```

---

## Bill Types (Canonical Examples)

| Bill Type | Key Columns |
|-----------|-------------|
| Sales & Stock Statement | Product, Op Bal, Pur, Total, Sales, Cl Bal, repeated product tables |
| Batch-wise Stock Report | Pack, Batch, Expiry, Stock, MRP, Distributor |
| Stock & Sales Analysis | Opening, Purchases, Sales, Closing |
| Short Sales & Stock Statement | Op Bal, Pur, Total, Sales, Cl Bal, CP |

---

## Constraints

- **Offline-first**: Core functionality works without internet; internet optional for updates/data transfer
- **Low-end hardware**: Must run on budget Windows laptops (4GB RAM, HDD acceptable)
- **No paid APIs**: Zero cost for LLMs, cloud services, or GPU compute
- **OCR fallback**: Primary mode is text extraction. If text extraction fails or confidence is low, Tesseract OCR as fallback (max page width 1600px to limit CPU cost)
- **Single instance per location**: No multi-tenant architecture needed
- **Python stack**: Backend in Python, SQLite for storage, local web UI

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+ with FastAPI |
| Database | SQLite (with WAL mode for concurrent reads) |
| PDF Parsing | pdfplumber (primary), camelot-py (fallback) |
| OCR Fallback | Tesseract (optional, for scanned PDFs) |
| Frontend | Local web app (HTML/CSS/JS served by FastAPI) |
| ORM | SQLAlchemy (lightweight) |
| Packaging | Single-script launcher or PyInstaller for distribution |

---

## Acceptance Criteria

### Phase 1 → Phase 2 Handoff

- [ ] Can clone repo, run migrations, upload a PDF, see it recorded in `documents` with raw text stored
- [ ] Schema freeze document committed with field definitions, types, nullability, and indices
- [ ] Parser contract JSON defined and committed
- [ ] Staging pipeline operational (raw → extracted → staged_rows)
- [ ] Schema versioning with `schema_version` table and migration script

### Phase 2 Parsing Accuracy

- [ ] **Unit tests**: parser functions (date normalization, numeric normalization, header mapping) with >80% coverage
- [ ] **Integration tests**: 3 canonical bill types × 10 sample PDFs; canonical JSON outputs compared with labeled gold data. Target: ≥90% field-level match (`matched_fields / total_fields`)
- [ ] **Performance**: average bill processed in 1–3s on target hardware (dual-core 2.0 GHz, 4–8 GB RAM) for text-based PDFs
- [ ] **Robustness**: system gracefully flags and records parsing failures without crashing
- [ ] **Human review threshold**: documents with `avg_confidence < 0.75` flagged for manual review

### Overall Success

- [ ] Dashboard loads in <3 seconds on a 4GB RAM Windows machine
- [ ] User can search, filter, and view all ingested bills
- [ ] Expiry alerts surface products expiring within 30/60/90 days
- [ ] Supplier price comparison works across ingested bills
- [ ] Payment status tracking per bill
- [ ] Runs fully offline after initial setup

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| OCR quality on scanned invoices | Reduced accuracy | Staged OCR + human review UI; text extraction primary |
| Supplier format drift | Parser breaks on new layouts | Supplier-specific mapping config; auto-detect versioning |
| Resource limits on low-end devices | Slow OCR processing | Default to text extraction; OCR only when necessary; allow manual fallback |
| Data correctness / arithmetic mismatches | Wrong inventory data | Automatic sanity checks (totals, negative qty) and flagging |
| Schema evolution | Breaking changes to stored data | `schema_version` table + migration scripts from Phase 1 |
