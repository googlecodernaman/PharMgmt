"""Generate sample PDF bills for testing the parser.

Creates 3 sample PDFs matching the canonical bill types:
1. Sales & Stock Statement
2. Batch-wise Stock Report
3. Short Sales & Stock Statement

Usage:
    python tests/fixtures/generate_samples.py
"""

import json
import os
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


FIXTURES_DIR = Path(__file__).parent
EXPECTED_DIR = FIXTURES_DIR / "expected"


def _draw_table(c, x_start, y_start, headers, rows, col_widths):
    """Draw a simple table on the canvas."""
    y = y_start

    # Draw header
    c.setFont("Helvetica-Bold", 8)
    x = x_start
    for header, width in zip(headers, col_widths):
        c.drawString(x, y, str(header))
        x += width
    y -= 14

    # Draw separator
    c.line(x_start, y + 5, x_start + sum(col_widths), y + 5)
    y -= 2

    # Draw rows
    c.setFont("Helvetica", 8)
    for row in rows:
        x = x_start
        for val, width in zip(row, col_widths):
            c.drawString(x, y, str(val))
            x += width
        y -= 13

    return y


def generate_sales_stock_pdf(output_path: str) -> list[dict]:
    """Generate a Sales & Stock Statement sample PDF.

    Returns:
        Expected gold data (list of canonical row dicts)
    """
    c = canvas.Canvas(output_path, pagesize=A4)

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 780, "PHARMA DISTRIBUTORS - Sales & Stock Statement")
    c.setFont("Helvetica", 10)
    c.drawString(50, 762, "GSTIN: 29AABCU9603R1ZM")
    c.drawString(50, 747, "Period: 01/01/2025 to 31/01/2025")

    headers = ["Product", "Pack", "Op Bal", "Pur", "Total", "Sales", "Cl Bal", "MRP"]
    col_widths = [130, 45, 50, 45, 45, 45, 50, 50]

    rows = [
        ["Paracetamol 500mg Tab", "10'S", "100", "50", "150", "80", "70", "25.50"],
        ["Amoxicillin 250mg Cap", "15'S", "200", "100", "300", "150", "150", "85.00"],
        ["Omeprazole 20mg Cap", "10'S", "50", "30", "80", "40", "40", "42.00"],
        ["Cetirizine 10mg Tab", "10'S", "300", "0", "300", "120", "180", "15.00"],
        ["Azithromycin 500mg Tab", "3'S", "80", "40", "120", "65", "55", "95.00"],
    ]

    _draw_table(c, 50, 720, headers, rows, col_widths)

    # Add a total row
    total_y = 720 - 14 * (len(rows) + 1) - 20
    c.setFont("Helvetica-Bold", 8)
    c.drawString(50, total_y, "Total")
    c.drawString(50 + 130 + 45, total_y, "730")
    c.drawString(50 + 130 + 45 + 50, total_y, "220")

    c.showPage()
    c.save()

    # Gold data
    gold = [
        {"product_name_raw": "Paracetamol 500mg Tab", "packing": "10'S", "opening_qty": 100, "receipt_qty": 50, "total_qty": 150, "issue_qty": 80, "closing_qty": 70, "price_paise": 2550},
        {"product_name_raw": "Amoxicillin 250mg Cap", "packing": "15'S", "opening_qty": 200, "receipt_qty": 100, "total_qty": 300, "issue_qty": 150, "closing_qty": 150, "price_paise": 8500},
        {"product_name_raw": "Omeprazole 20mg Cap", "packing": "10'S", "opening_qty": 50, "receipt_qty": 30, "total_qty": 80, "issue_qty": 40, "closing_qty": 40, "price_paise": 4200},
        {"product_name_raw": "Cetirizine 10mg Tab", "packing": "10'S", "opening_qty": 300, "receipt_qty": 0, "total_qty": 300, "issue_qty": 120, "closing_qty": 180, "price_paise": 1500},
        {"product_name_raw": "Azithromycin 500mg Tab", "packing": "3'S", "opening_qty": 80, "receipt_qty": 40, "total_qty": 120, "issue_qty": 65, "closing_qty": 55, "price_paise": 9500},
    ]
    return gold


