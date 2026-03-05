"""Payment model — payment status per document."""

import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    status = Column(String, default="unpaid")  # 'paid' | 'unpaid' | 'partial'
    amount_paise = Column(Integer, nullable=True)
    paid_amount_paise = Column(Integer, default=0)
    paid_date = Column(String, nullable=True)  # ISO date
    notes = Column(Text, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="payment")

    def __repr__(self):
        return f"<Payment(id={self.id[:8]}..., status={self.status})>"
