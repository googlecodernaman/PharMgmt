---
phase: 1
plan: 2
wave: 1
---

# Plan 1.2: Schema Design & SQLAlchemy Models

## Objective
Implement the canonical database schema as SQLAlchemy ORM models with all 8 canonical tables, 3 staging tables, schema_meta, indices, and migration infrastructure. This is the data backbone of the entire system.

## Context
- .gsd/SPEC.md — Canonical Schema section (SQL definition, indices, normalization rules)
- .gsd/DECISIONS.md — ADR-004 (paisa storage), ADR-005 (staging), ADR-006 (SHA-256 dedup)

## Tasks

<task type="auto">
  <name>Implement SQLAlchemy ORM models for all tables</name>
  <files>
    c:\PharMgmt\src\pharmgmt\models\base.py
    c:\PharMgmt\src\pharmgmt\models\document.py
    c:\PharMgmt\src\pharmgmt\models\supplier.py
    c:\PharMgmt\src\pharmgmt\models\product.py
    c:\PharMgmt\src\pharmgmt\models\batch.py
    c:\PharMgmt\src\pharmgmt\models\line_item.py
    c:\PharMgmt\src\pharmgmt\models\parsing_run.py
    c:\PharMgmt\src\pharmgmt\models\alert.py
    c:\PharMgmt\src\pharmgmt\models\payment.py
    c:\PharMgmt\src\pharmgmt\models\staging.py
    c:\PharMgmt\src\pharmgmt\models\__init__.py
  </files>
  <action>
    Create `base.py`:
    - Define `Base = declarative_base()`
    - Define `engine_factory(db_url)` that creates SQLite engine with WAL mode pragma
    - Define `session_factory(engine)` returning sessionmaker

    Create one model file per canonical table matching SPEC.md SQL schema exactly:
    - `document.py`: Document model — id (UUID TEXT PK), file_name, original_file_hash (UNIQUE), supplier_id (FK), title, report_from, report_to, report_generated, raw_text, is_scanned (bool default False), parser_version, schema_version (int default 1), ingest_ts (datetime default utcnow)
    - `supplier.py`: Supplier model — id, name, address, gstin
    - `product.py`: Product model — id, normalized_name, raw_names (JSON TEXT), unit, primary_pack_size, drug_code, created_ts
    - `batch.py`: Batch model — id, product_id (FK), batch_no, expiry_normalized (DATE), expiry_precision (TEXT), mrp_paise (INTEGER)
    - `line_item.py`: LineItem model — id, document_id (FK), page, row_index, product_id (FK nullable), product_name_raw, packing, batch_no, expiry, opening_qty, receipt_qty, total_qty, issue_qty, breakage_qty, closing_qty, reorder_qty, near_expiry_qty, price_paise (INTEGER), parser_confidence (REAL), raw_row_text, source_coords (JSON TEXT)
    - `parsing_run.py`: ParsingRun model — id, document_id (FK), parser_version, duration_ms, rows_parsed, rows_flagged, error_flags (JSON TEXT), avg_confidence (REAL), needs_review (bool default False), run_ts
    - `alert.py`: Alert model — id, type, product_id (FK), batch_id (FK), due_date, is_dismissed (bool default False), created_ts
    - `payment.py`: Payment model — id, document_id (FK), status (default 'unpaid'), amount_paise, paid_amount_paise (default 0), paid_date, notes

    Create `staging.py` with 3 staging models:
    - RawFile — id, document_id (FK), file_blob (BLOB)
    - ExtractedText — id, document_id (FK), page, text_json (TEXT)
    - StagedRow — id, document_id (FK), page, row_index, raw_data (JSON TEXT), canonical_data (JSON TEXT), status (default 'pending'), reviewer_notes

    IMPORTANT:
    - Use UUID strings (via `uuid.uuid4().hex`) for all primary keys
    - All monetary fields are INTEGER (paisa) — NOT float
    - Use `Column(Text)` for JSON fields (SQLite doesn't have native JSON)
    - Define relationships using `relationship()` where appropriate
    - Add `__repr__` methods for debugging

    Update `models/__init__.py` to re-export all models.
  </action>
  <verify>
    .venv\Scripts\python -c "from pharmgmt.models import Document, Supplier, Product, Batch, LineItem, ParsingRun, Alert, Payment, RawFile, ExtractedText, StagedRow; print('All models imported OK')"
  </verify>
  <done>All 11 models importable, field types match SPEC.md, FK relationships defined</done>
</task>

<task type="auto">
  <name>Implement database initialization and migration</name>
  <files>
    c:\PharMgmt\src\pharmgmt\db.py
    c:\PharMgmt\src\pharmgmt\models\schema_meta.py
  </files>
  <action>
    Create `schema_meta.py`:
    - SchemaMeta model — key (TEXT PK), value (TEXT)

    Create `db.py` with:
    - `init_db(db_url)`: Creates all tables via `Base.metadata.create_all()`, inserts initial schema_version=1 into schema_meta, enables WAL mode
    - `get_db_session(db_url)`: Context manager yielding a session
    - `check_schema_version(session)`: Reads schema_version from schema_meta, returns int
    - `migrate_db(session, from_version, to_version)`: Placeholder for future migrations with version checks

    Create indices matching SPEC.md:
    - idx_documents_hash on documents(original_file_hash)
    - idx_line_items_product on line_items(product_id)
    - idx_line_items_document on line_items(document_id)
    - idx_batches_product_batch on batches(product_id, batch_no)
    - idx_batches_expiry on batches(expiry_normalized)
    - idx_products_name on products(normalized_name)
    - idx_alerts_due on alerts(due_date)
    - idx_alerts_type on alerts(type, is_dismissed)
    - idx_staged_rows_status on staged_rows(status)

    Define indices using SQLAlchemy `Index()` objects in the model files or in db.py.
  </action>
  <verify>
    .venv\Scripts\python -c "from pharmgmt.db import init_db; init_db('sqlite:///test_schema.db'); print('DB created OK')"
    .venv\Scripts\python -c "import sqlite3; conn = sqlite3.connect('test_schema.db'); tables = [r[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()]; print(tables); assert len(tables) >= 12, f'Expected 12+ tables, got {len(tables)}'"
  </verify>
  <done>init_db creates all 12 tables + schema_meta with correct indices, WAL mode enabled</done>
</task>

<task type="auto">
  <name>Create schema freeze document</name>
  <files>
    c:\PharMgmt\docs\schema.md
  </files>
  <action>
    Create `docs/schema.md` documenting:
    - All tables with field names, types, nullability, defaults
    - All indices with column lists
    - FK relationships diagram (mermaid or text)
    - Data normalization rules (from SPEC.md)
    - Parser contract JSON format (from SPEC.md)
    - Schema version: 1
    - This is the canonical reference — any schema change must update this doc

    This is the "schema freeze" deliverable. It lives in `docs/` so it's versioned with code.
  </action>
  <verify>
    Test-Path "c:\PharMgmt\docs\schema.md"
  </verify>
  <done>Schema freeze document committed with complete field definitions and normalization rules</done>
</task>

## Success Criteria
- [ ] All 11 ORM models + SchemaMeta importable
- [ ] init_db creates all tables with correct columns and indices
- [ ] WAL mode enabled on SQLite
- [ ] Schema version tracked in schema_meta
- [ ] docs/schema.md committed as schema freeze
