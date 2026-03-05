"""Alert model — expiry and stock alerts."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String

from .base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    type = Column(String, nullable=False)  # 'expiry_30d' | 'expiry_60d' | 'expiry_90d' | 'low_stock'
    product_id = Column(String, nullable=True)
    batch_id = Column(String, nullable=True)
    due_date = Column(String, nullable=True)  # ISO date
    is_dismissed = Column(Integer, default=0)  # SQLite boolean
    created_ts = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<Alert(id={self.id[:8]}..., type={self.type})>"


# Indices
Index("idx_alerts_due", Alert.due_date)
Index("idx_alerts_type", Alert.type, Alert.is_dismissed)
