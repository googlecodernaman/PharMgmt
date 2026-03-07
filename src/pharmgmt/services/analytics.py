"""Analytics service — price comparison, supplier analytics."""

import logging

logger = logging.getLogger("pharmgmt.analytics")


def get_price_history(session, product_name: str) -> list[dict]:
    """Get price history for a product across all bills.

    Args:
        session: SQLAlchemy session
        product_name: Product name to search

    Returns:
        List of price points sorted by date
    """
    from pharmgmt.models import LineItem, Document

    items = (
        session.query(LineItem, Document)
        .join(Document, LineItem.document_id == Document.id)
        .filter(LineItem.product_name_raw == product_name)
        .filter(LineItem.price_paise.isnot(None))
        .order_by(Document.ingest_ts)
        .all()
    )

    return [
        {
            "date": doc.ingest_ts.isoformat() if doc.ingest_ts else None,
            "price_paise": li.price_paise,
            "document_id": doc.id,
            "file_name": doc.file_name,
        }
        for li, doc in items
    ]


def get_price_changes(session) -> list[dict]:
    """Detect products with price changes across bills.

    Returns:
        List of products with old/new price and change percentage
    """
    from sqlalchemy import func
    from pharmgmt.models import LineItem, Document

    # Get all products with more than one distinct price
    products = (
        session.query(LineItem.product_name_raw)
        .filter(LineItem.product_name_raw.isnot(None))
        .filter(LineItem.price_paise.isnot(None))
        .group_by(LineItem.product_name_raw)
        .having(func.count(func.distinct(LineItem.price_paise)) > 1)
        .all()
    )

    changes = []
    for (product_name,) in products:
        history = get_price_history(session, product_name)
        if len(history) < 2:
            continue

        # Get unique prices in order
        seen = []
        for h in history:
            if not seen or seen[-1]["price_paise"] != h["price_paise"]:
                seen.append(h)

        if len(seen) < 2:
            continue

        old_price = seen[-2]["price_paise"]
        new_price = seen[-1]["price_paise"]
        change_pct = ((new_price - old_price) / old_price * 100) if old_price else 0

        changes.append({
            "product": product_name,
            "old_price": old_price,
            "new_price": new_price,
            "change_pct": round(change_pct, 1),
            "direction": "up" if new_price > old_price else "down",
            "old_date": seen[-2].get("date"),
            "new_date": seen[-1].get("date"),
        })

    changes.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return changes
