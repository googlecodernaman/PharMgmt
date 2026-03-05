"""Document model — metadata for each uploaded PDF."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    file_name = Column(String, nullable=False)
    original_file_hash = Column(String, unique=True, nullable=True)
    supplier_id = Column(String, nullable=True)
    title = Column(String, nullable=True)
    report_from = Column(String, nullable=True)  # ISO date string
    report_to = Column(String, nullable=True)
    report_generated = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    is_scanned = Column(Integer, default=0)  # SQLite boolean
    parser_version = Column(String, nullable=True)
    schema_version = Column(Integer, default=1)
    ingest_ts = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    line_items = relationship("LineItem", back_populates="document", cascade="all, delete-orphan")
    parsing_runs = relationship("ParsingRun", back_populates="document", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="document", uselist=False, cascade="all, delete-orphan")
    raw_file = relationship("RawFile", back_populates="document", uselist=False, cascade="all, delete-orphan")
    extracted_texts = relationship("ExtractedText", back_populates="document", cascade="all, delete-orphan")
    staged_rows = relationship("StagedRow", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id[:8]}..., file={self.file_name})>"


# Indices
Index("idx_documents_hash", Document.original_file_hash)
