"""ParsingRun model — ingestion metadata per document parse."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class ParsingRun(Base):
    __tablename__ = "parsing_runs"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    parser_version = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    rows_parsed = Column(Integer, nullable=True)
    rows_flagged = Column(Integer, nullable=True)
    error_flags = Column(Text, nullable=True)  # JSON list
    avg_confidence = Column(Float, nullable=True)
    needs_review = Column(Integer, default=0)  # SQLite boolean
    run_ts = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="parsing_runs")

    def __repr__(self):
        return f"<ParsingRun(id={self.id[:8]}..., rows={self.rows_parsed})>"
