"""Supplier model — normalized supplier/vendor records."""

import uuid

from sqlalchemy import Column, String

from .base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    gstin = Column(String, nullable=True)

    def __repr__(self):
        return f"<Supplier(id={self.id[:8]}..., name={self.name})>"
