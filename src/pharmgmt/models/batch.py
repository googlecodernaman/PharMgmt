"""Batch model — batch-level records per product."""

import uuid

from sqlalchemy import Column, Index, Integer, String

from .base import Base


class Batch(Base):
    __tablename__ = "batches"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    product_id = Column(String, nullable=False)
    batch_no = Column(String, nullable=False)
    expiry_normalized = Column(String, nullable=True)  # ISO date
    expiry_precision = Column(String, nullable=True)  # 'day' | 'month' | 'year'
    mrp_paise = Column(Integer, nullable=True)  # price in paisa

    def __repr__(self):
        return f"<Batch(id={self.id[:8]}..., batch={self.batch_no})>"


# Indices
Index("idx_batches_product_batch", Batch.product_id, Batch.batch_no)
Index("idx_batches_expiry", Batch.expiry_normalized)
