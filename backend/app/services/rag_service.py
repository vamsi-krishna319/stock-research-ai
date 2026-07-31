"""
Retrieval-Augmented Generation service on top of ChromaDB.

Handles ingestion of financial documents (SEC filings text, uploaded
PDFs) as embedded chunks, and retrieval of the most relevant chunks
for a given ticker/query to ground Gemini's analysis.
"""
import logging
import uuid

from app.database.chromadb_client import get_financial_docs_collection
from app.services.pdf_service import chunk_text

logger = logging.getLogger(__name__)


def ingest_document(ticker: str, text: str, doc_type: str, source: str) -> int:
    """
    Chunk and store a document's text in ChromaDB under the shared
    financial_documents collection. Returns number of chunks stored.
    """
    if not text:
        return 0
    collection = get_financial_docs_collection()
    chunks = chunk_text(text)
    if not chunks:
        return 0

    ids = [f"{ticker}-{doc_type}-{uuid.uuid4().hex[:10]}-{i}" for i in range(len(chunks))]
    metadatas = [
        {"ticker": ticker.upper(), "doc_type": doc_type, "source": source, "chunk_index": i}
        for i in range(len(chunks))
    ]
    try:
        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        return len(chunks)
    except Exception as exc:  # noqa: BLE001
        logger.error("ChromaDB ingestion failed: %s", exc)
        return 0


def retrieve_relevant_chunks(ticker: str, query: str, n_results: int = 5) -> list[str]:
    """Retrieve the most relevant document chunks for a ticker + query."""
    collection = get_financial_docs_collection()
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"ticker": ticker.upper()},
        )
        docs = results.get("documents", [[]])
        return docs[0] if docs else []
    except Exception as exc:  # noqa: BLE001
        logger.error("ChromaDB retrieval failed: %s", exc)
        return []


def retrieve_any(query: str, n_results: int = 5) -> list[str]:
    """Retrieve relevant chunks across all tickers (used by chat assistant)."""
    collection = get_financial_docs_collection()
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])
        return docs[0] if docs else []
    except Exception as exc:  # noqa: BLE001
        logger.error("ChromaDB retrieval failed: %s", exc)
        return []
