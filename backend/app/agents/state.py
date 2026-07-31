"""
Shared state object passed between all nodes of the LangGraph
supervisor pipeline.
"""
from typing import Any, Optional, TypedDict


class ResearchState(TypedDict, total=False):
    ticker: str
    uploaded_pdf_path: Optional[str]
    portfolio_holdings: Optional[list[dict]]  # [{ticker, weight}, ...]

    news_analysis: dict[str, Any]
    financial_analysis: dict[str, Any]
    technical_analysis: dict[str, Any]
    risk_analysis: dict[str, Any]
    portfolio_analysis: dict[str, Any]
    advisor_recommendation: dict[str, Any]
    report_markdown: str

    errors: list[str]
