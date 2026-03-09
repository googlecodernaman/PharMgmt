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

    Raises:
        ValueError: If the file is not a valid PDF or is password-protected
    """
    results = []

    try:
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("PDF has 0 pages — file may be empty or corrupt")

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

    except ValueError:
        raise  # Re-raise our own errors
    except Exception as e:
        err_msg = str(e).lower()
        if "password" in err_msg or "encrypted" in err_msg:
            raise ValueError("This PDF is password-protected. Please unlock it first.") from e
        elif "not a pdf" in err_msg or "invalid" in err_msg:
            raise ValueError("This file is not a valid PDF.") from e
        else:
            raise ValueError(f"Failed to read PDF: {e}") from e

    return results

