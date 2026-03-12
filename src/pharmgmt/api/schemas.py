"""Pydantic response schemas for API endpoints."""

from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    schema_version: int


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    supplier_name: str | None = None
    title: str | None = None
    report_from: str | None = None
    report_to: str | None = None
    ingest_ts: datetime
    line_item_count: int = 0

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class DocumentDetailResponse(DocumentResponse):
    raw_text: str | None = None
    is_scanned: bool = False
    parser_version: str | None = None
    line_items: list[dict] = []


class ParseResultRow(BaseModel):
    page: int
    row_index: int
    raw_text: str | None = None
    fields: dict = {}
    confidence: float = 0.0
    warnings: list[str] = []


class ParseResultMeta(BaseModel):
    parser_version: str
    duration_ms: int
    rows_parsed: int
    rows_flagged: int
    avg_confidence: float
    error_flags: list[str] = []
    bill_type: str | None = None
    ml_assisted: bool = False


class ParseResultResponse(BaseModel):
    document: dict
    rows: list[ParseResultRow]
    meta: ParseResultMeta
