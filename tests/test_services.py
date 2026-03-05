"""Tests for ingestion and text extraction services."""

import pytest
from pharmgmt.services.ingestion import compute_file_hash, ingest_pdf


class TestComputeFileHash:
    def test_returns_64_char_hex(self):
        h = compute_file_hash(b"test content")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic(self):
        h1 = compute_file_hash(b"same content")
        h2 = compute_file_hash(b"same content")
        assert h1 == h2

    def test_different_content(self):
        h1 = compute_file_hash(b"content A")
        h2 = compute_file_hash(b"content B")
        assert h1 != h2


class TestIngestPdf:
    def test_ingest_success(self, db_session, sample_pdf_path):
        result = ingest_pdf(db_session, sample_pdf_path, "test_bill.pdf")
        assert result["status"] == "success"
        assert "document_id" in result
        assert result["pages_extracted"] >= 1

    def test_ingest_duplicate(self, db_session, sample_pdf_path):
        # First ingest
        result1 = ingest_pdf(db_session, sample_pdf_path, "test_bill.pdf")
        db_session.commit()
        assert result1["status"] == "success"

        # Second ingest of same file
        result2 = ingest_pdf(db_session, sample_pdf_path, "test_bill_copy.pdf")
        assert result2["status"] == "duplicate"

    def test_ingest_nonexistent_file(self, db_session):
        result = ingest_pdf(db_session, "/nonexistent/file.pdf", "missing.pdf")
        assert result["status"] == "error"
