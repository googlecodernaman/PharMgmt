"""LineItem model — invoice rows, one per product/batch on the bill."""

import uuid

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    page = Column(Integer, nullable=True)
    row_index = Column(Integer, nullable=True)
    product_id = Column(String, nullable=True)
    product_name_raw = Column(String, nullable=True)
    packing = Column(String, nullable=True)
    batch_no = Column(String, nullable=True)
    expiry = Column(String, nullable=True)
    opening_qty = Column(Integer, nullable=True)
    receipt_qty = Column(Integer, nullable=True)
    total_qty = Column(Integer, nullable=True)
    issue_qty = Column(Integer, nullable=True)
    breakage_qty = Column(Integer, nullable=True)
    closing_qty = Column(Integer, nullable=True)
    reorder_qty = Column(Integer, nullable=True)
    near_expiry_qty = Column(Integer, nullable=True)
    price_paise = Column(Integer, nullable=True)
    parser_confidence = Column(Float, nullable=True)  # 0.0–1.0
    raw_row_text = Column(Text, nullable=True)
    source_coords = Column(Text, nullable=True)  # JSON: {x1, y1, x2, y2}

    # Relationships
    document = relationship("Document", back_populates="line_items")

    def __repr__(self):
        return f"<LineItem(id={self.id[:8]}..., product={self.product_name_raw})>"


# Indices
Index("idx_line_items_product", LineItem.product_id)
Index("idx_line_items_document", LineItem.document_id)
