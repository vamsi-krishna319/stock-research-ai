"""
Pydantic models for API request/response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------- Research ----------------
class ResearchRequest(BaseModel):
    ticker: str
    uploaded_pdf_id: Optional[str] = None  # optional manually uploaded filing
    user_id: Optional[str] = "default_user"


class ResearchResponse(BaseModel):
    ticker: str
    news_analysis: dict
    financial_analysis: dict
    technical_analysis: dict
    risk_analysis: dict
    advisor_recommendation: dict
    report_markdown: str
    report_id: str
    created_at: datetime


# ---------------- Portfolio ----------------
class PortfolioHolding(BaseModel):
    ticker: str
    weight: float = Field(..., ge=0, le=1)
    shares: Optional[float] = None


class PortfolioCreateRequest(BaseModel):
    user_id: str = "default_user"
    name: str
    holdings: list[PortfolioHolding]


class PortfolioAnalyzeRequest(BaseModel):
    holdings: list[PortfolioHolding]


# ---------------- Watchlist ----------------
class WatchlistItem(BaseModel):
    ticker: str
    note: Optional[str] = None


class WatchlistCreateRequest(BaseModel):
    user_id: str = "default_user"
    tickers: list[WatchlistItem]


# ---------------- Chat ----------------
class ChatRequest(BaseModel):
    session_id: str
    message: str
    ticker_context: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    sources: list[str] = []


# ---------------- Upload ----------------
class UploadResponse(BaseModel):
    file_id: str
    filename: str
    ticker: str
    chunks_ingested: int
