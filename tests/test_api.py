"""Integration tests for API endpoints."""

import pytest


class TestHealthEndpoint:
    def test_health_returns_200(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_has_schema_version(self, test_client):
        response = test_client.get("/health")
        data = response.json()
        assert "schema_version" in data
        assert data["schema_version"] >= 1


class TestDocumentsEndpoint:
    def test_list_empty(self, test_client):
        response = test_client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_upload_then_list(self, test_client, sample_pdf_path):
        # Upload
        with open(sample_pdf_path, "rb") as f:
            response = test_client.post(
                "/api/upload",
                files={"file": ("test_bill.pdf", f, "application/pdf")},
            )
        assert response.status_code == 200
        doc_id = response.json()["document"]["document_id"]

        # List
        response = test_client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == doc_id

    def test_get_document_detail(self, test_client, sample_pdf_path):
        # Upload first
        with open(sample_pdf_path, "rb") as f:
            upload_resp = test_client.post(
                "/api/upload",
                files={"file": ("bill.pdf", f, "application/pdf")},
            )
        doc_id = upload_resp.json()["document"]["document_id"]

        # Get detail
        response = test_client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert data["file_name"] == "bill.pdf"

    def test_get_document_not_found(self, test_client):
        response = test_client.get("/api/documents/nonexistent")
        assert response.status_code == 404


class TestUploadEndpoint:
    def test_upload_pdf(self, test_client, sample_pdf_path):
        with open(sample_pdf_path, "rb") as f:
            response = test_client.post(
                "/api/upload",
                files={"file": ("bill.pdf", f, "application/pdf")},
            )
        assert response.status_code == 200
        data = response.json()
        assert "document" in data
        assert "meta" in data
        assert data["meta"]["parser_version"] == "0.1.0-stub"

    def test_upload_duplicate_returns_409(self, test_client, sample_pdf_path):
        # First upload
        with open(sample_pdf_path, "rb") as f:
            test_client.post(
                "/api/upload",
                files={"file": ("bill.pdf", f, "application/pdf")},
            )

        # Duplicate upload
        with open(sample_pdf_path, "rb") as f:
            response = test_client.post(
                "/api/upload",
                files={"file": ("bill_copy.pdf", f, "application/pdf")},
            )
        assert response.status_code == 409

    def test_upload_non_pdf_rejected(self, test_client):
        response = test_client.post(
            "/api/upload",
            files={"file": ("report.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400
