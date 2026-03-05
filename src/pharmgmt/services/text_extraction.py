"""Text extraction from PDF files using pdfplumber."""

import json
import logging

import pdfplumber

logger = logging.getLogger("pharmgmt.parsing")


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """Extract text and tables from each page of a PDF.

    Args:
        file_path: Path to the PDF file

    Returns:
        List of dicts: [{page: int, text: str, tables: list}]
    """
    results = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_data = {"page": i + 1, "text": "", "tables": []}

                try:
                    text = page.extract_text()
                    page_data["text"] = text or ""
                except Exception as e:
                    logger.warning("Text extraction failed on page %d: %s", i + 1, e)

                try:
                    tables = page.extract_tables()
                    page_data["tables"] = tables or []
                except Exception as e:
                    logger.warning("Table extraction failed on page %d: %s", i + 1, e)

                results.append(page_data)

            logger.info("Extracted %d pages from %s", len(results), file_path)

    except Exception as e:
        logger.error("Failed to open PDF %s: %s", file_path, e)
        return []

    return results
