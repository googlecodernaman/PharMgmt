"""Product model — normalized product catalog."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from .base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    normalized_name = Column(String, nullable=False)
    raw_names = Column(Text, nullable=True)  # JSON array of aliases
    unit = Column(String, nullable=True)  # strip/pack/ML etc
    primary_pack_size = Column(Integer, nullable=True)
    drug_code = Column(String, nullable=True)  # nullable SKU
    created_ts = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<Product(id={self.id[:8]}..., name={self.normalized_name})>"


# Indices
Index("idx_products_name", Product.normalized_name)
