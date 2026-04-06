"""Ingestion service — PDF upload, dedup, text extraction, parsing, staging."""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from pharmgmt.models import (
    Document, RawFile, ExtractedText, StagedRow, LineItem, ParsingRun,
)
from pharmgmt.parsing.table_parser import parse_tables
from pharmgmt.services.text_extraction import extract_text_from_pdf

logger = logging.getLogger("pharmgmt.parsing")


def compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file bytes.

    Args:
        file_bytes: Raw file content

    Returns:
        64-character hex digest string
    """
    return hashlib.sha256(file_bytes).hexdigest()


def ingest_pdf(session: Session, file_path: str, file_name: str) -> dict:
    """Ingest a PDF file: extract text, parse tables, store results.

    Args:
        session: SQLAlchemy session
        file_path: Path to the PDF file on disk
        file_name: Original filename

    Returns:
        Dict with document_id, parse_result, status, or error
    """
    # 1. Read file and compute hash
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        logger.error("Failed to read file %s: %s", file_path, e)
        return {"status": "error", "error": f"Cannot read file: {e}"}

    file_hash = compute_file_hash(file_bytes)

    # 2. Check for duplicate
    existing = session.query(Document).filter_by(original_file_hash=file_hash).first()
    if existing:
        logger.info("Duplicate file detected: %s (matches doc %s)", file_name, existing.id)
        return {
            "status": "duplicate",
            "error": f"File already ingested as document {existing.id}",
            "existing_document_id": existing.id,
        }

    # 3. Create Document record
    doc_id = uuid.uuid4().hex
    doc = Document(
        id=doc_id,
        file_name=file_name,
        original_file_hash=file_hash,
        ingest_ts=datetime.now(timezone.utc),
    )
    session.add(doc)

    # 4. Store raw bytes
    raw_file = RawFile(
        id=uuid.uuid4().hex,
        document_id=doc_id,
        file_blob=file_bytes,
    )
    session.add(raw_file)

    # 5. Extract text
    pages = extract_text_from_pdf(file_path)

    # 6. Store extracted text per page
    for page_data in pages:
        ext_text = ExtractedText(
            id=uuid.uuid4().hex,
            document_id=doc_id,
            page=page_data["page"],
            text_json=json.dumps(page_data),
        )
        session.add(ext_text)

    # Concatenate all page text into document raw_text
    doc.raw_text = "\n\n".join(p.get("text", "") for p in pages)

    # 7. Parse tables
    parse_result = parse_tables(pages)

    # 8. Update document metadata from parse result
    doc_meta = parse_result.get("document", {})
    if doc_meta.get("report_title"):
        doc.title = doc_meta.get("report_title")
    if doc_meta.get("report_date_from"):
        doc.report_from = doc_meta["report_date_from"]
    if doc_meta.get("report_date_to"):
        doc.report_to = doc_meta["report_date_to"]

    meta = parse_result.get("meta", {})
    doc.parser_version = meta.get("parser_version", "0.2.0")

    # 9. Create StagedRows for all parsed rows (include confidence + warnings for reviewer)
    for row in parse_result.get("rows", []):
        staged = StagedRow(
            id=uuid.uuid4().hex,
            document_id=doc_id,
            page=row.get("page"),
            row_index=row.get("row_index"),
            raw_data=json.dumps({
                "raw_text": row.get("raw_text", ""),
                "confidence": row.get("confidence", 0.0),
                "warnings": row.get("warnings", []),
            }),
            canonical_data=json.dumps(row.get("fields", {})),
            status="pending",
        )
        session.add(staged)

    # 10. Create LineItems for high-confidence documents
    avg_confidence = meta.get("avg_confidence", 0.0)
    if avg_confidence >= 0.75:
        for row in parse_result.get("rows", []):
            fields = row.get("fields", {})
            li = LineItem(
                id=uuid.uuid4().hex,
                document_id=doc_id,
                page=row.get("page"),
                row_index=row.get("row_index"),
                product_name_raw=fields.get("product_name_raw"),
                packing=fields.get("packing"),
                batch_no=fields.get("batch_no"),
                expiry=fields.get("expiry"),
                opening_qty=fields.get("opening_qty"),
                receipt_qty=fields.get("receipt_qty"),
                total_qty=fields.get("total_qty"),
                issue_qty=fields.get("issue_qty"),
                closing_qty=fields.get("closing_qty"),
                near_expiry_qty=fields.get("near_expiry_qty"),
                price_paise=fields.get("price_paise"),
                parser_confidence=row.get("confidence"),
                raw_row_text=row.get("raw_text"),
            )
            session.add(li)

    # 11. Create ParsingRun record
    parsing_run = ParsingRun(
        id=uuid.uuid4().hex,
        document_id=doc_id,
        parser_version=meta.get("parser_version", "0.2.0"),
        duration_ms=meta.get("duration_ms"),
        rows_parsed=meta.get("rows_parsed", 0),
        rows_flagged=meta.get("rows_flagged", 0),
        error_flags=json.dumps(meta.get("error_flags", [])),
        avg_confidence=avg_confidence,
        needs_review=1 if meta.get("needs_review", True) else 0,
        bill_type=meta.get("bill_type"),
    )
    session.add(parsing_run)

    session.flush()

    logger.info(
        "Ingested %s -> doc %s (%d pages, %d rows, confidence %.2f)",
        file_name, doc_id[:8], len(pages),
        meta.get("rows_parsed", 0), avg_confidence,
    )

    return {
        "status": "success",
        "document_id": doc_id,
        "file_name": file_name,
        "file_hash": file_hash,
        "pages_extracted": len(pages),
        "parse_result": parse_result,
    }
