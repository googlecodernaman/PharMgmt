"""Retention policy — clean up old raw data while preserving parsed records."""

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("pharmgmt.retention")

# Defaults (configurable)
RAW_RETENTION_DAYS = 90
TEXT_RETENTION_DAYS = 180


def cleanup_old_data(session, raw_days: int = RAW_RETENTION_DAYS, text_days: int = TEXT_RETENTION_DAYS) -> dict:
    """Delete old raw files and extracted text but keep parsed records.

    Args:
        session: SQLAlchemy session
        raw_days: Days to keep raw PDF files
        text_days: Days to keep extracted text

    Returns:
        Dict with deletion counts
    """
    from pharmgmt.models import RawFile, ExtractedText, Document

    now = datetime.now(timezone.utc)
    raw_cutoff = now - timedelta(days=raw_days)
    text_cutoff = now - timedelta(days=text_days)

    # Find old documents
    old_raw_docs = (
        session.query(Document.id)
        .filter(Document.ingest_ts < raw_cutoff)
        .all()
    )
    old_raw_ids = [d.id for d in old_raw_docs]

    old_text_docs = (
        session.query(Document.id)
        .filter(Document.ingest_ts < text_cutoff)
        .all()
    )
    old_text_ids = [d.id for d in old_text_docs]

    # Delete raw files
    raw_deleted = 0
    if old_raw_ids:
        raw_deleted = session.query(RawFile).filter(RawFile.document_id.in_(old_raw_ids)).delete(synchronize_session=False)
        logger.info("Deleted %d raw files older than %d days", raw_deleted, raw_days)

    # Delete extracted texts
    text_deleted = 0
    if old_text_ids:
        text_deleted = session.query(ExtractedText).filter(ExtractedText.document_id.in_(old_text_ids)).delete(synchronize_session=False)
        logger.info("Deleted %d extracted texts older than %d days", text_deleted, text_days)

    session.commit()

    return {
        "raw_files_deleted": raw_deleted,
        "extracted_texts_deleted": text_deleted,
        "raw_cutoff_days": raw_days,
        "text_cutoff_days": text_days,
    }