def generate_batch_stock_pdf(output_path: str) -> list[dict]:
    """Generate a Batch-wise Stock Report sample PDF."""
    c = canvas.Canvas(output_path, pagesize=A4)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 780, "Batch-wise Stock Report")
    c.setFont("Helvetica", 10)
    c.drawString(50, 762, "Supplier: MEDICO PHARMA LTD")
    c.drawString(50, 747, "GSTIN: 07AAACM5678Q1Z5")

    headers = ["Product", "Pack", "Batch", "Expiry", "Stock", "MRP"]
    col_widths = [150, 50, 60, 60, 50, 55]

    rows = [
        ["Metformin 500mg Tab", "10'S", "MET001", "06/2026", "250", "32.00"],
        ["Atorvastatin 10mg Tab", "10'S", "ATV002", "03/2025", "80", "55.00"],
        ["Losartan 50mg Tab", "10'S", "LOS003", "12/2025", "120", "48.00"],
        ["Pantoprazole 40mg Tab", "10'S", "PAN004", "09/2026", "300", "65.00"],
        ["Metformin 500mg Tab", "10'S", "MET005", "01/2026", "100", "32.00"],
    ]

    _draw_table(c, 50, 720, headers, rows, col_widths)
    c.showPage()
    c.save()

    gold = [
        {"product_name_raw": "Metformin 500mg Tab", "packing": "10'S", "batch_no": "MET001", "expiry": "06/2026", "closing_qty": 250, "price_paise": 3200},
        {"product_name_raw": "Atorvastatin 10mg Tab", "packing": "10'S", "batch_no": "ATV002", "expiry": "03/2025", "closing_qty": 80, "price_paise": 5500},
        {"product_name_raw": "Losartan 50mg Tab", "packing": "10'S", "batch_no": "LOS003", "expiry": "12/2025", "closing_qty": 120, "price_paise": 4800},
        {"product_name_raw": "Pantoprazole 40mg Tab", "packing": "10'S", "batch_no": "PAN004", "expiry": "09/2026", "closing_qty": 300, "price_paise": 6500},
        {"product_name_raw": "Metformin 500mg Tab", "packing": "10'S", "batch_no": "MET005", "expiry": "01/2026", "closing_qty": 100, "price_paise": 3200},
    ]
    return gold


def generate_short_sales_pdf(output_path: str) -> list[dict]:
    """Generate a Short Sales & Stock Statement sample PDF."""
    c = canvas.Canvas(output_path, pagesize=A4)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 780, "Short Sales & Stock Statement")
    c.setFont("Helvetica", 10)
    c.drawString(50, 762, "ABC MEDICAL STORES")

    headers = ["Product", "Pack", "Op Bal", "Pur", "Total", "Sales", "Cl Bal", "CP"]
    col_widths = [130, 45, 50, 45, 45, 45, 50, 50]

    rows = [
        ["Diclofenac 50mg Tab", "10'S", "150", "75", "225", "100", "125", "18.50"],
        ["Ranitidine 150mg Tab", "10'S", "90", "60", "150", "85", "65", "22.00"],
        ["Ciprofloxacin 500mg Tab", "10'S", "40", "20", "60", "30", "30", "38.00"],
        ["Doxycycline 100mg Cap", "10'S", "200", "0", "200", "75", "125", "45.00"],
    ]

    _draw_table(c, 50, 720, headers, rows, col_widths)

    # Total row
    total_y = 720 - 14 * (len(rows) + 1) - 15
    c.setFont("Helvetica-Bold", 8)
    c.drawString(50, total_y, "Total")

    c.showPage()
    c.save()

    gold = [
        {"product_name_raw": "Diclofenac 50mg Tab", "packing": "10'S", "opening_qty": 150, "receipt_qty": 75, "total_qty": 225, "issue_qty": 100, "closing_qty": 125, "price_paise": 1850},
        {"product_name_raw": "Ranitidine 150mg Tab", "packing": "10'S", "opening_qty": 90, "receipt_qty": 60, "total_qty": 150, "issue_qty": 85, "closing_qty": 65, "price_paise": 2200},
        {"product_name_raw": "Ciprofloxacin 500mg Tab", "packing": "10'S", "opening_qty": 40, "receipt_qty": 20, "total_qty": 60, "issue_qty": 30, "closing_qty": 30, "price_paise": 3800},
        {"product_name_raw": "Doxycycline 100mg Cap", "packing": "10'S", "opening_qty": 200, "receipt_qty": 0, "total_qty": 200, "issue_qty": 75, "closing_qty": 125, "price_paise": 4500},
    ]
    return gold


def generate_all():
    """Generate all sample PDFs and save gold data."""
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    os.makedirs(EXPECTED_DIR, exist_ok=True)

    samples = [
        ("sample_sales_stock.pdf", generate_sales_stock_pdf, "sales_stock"),
        ("sample_batch_stock.pdf", generate_batch_stock_pdf, "batch_stock"),
        ("sample_short_sales.pdf", generate_short_sales_pdf, "short_sales"),
    ]

    for filename, generator, bill_type in samples:
        pdf_path = str(FIXTURES_DIR / filename)
        gold = generator(pdf_path)

        # Save gold JSON
        gold_path = str(EXPECTED_DIR / f"{bill_type}.json")
        with open(gold_path, "w", encoding="utf-8") as f:
            json.dump(gold, f, indent=2)

        print(f"Generated: {filename} ({len(gold)} rows) + {bill_type}.json")


if __name__ == "__main__":
    generate_all()
