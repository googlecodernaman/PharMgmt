"""Pytest configuration and shared fixtures."""

import os
import tempfile
import pytest

from pharmgmt.db import init_db, get_db_session
from pharmgmt.models import engine_factory, session_factory, Base


@pytest.fixture
def db_url(tmp_path):
    """Create a temporary SQLite database URL."""
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    init_db(url)
    return url


@pytest.fixture
def db_session(db_url):
    """Yield a database session for testing."""
    engine = engine_factory(db_url)
    Session = session_factory(engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a minimal valid PDF file for testing."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4

        pdf_path = tmp_path / "sample_bill.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=A4)

        # Page 1 — header and a simple table
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 780, "SAMPLE SUPPLIER - Stock Statement")
        c.setFont("Helvetica", 10)
        c.drawString(50, 760, "GSTIN: 29AABCU9603R1ZM")
        c.drawString(50, 745, "Period: 01/01/2025 to 31/01/2025")

        # Table header
        y = 710
        headers = ["Product", "Pack", "Batch", "Expiry", "Op Bal", "Pur", "Sales", "Cl Bal", "MRP"]
        x_positions = [50, 170, 230, 290, 350, 400, 445, 495, 545]
        c.setFont("Helvetica-Bold", 8)
        for header, x in zip(headers, x_positions):
            c.drawString(x, y, header)

        # Table rows
        c.setFont("Helvetica", 8)
        rows = [
            ["Paracetamol 500mg", "10'S", "B001", "06/2026", "100", "50", "80", "70", "25.50"],
            ["Amoxicillin 250mg", "15'S", "B002", "03/2025", "200", "100", "150", "150", "85.00"],
            ["Omeprazole 20mg", "10'S", "B003", "12/2025", "50", "30", "40", "40", "42.00"],
        ]
        for row in rows:
            y -= 15
            for val, x in zip(row, x_positions):
                c.drawString(x, y, val)

        c.showPage()
        c.save()
        return str(pdf_path)

    except ImportError:
        # Fallback: create a minimal valid PDF manually
        pdf_path = tmp_path / "sample_bill.pdf"
        minimal_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
            b"xref\n0 4\n0000000000 65535 f \n"
            b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
            b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n206\n%%EOF"
        )
        pdf_path.write_bytes(minimal_pdf)
        return str(pdf_path)


@pytest.fixture
def test_client(db_url):
    """Create a FastAPI test client."""
    import os
    os.environ["PHARM_DATABASE_URL"] = db_url
    os.environ["PHARM_LOG_DIR"] = "./test_logs"

    from httpx import ASGITransport, AsyncClient
    from pharmgmt.main import app

    from fastapi.testclient import TestClient
    client = TestClient(app)
    yield client

    # Cleanup
    os.environ.pop("PHARM_DATABASE_URL", None)
    os.environ.pop("PHARM_LOG_DIR", None)
