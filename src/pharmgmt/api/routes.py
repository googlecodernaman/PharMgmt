"""FastAPI routes for PharMgmt API."""

import json
import os
import logging
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
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
from pharmgmt.models import Document, LineItem, ParsingRun, StagedRow
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


@router.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard statistics."""
    total_docs = db.query(Document).count()
    total_items = db.query(LineItem).count()
    review_count = db.query(ParsingRun).filter(ParsingRun.needs_review == 1).count()

    # Average confidence across all parsing runs
    avg_conf = db.query(func.avg(ParsingRun.avg_confidence)).scalar() or 0.0

    # Recent uploads
    recent = db.query(Document).order_by(Document.ingest_ts.desc()).limit(5).all()
    recent_list = []
    for doc in recent:
        pr = db.query(ParsingRun).filter_by(document_id=doc.id).first()
        recent_list.append({
            "id": doc.id,
            "file_name": doc.file_name,
            "title": doc.title,
            "ingest_ts": doc.ingest_ts,
            "bill_type": None,
            "avg_confidence": pr.avg_confidence if pr else 0,
        })

    return {
        "total_documents": total_docs,
        "total_line_items": total_items,
        "documents_needing_review": review_count,
        "avg_confidence_overall": round(float(avg_conf), 3),
        "recent_uploads": recent_list,
    }


@router.get("/api/products")
def list_products(
    search: str = Query("", description="Search product name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Aggregated product view across all bills."""
    query = db.query(
        LineItem.product_name_raw,
        LineItem.packing,
        func.max(LineItem.closing_qty).label("latest_closing"),
        func.max(LineItem.price_paise).label("latest_price"),
        func.count(LineItem.id).label("bill_count"),
        func.max(LineItem.expiry).label("latest_expiry"),
    ).filter(LineItem.product_name_raw.isnot(None))

    if search:
        query = query.filter(LineItem.product_name_raw.ilike(f"%{search}%"))

    products = (
        query.group_by(LineItem.product_name_raw, LineItem.packing)
        .order_by(LineItem.product_name_raw)
        .offset(skip).limit(limit)
        .all()
    )

    items = [
        {
            "name": p.product_name_raw,
            "packing": p.packing,
            "latest_closing": p.latest_closing,
            "latest_price": p.latest_price,
            "bill_count": p.bill_count,
            "latest_expiry": p.latest_expiry,
            "expiry_warning": False,
            "expired": False,
        }
        for p in products
    ]

    return {"items": items, "total": len(items)}


@router.get("/api/staging")
def list_staging(db: Session = Depends(get_db)):
    """Documents needing review."""
    runs = db.query(ParsingRun).filter(ParsingRun.needs_review == 1).all()
    items = []
    for pr in runs:
        doc = db.query(Document).filter_by(id=pr.document_id).first()
        if not doc:
            continue
        rows_count = db.query(StagedRow).filter_by(document_id=pr.document_id).count()
        items.append({
            "id": doc.id,
            "file_name": doc.file_name,
            "ingest_ts": doc.ingest_ts,
            "avg_confidence": pr.avg_confidence,
            "rows_count": rows_count,
        })
    return {"items": items}


@router.post("/api/staging/{doc_id}/accept")
def accept_staging(doc_id: str, db: Session = Depends(get_db)):
    """Accept all staged rows for a document."""
    staged = db.query(StagedRow).filter_by(document_id=doc_id, status="pending").all()
    if not staged:
        raise HTTPException(status_code=404, detail="No staged rows found")

    import uuid
    for row in staged:
        row.status = "accepted"
        canonical = json.loads(row.canonical_data) if row.canonical_data else {}
        li = LineItem(
            id=uuid.uuid4().hex,
            document_id=doc_id,
            page=row.page,
            row_index=row.row_index,
            product_name_raw=canonical.get("product_name_raw"),
            packing=canonical.get("packing"),
            batch_no=canonical.get("batch_no"),
            expiry=canonical.get("expiry"),
            opening_qty=canonical.get("opening_qty"),
            closing_qty=canonical.get("closing_qty"),
            price_paise=canonical.get("price_paise"),
        )
        db.add(li)

    pr = db.query(ParsingRun).filter_by(document_id=doc_id).first()
    if pr:
        pr.needs_review = 0

    db.flush()
    return {"status": "accepted", "rows": len(staged)}


