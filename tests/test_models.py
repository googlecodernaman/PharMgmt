"""Tests for SQLAlchemy ORM models."""

import pytest
from sqlalchemy.exc import IntegrityError

from pharmgmt.models import (
    Document, Supplier, Product, Batch, LineItem,
    ParsingRun, Alert, Payment, StagedRow, SchemaMeta,
)


class TestDocument:
    def test_create_document(self, db_session):
        doc = Document(file_name="test.pdf", original_file_hash="abc123")
        db_session.add(doc)
        db_session.flush()

        assert doc.id is not None
        assert doc.file_name == "test.pdf"
        assert doc.schema_version == 1
        assert doc.is_scanned == 0
        assert doc.ingest_ts is not None

    def test_duplicate_hash_rejected(self, db_session):
        doc1 = Document(file_name="test1.pdf", original_file_hash="same_hash")
        db_session.add(doc1)
        db_session.flush()

        doc2 = Document(file_name="test2.pdf", original_file_hash="same_hash")
        db_session.add(doc2)
        with pytest.raises(IntegrityError):
            db_session.flush()


class TestSupplier:
    def test_create_supplier(self, db_session):
        s = Supplier(name="Pharma Corp", address="123 Main St", gstin="29AABCU9603R1ZM")
        db_session.add(s)
        db_session.flush()

        assert s.id is not None
        assert s.name == "Pharma Corp"


class TestProduct:
    def test_create_product(self, db_session):
        p = Product(normalized_name="paracetamol 500mg", raw_names='["Paracetamol 500mg", "PARACETAMOL TAB"]', unit="strip")
        db_session.add(p)
        db_session.flush()

        assert p.id is not None
        assert p.normalized_name == "paracetamol 500mg"


class TestLineItem:
    def test_create_with_document(self, db_session):
        doc = Document(file_name="bill.pdf")
        db_session.add(doc)
        db_session.flush()

        li = LineItem(
            document_id=doc.id,
            product_name_raw="Paracetamol 500mg",
            opening_qty=100, closing_qty=70,
            price_paise=2550,
            parser_confidence=0.95,
        )
        db_session.add(li)
        db_session.flush()

        assert li.id is not None
        assert li.price_paise == 2550
        assert li.parser_confidence == 0.95


class TestBatch:
    def test_create_batch(self, db_session):
        p = Product(normalized_name="test drug")
        db_session.add(p)
        db_session.flush()

        b = Batch(product_id=p.id, batch_no="B001", expiry_normalized="2025-06-01", expiry_precision="month", mrp_paise=2550)
        db_session.add(b)
        db_session.flush()

        assert b.mrp_paise == 2550
        assert b.expiry_precision == "month"


class TestPayment:
    def test_default_status(self, db_session):
        doc = Document(file_name="bill.pdf")
        db_session.add(doc)
        db_session.flush()

        pay = Payment(document_id=doc.id, amount_paise=125000)
        db_session.add(pay)
        db_session.flush()

        assert pay.status == "unpaid"
        assert pay.paid_amount_paise == 0


class TestSchemaMeta:
    def test_version_set(self, db_session):
        meta = db_session.query(SchemaMeta).filter_by(key="schema_version").first()
        assert meta is not None
        assert meta.value == "1"
