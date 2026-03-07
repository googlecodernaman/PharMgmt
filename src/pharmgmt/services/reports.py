"""Reports service — purchase reports, stock summaries, sanity reports."""

import json
import logging

logger = logging.getLogger("pharmgmt.reports")


def purchase_report(session, date_from: str = None, date_to: str = None) -> dict:
    """Generate purchase report for a date range.

    Groups line items by document (supplier), then product.

    Returns:
        Dict with items list and totals
    """
    from pharmgmt.models import LineItem, Document

    query = session.query(LineItem, Document).join(Document, LineItem.document_id == Document.id)

    if date_from:
        query = query.filter(Document.ingest_ts >= date_from)
    if date_to:
        query = query.filter(Document.ingest_ts <= date_to)

    results = query.order_by(Document.ingest_ts.desc()).all()

    items = []
    total_qty = 0
    total_value = 0

    for li, doc in results:
        qty = li.issue_qty or li.closing_qty or 0
        price = li.price_paise or 0
        value = qty * price

        items.append({
            "document_id": doc.id,
            "file_name": doc.file_name,
            "date": doc.ingest_ts.isoformat() if doc.ingest_ts else None,
            "product": li.product_name_raw,
            "packing": li.packing,
            "batch": li.batch_no,
            "quantity": qty,
            "price_paise": price,
            "value_paise": value,
        })
        total_qty += qty if isinstance(qty, (int, float)) else 0
        total_value += value if isinstance(value, (int, float)) else 0

    return {
        "items": items,
        "total_items": len(items),
        "total_quantity": total_qty,
        "total_value_paise": total_value,
    }


def stock_summary(session) -> dict:
    """Generate current stock snapshot.

    Per product: latest closing qty, latest price, total value.

    Returns:
        Dict with products list and totals
    """
    from sqlalchemy import func
    from pharmgmt.models import LineItem

    products = (
        session.query(
            LineItem.product_name_raw,
            LineItem.packing,
            func.max(LineItem.closing_qty).label("closing"),
            func.max(LineItem.price_paise).label("price"),
            func.max(LineItem.expiry).label("expiry"),
        )
        .filter(LineItem.product_name_raw.isnot(None))
        .group_by(LineItem.product_name_raw, LineItem.packing)
        .order_by(LineItem.product_name_raw)
        .all()
    )

    items = []
    total_value = 0
    for p in products:
        closing = p.closing or 0
        price = p.price or 0
        value = closing * price if isinstance(closing, (int, float)) and isinstance(price, (int, float)) else 0
        items.append({
            "product": p.product_name_raw,
            "packing": p.packing,
            "closing_qty": closing,
            "price_paise": price,
            "value_paise": value,
            "expiry": p.expiry,
        })
        total_value += value

    return {"items": items, "total_products": len(items), "total_value_paise": total_value}


def sanity_report(session) -> dict:
    """Generate sanity report with all flagged issues.

    Returns:
        Dict with flagged documents, rows, and summary
    """
    from pharmgmt.models import ParsingRun, Document

    runs = session.query(ParsingRun).all()

    flagged_docs = []
    total_flagged_rows = 0

    for pr in runs:
        flags = json.loads(pr.error_flags) if pr.error_flags else []
        if not flags and pr.rows_flagged == 0:
            continue

        doc = session.query(Document).filter_by(id=pr.document_id).first()
        flagged_docs.append({
            "document_id": pr.document_id,
            "file_name": doc.file_name if doc else None,
            "avg_confidence": pr.avg_confidence,
            "rows_flagged": pr.rows_flagged,
            "error_flags": flags,
            "needs_review": bool(pr.needs_review),
        })
        total_flagged_rows += pr.rows_flagged or 0

    return {
        "flagged_documents": flagged_docs,
        "total_flagged_docs": len(flagged_docs),
        "total_flagged_rows": total_flagged_rows,
    }
