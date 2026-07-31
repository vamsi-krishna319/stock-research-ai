"""
Custom ChromaDB embedding function backed by Gemini Embeddings
(via langchain-google-genai), so all vectors stored in ChromaDB
are produced by Gemini rather than any local/default model.
"""
from chromadb import Documents, EmbeddingFunction, Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self._embedder = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )

    def __call__(self, input: Documents) -> Embeddings:
        # GoogleGenerativeAIEmbeddings.embed_documents handles batching
        return self._embedder.embed_documents(list(input))
