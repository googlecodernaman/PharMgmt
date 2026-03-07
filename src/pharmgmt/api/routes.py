"""FastAPI routes for PharMgmt API."""

import os
import logging
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
    """Upload a PDF file for ingestion and parsing."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    temp_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}.pdf")
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Ingest and parse
        result = ingest_pdf(db, temp_path, file.filename)

        if result["status"] == "duplicate":
            raise HTTPException(status_code=409, detail=result["error"])

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])

        # Return real parse result
        pr = result.get("parse_result", {})
        meta = pr.get("meta", {})

        rows = []
        for r in pr.get("rows", []):
            rows.append(ParseResultRow(
                page=r.get("page", 0),
                row_index=r.get("row_index", 0),
                raw_text=r.get("raw_text"),
                fields=r.get("fields", {}),
                confidence=r.get("confidence", 0.0),
                warnings=r.get("warnings", []),
            ))

        return ParseResultResponse(
            document={
                "document_id": result["document_id"],
                "file_name": result["file_name"],
                "file_hash": result["file_hash"],
                **(pr.get("document", {})),
            },
            rows=rows,
            meta=ParseResultMeta(
                parser_version=meta.get("parser_version", "0.2.0"),
                duration_ms=meta.get("duration_ms", 0),
                rows_parsed=meta.get("rows_parsed", 0),
                rows_flagged=meta.get("rows_flagged", 0),
                avg_confidence=meta.get("avg_confidence", 0.0),
                error_flags=meta.get("error_flags", []),
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
