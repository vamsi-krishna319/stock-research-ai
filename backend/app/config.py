"""
Centralized application configuration.
All values are read from environment variables (see .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_FLASH_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_PRO_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # NewsAPI
    NEWSAPI_KEY: str = ""

    # SEC EDGAR
    SEC_USER_AGENT: str = "StockResearchAI your-email@example.com"

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "stock_research_ai"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Uploads
    UPLOAD_DIR: str = "./uploads"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
