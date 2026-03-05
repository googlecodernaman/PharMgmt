"""Schema metadata model for version tracking."""

from sqlalchemy import Column, String

from .base import Base


class SchemaMeta(Base):
    __tablename__ = "schema_meta"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=True)

    def __repr__(self):
        return f"<SchemaMeta(key={self.key}, value={self.value})>"
