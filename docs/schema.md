# Schema Freeze — v1

> **Status**: Frozen | **Version**: 1 | **Date**: 2026-03-05

## Tables

### Canonical (8)

| Table | PK | Key Columns | Notes |
|-------|-----|-------------|-------|
| `documents` | id (UUID) | file_name, original_file_hash (UNIQUE), supplier_id (FK→suppliers), ingest_ts | One per uploaded PDF |
| `suppliers` | id (UUID) | name, address, gstin | Normalized vendor records |
| `products` | id (UUID) | normalized_name, raw_names (JSON), unit, primary_pack_size, drug_code | Product catalog |
| `batches` | id (UUID) | product_id (FK→products), batch_no, expiry_normalized, expiry_precision, mrp_paise | Batch-level records |
| `line_items` | id (UUID) | document_id (FK→documents), product_id (FK→products), product_name_raw, batch_no, all qty fields, price_paise, parser_confidence | One row per product/batch on bill |
| `parsing_runs` | id (UUID) | document_id (FK→documents), parser_version, duration_ms, rows_parsed, rows_flagged, avg_confidence, needs_review | Parse metadata |
| `alerts` | id (UUID) | type, product_id, batch_id, due_date, is_dismissed | Expiry/stock alerts |
| `payments` | id (UUID) | document_id (FK→documents), status, amount_paise, paid_amount_paise, paid_date | Payment tracking |

### Staging (3)

| Table | PK | Key Columns | Notes |
|-------|-----|-------------|-------|
| `raw_files` | id (UUID) | document_id (FK→documents), file_blob (BLOB) | Binary PDF storage |
| `extracted_text` | id (UUID) | document_id (FK→documents), page, text_json | Raw text per page |
| `staged_rows` | id (UUID) | document_id (FK→documents), raw_data (JSON), canonical_data (JSON), status | QA pipeline |

### Meta (1)

| Table | PK | Key Columns |
|-------|-----|-------------|
| `schema_meta` | key (TEXT) | value | KV store for schema_version |

## Indices

| Index | Table | Columns |
|-------|-------|---------|
| idx_documents_hash | documents | original_file_hash |
| idx_line_items_product | line_items | product_id |
| idx_line_items_document | line_items | document_id |
| idx_batches_product_batch | batches | product_id, batch_no |
| idx_batches_expiry | batches | expiry_normalized |
| idx_products_name | products | normalized_name |
| idx_alerts_due | alerts | due_date |
| idx_alerts_type | alerts | type, is_dismissed |
| idx_staged_rows_status | staged_rows | status |

## Data Normalization

| Data | Rule |
|------|------|
| Dates | ISO `YYYY-MM-DD`. Store `expiry_precision` (day/month/year) |
| Money | Integer paisa (₹1.00 = 100). Column suffix: `_paise` |
| Quantities | Integer for counts |
| Text | raw + normalized separately. Normalized = lowercase, unicode-normalized |
| Hashes | SHA-256 hex of raw PDF bytes |

## Parser Contract

See [SPEC.md](../../.gsd/SPEC.md#parser-contract-parse_result-json) for the `parse_result` JSON format.

---

*Any schema change MUST update this document and increment schema_version.*
