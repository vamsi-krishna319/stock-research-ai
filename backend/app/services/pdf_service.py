"""
PDF processing utilities using PyPDF: text extraction and
simple fixed-size chunking for RAG ingestion.
"""
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF file on disk."""
    try:
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)
    except Exception as exc:  # noqa: BLE001
        logger.error("PDF text extraction failed for %s: %s", pdf_path, exc)
        return ""


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks suitable for embedding."""
    if not text:
        return []
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