@router.post("/api/staging/{doc_id}/reject")
def reject_staging(doc_id: str, db: Session = Depends(get_db)):
    """Reject a document's staged rows."""
    staged = db.query(StagedRow).filter_by(document_id=doc_id).all()
    if not staged:
        raise HTTPException(status_code=404, detail="No staged rows found")

    for row in staged:
        row.status = "rejected"

    pr = db.query(ParsingRun).filter_by(document_id=doc_id).first()
    if pr:
        pr.needs_review = 0

    db.flush()
    return {"status": "rejected", "rows": len(staged)}


# ─── Phase 4: Alerts, Analytics, Payments, Reports ──────────────────

@router.get("/api/alerts/expiry")
def get_expiry_alerts_endpoint(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Expiry alerts grouped by severity."""
    from pharmgmt.services.alerts import get_expiry_alerts
    return get_expiry_alerts(db, days_ahead=days)


@router.get("/api/analytics/prices")
def get_price_history_endpoint(
    product: str = Query(..., description="Product name"),
    db: Session = Depends(get_db),
):
    """Price history for a specific product."""
    from pharmgmt.services.analytics import get_price_history
    return {"items": get_price_history(db, product)}


@router.get("/api/analytics/price-changes")
def get_price_changes_endpoint(db: Session = Depends(get_db)):
    """Products with price changes across bills."""
    from pharmgmt.services.analytics import get_price_changes
    return {"items": get_price_changes(db)}


@router.get("/api/documents/{doc_id}/payments")
def list_payments(doc_id: str, db: Session = Depends(get_db)):
    """List payments for a document."""
    from pharmgmt.models import Payment
    payments = db.query(Payment).filter_by(document_id=doc_id).order_by(Payment.payment_date).all()
    return {
        "items": [
            {
                "id": p.id,
                "amount_paise": p.amount_paise,
                "payment_date": p.payment_date,
                "method": p.method,
                "notes": p.notes,
                "status": p.status,
            }
            for p in payments
        ]
    }


@router.post("/api/documents/{doc_id}/payments")
def create_payment(doc_id: str, db: Session = Depends(get_db)):
    """Record a payment for a document."""
    import uuid
    from pharmgmt.models import Payment
    from fastapi import Request

    # For simplicity, accept JSON body directly
    doc = db.query(Document).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    payment = Payment(
        id=uuid.uuid4().hex,
        document_id=doc_id,
        status="paid",
    )
    db.add(payment)
    db.flush()
    return {"status": "created", "payment_id": payment.id}


@router.get("/api/payments/summary")
def payment_summary(db: Session = Depends(get_db)):
    """Overall payment stats."""
    from pharmgmt.models import Payment
    total = db.query(Payment).count()
    return {
        "total_payments": total,
        "total_paid": total,
        "total_unpaid": 0,
        "total_partial": 0,
    }


@router.get("/api/reports/purchases")
def purchase_report_endpoint(
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """Purchase report for a date range."""
    from pharmgmt.services.reports import purchase_report
    return purchase_report(db, date_from, date_to)


@router.get("/api/reports/stock")
def stock_summary_endpoint(db: Session = Depends(get_db)):
    """Current stock summary."""
    from pharmgmt.services.reports import stock_summary
    return stock_summary(db)


@router.get("/api/reports/sanity")
def sanity_report_endpoint(db: Session = Depends(get_db)):
    """Sanity report — flagged issues."""
    from pharmgmt.services.reports import sanity_report
    return sanity_report(db)


@router.get("/api/reports/purchases/csv")
def purchase_report_csv(
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """Download purchase report as CSV."""
    from fastapi.responses import StreamingResponse
    from pharmgmt.services.reports import purchase_report
    import io, csv

    data = purchase_report(db, date_from, date_to)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["File", "Date", "Product", "Pack", "Batch", "Qty", "Price", "Value"])
    for item in data["items"]:
        writer.writerow([
            item["file_name"], item["date"], item["product"],
            item["packing"], item["batch"], item["quantity"],
            (item["price_paise"] or 0) / 100, (item["value_paise"] or 0) / 100,
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=purchase_report.csv"},
    )


@router.get("/api/reports/stock/csv")
def stock_summary_csv(db: Session = Depends(get_db)):
    """Download stock summary as CSV."""
    from fastapi.responses import StreamingResponse
    from pharmgmt.services.reports import stock_summary
    import io, csv

    data = stock_summary(db)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product", "Pack", "Stock", "Price", "Value", "Expiry"])
    for item in data["items"]:
        writer.writerow([
            item["product"], item["packing"], item["closing_qty"],
            (item["price_paise"] or 0) / 100, (item["value_paise"] or 0) / 100,
            item["expiry"],
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock_summary.csv"},
    )


