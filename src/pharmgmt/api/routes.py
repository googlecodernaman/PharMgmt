"""FastAPI routes for PharMgmt API."""

import os
import logging
import tempfile
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from pharmgmt import __version__
from pharmgmt.api.dependencies import get_db
from pharmgmt.api.schemas import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    HealthResponse,
    ParseResultMeta,
    ParseResultResponse,
    ParseResultRow,
)
from pharmgmt.config import get_settings
from pharmgmt.db import check_schema_version
from pharmgmt.models import Document, LineItem
from pharmgmt.services.ingestion import ingest_pdf

logger = logging.getLogger("pharmgmt.api")
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    settings = get_settings()
    try:
        sv = check_schema_version(settings.DATABASE_URL)
    except Exception:
        sv = 0
    return HealthResponse(
        status="ok",
        version=__version__,
        schema_version=sv,
    )


@router.get("/api/documents", response_model=DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all ingested documents with pagination."""
    total = db.query(Document).count()
    docs = (
        db.query(Document)
        .order_by(Document.ingest_ts.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = []
    for doc in docs:
        li_count = db.query(LineItem).filter_by(document_id=doc.id).count()
        items.append(
            DocumentResponse(
                id=doc.id,
                file_name=doc.file_name,
                supplier_name=None,
                title=doc.title,
                report_from=doc.report_from,
                report_to=doc.report_to,
                ingest_ts=doc.ingest_ts,
                line_item_count=li_count,
            )
        )

    return DocumentListResponse(items=items, total=total)


@router.get("/api/documents/{doc_id}", response_model=DocumentDetailResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    """Get a single document with its line items."""
    doc = db.query(Document).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    line_items = db.query(LineItem).filter_by(document_id=doc_id).all()
    li_list = [
        {
            "id": li.id,
            "product_name_raw": li.product_name_raw,
            "packing": li.packing,
            "batch_no": li.batch_no,
            "expiry": li.expiry,
            "opening_qty": li.opening_qty,
            "closing_qty": li.closing_qty,
            "price_paise": li.price_paise,
            "parser_confidence": li.parser_confidence,
        }
        for li in line_items
    ]

    return DocumentDetailResponse(
        id=doc.id,
        file_name=doc.file_name,
        title=doc.title,
        report_from=doc.report_from,
        report_to=doc.report_to,
        ingest_ts=doc.ingest_ts,
        raw_text=doc.raw_text,
        is_scanned=bool(doc.is_scanned),
        parser_version=doc.parser_version,
        line_item_count=len(li_list),
        line_items=li_list,
    )


@router.post("/api/upload", response_model=ParseResultResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF file for ingestion."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Save uploaded file to temp location
    start_time = time.time()
    temp_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}.pdf")
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Ingest
        result = ingest_pdf(db, temp_path, file.filename)

        duration_ms = int((time.time() - start_time) * 1000)

        if result["status"] == "duplicate":
            raise HTTPException(status_code=409, detail=result["error"])

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])

        # Return stub parse result (actual parsing in Phase 2)
        return ParseResultResponse(
            document={
                "document_id": result["document_id"],
                "file_name": result["file_name"],
                "file_hash": result["file_hash"],
            },
            rows=[],  # No row parsing yet
            meta=ParseResultMeta(
                parser_version="0.1.0-stub",
                duration_ms=duration_ms,
                rows_parsed=0,
                rows_flagged=0,
                avg_confidence=0.0,
                error_flags=[],
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    finally:
        # Keep the uploaded file in UPLOAD_DIR (it's also stored as blob in DB)
        pass
