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

- OCR / scanned image processing (PDFs have extractable text/tables)
- Cloud hosting or SaaS deployment
- Multi-location data sync (each location runs independently)
- Integration with POS or accounting software (v1)
- Mobile app
- Real-time collaboration between users

## Users

**Primary**: Pharmacy store staff and owners operating independent retail pharmacies in India. Users range from moderately tech-savvy to basic computer literacy. They currently use a mix of manual registers and basic software for bill tracking.

**Usage pattern**: 10–20 bills ingested per day from multiple distributors covering daily supply replenishment, emergency restocking, and category-specific suppliers.

## Canonical Schema

### Document-Level

```json
{
  "document_id": "uuid",
  "supplier_name": "string",
  "supplier_address": "string|null",
  "supplier_gstin": "string|null",
  "report_title": "string",
  "report_date_from": "YYYY-MM-DD|null",
  "report_date_to": "YYYY-MM-DD|null",
  "report_generated_date": "YYYY-MM-DD|null",
  "page_number": "int",
  "source_file": "string",
  "ingestion_timestamp": "ISO-8601"
}
```

### Line-Item (Product-Level)

```json
{
  "product_name": "string",
  "packing": "string|null",
  "pack_units": "int|null",
  "batch": "string|null",
  "expiry": "YYYY-MM-DD|null",
  "opening_qty": "int|null",
  "receipt_qty": "int|null",
  "total_qty": "int|null",
  "issue_qty": "int|null",
  "breakage_qty": "int|null",
  "closing_qty": "int|null",
  "reorder_qty": "int|null",
  "near_expiry_qty": "int|null",
  "mrp": "float|null",
  "currency": "INR|null",
  "notes": "string|null"
}
```

Columns found in each source file are mapped to canonical keys. Absent columns → `null`.

## Bill Types (Canonical Examples)

| Bill Type | Key Columns |
|-----------|-------------|
| Sales & Stock Statement | Product, Op Bal, Pur, Total, Sales, Cl Bal, repeated product tables |
| Batch-wise Stock Report | Pack, Batch, Expiry, Stock, MRP, Distributor |
| Stock & Sales Analysis | Opening, Purchases, Sales, Closing |
| Short Sales & Stock Statement | Op Bal, Pur, Total, Sales, Cl Bal, CP |

## Constraints

- **Offline-first**: Core functionality works without internet; internet optional for updates/data transfer
- **Low-end hardware**: Must run on budget Windows laptops (4GB RAM, HDD acceptable)
- **No paid APIs**: Zero cost for LLMs, cloud services, or GPU compute
- **No OCR**: All PDFs have extractable text and tables
- **Single instance per location**: No multi-tenant architecture needed
- **Python stack**: Backend in Python, SQLite for storage, local web UI

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+ with FastAPI |
| Database | SQLite |
| PDF Parsing | pdfplumber (primary), camelot-py (fallback) |
| Frontend | Local web app (HTML/CSS/JS served by FastAPI) |
| Packaging | Single-script launcher or PyInstaller for distribution |

## Success Criteria

- [ ] Can ingest 3+ different PDF bill formats and extract data correctly
- [ ] Canonical schema populated with ≥90% field accuracy from supported formats
- [ ] Dashboard loads in <3 seconds on a 4GB RAM Windows machine
- [ ] User can search, filter, and view all ingested bills
- [ ] Expiry alerts surface products expiring within 30/60/90 days
- [ ] Supplier price comparison works across ingested bills
- [ ] Payment status tracking per bill
- [ ] Runs fully offline after initial setup
