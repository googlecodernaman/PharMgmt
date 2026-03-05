"""Ingestion service — PDF upload, dedup, text extraction, staging."""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from pharmgmt.models import Document, RawFile, ExtractedText
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
    """Ingest a PDF file into the staging pipeline.

    Steps:
    1. Read file, compute hash
    2. Check for duplicate
    3. Create Document record
    4. Store raw bytes in RawFile
    5. Extract text using pdfplumber
    6. Store extracted text per page

    Args:
        session: SQLAlchemy session
        file_path: Path to the PDF file on disk
        file_name: Original filename

    Returns:
        Dict with document_id, pages_extracted, status, or error
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

    session.flush()

    logger.info(
        "Ingested %s → doc %s (%d pages)",
        file_name, doc_id[:8], len(pages),
    )

    return {
        "status": "success",
        "document_id": doc_id,
        "file_name": file_name,
        "pages_extracted": len(pages),
        "file_hash": file_hash,
    }
