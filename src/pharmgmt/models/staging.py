"""Staging models — raw files, extracted text, and staged rows for QA pipeline."""

import uuid

from sqlalchemy import Column, ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class RawFile(Base):
    """Binary storage for uploaded PDF files."""
    __tablename__ = "raw_files"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    file_blob = Column(LargeBinary, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="raw_file")

    def __repr__(self):
        return f"<RawFile(id={self.id[:8]}..., doc={self.document_id[:8]}...)>"


class ExtractedText(Base):
    """Raw extracted text per page."""
    __tablename__ = "extracted_text"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    page = Column(Integer, nullable=True)
    text_json = Column(Text, nullable=True)  # raw extracted text as JSON

    # Relationships
    document = relationship("Document", back_populates="extracted_texts")

    def __repr__(self):
        return f"<ExtractedText(id={self.id[:8]}..., page={self.page})>"


class StagedRow(Base):
    """Pre-canonical rows for QA review before promotion to canonical tables."""
    __tablename__ = "staged_rows"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    page = Column(Integer, nullable=True)
    row_index = Column(Integer, nullable=True)
    raw_data = Column(Text, nullable=True)  # JSON of raw extracted row
    canonical_data = Column(Text, nullable=True)  # JSON mapped to canonical fields
    status = Column(String, default="pending")  # 'pending' | 'accepted' | 'rejected' | 'corrected'
    reviewer_notes = Column(Text, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="staged_rows")

    def __repr__(self):
        return f"<StagedRow(id={self.id[:8]}..., status={self.status})>"


# Indices
Index("idx_staged_rows_status", StagedRow.status)
