"""
Portfolio Manager Agent
------------------------
If the user supplied a full portfolio (list of ticker+weight holdings),
this agent computes sector concentration and a return-correlation
matrix, then asks Gemini to comment on diversification. If no
portfolio was supplied (single-ticker research mode), this agent
is a lightweight pass-through.
"""
import logging

import pandas as pd

from app.agents.state import ResearchState
from app.services import gemini_service
from app.services.yfinance_service import get_company_info, get_returns

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a portfolio management agent inside a stock research system.
Given a portfolio's holdings, sector concentration breakdown, and a return-correlation matrix,
produce a JSON object with:
{
  "diversification_rating": "well_diversified" | "moderately_diversified" | "concentrated",
  "sector_concentration_commentary": "<1-3 sentences>",
  "correlation_commentary": "<1-3 sentences>",
  "summary": "<3-5 sentence overall portfolio assessment>"
}"""


def run_portfolio_agent(state: ResearchState) -> ResearchState:
    holdings = state.get("portfolio_holdings")
    errors = list(state.get("errors", []))

    if not holdings:
        return {
            **state,
            "portfolio_analysis": {
                "skipped": True,
                "summary": "No portfolio was supplied; single-ticker research mode.",
            },
            "errors": errors,
        }

    tickers = [h["ticker"] for h in holdings]
    weights = {h["ticker"]: h["weight"] for h in holdings}

    sector_weights: dict[str, float] = {}
    returns_map = {}
    for t in tickers:
        info = get_company_info(t)
        sector = info.get("sector") or "Unknown"
        sector_weights[sector] = sector_weights.get(sector, 0.0) + weights.get(t, 0.0)

        r = get_returns(t, period="6mo")
        if not r.empty:
            returns_map[t] = r

    correlation_matrix = {}
    if len(returns_map) > 1:
        combined = pd.DataFrame(returns_map).dropna()
        if not combined.empty:
            correlation_matrix = combined.corr().round(3).to_dict()

    user_prompt = (
        f"Holdings: {holdings}\n\n"
        f"Sector weight breakdown: {sector_weights}\n\n"
        f"Return correlation matrix: {correlation_matrix or 'insufficient data'}"
    )

    analysis = gemini_service.ask_json(SYSTEM_PROMPT, user_prompt)
    analysis["sector_weights"] = sector_weights
    analysis["correlation_matrix"] = correlation_matrix
    analysis["skipped"] = False

    return {**state, "portfolio_analysis": analysis, "errors": errors}
