"""
ChromaDB persistent client used as the RAG vector store for
Annual Reports, Quarterly Reports, SEC Filings and Financial
Research Documents.
"""
import chromadb

from app.config import settings
from app.database.embedding_function import GeminiEmbeddingFunction

_chroma_client = None
_embedding_fn = None

FINANCIAL_DOCS_COLLECTION = "financial_documents"


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _chroma_client


def get_embedding_function():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = GeminiEmbeddingFunction()
    return _embedding_fn


def get_financial_docs_collection():
    """
    Single collection storing Annual Reports, Quarterly Reports,
    SEC Filings and Financial Research Documents. Each document's
    metadata distinguishes its doc_type/ticker/source.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=FINANCIAL_DOCS_COLLECTION,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
