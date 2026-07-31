"""
Risk Analyzer Agent
--------------------
Runs after News, Financial Report and Technical agents have all
completed (fan-in node). Computes quantitative risk metrics
(volatility, beta vs S&P 500, Sharpe ratio, historical VaR) and
asks Gemini to synthesize an overall risk rating, taking into
account the outputs of the earlier agents.
"""
import logging

import numpy as np

from app.agents.state import ResearchState
from app.services import gemini_service
from app.services.yfinance_service import get_returns

logger = logging.getLogger(__name__)

RISK_FREE_RATE_ANNUAL = 0.04  # simplifying assumption, ~US T-bill yield

SYSTEM_PROMPT = """You are a risk assessment agent inside a stock research system.
You are given quantitative risk metrics for a stock plus summaries from a news analysis
agent, a financial report analysis agent, and a technical analysis agent. Produce a JSON
object with:
{
  "risk_rating": "low" | "moderate" | "high" | "very_high",
  "volatility_commentary": "<1-2 sentences>",
  "key_risk_factors": [<short strings, combine quantitative + qualitative factors>],
  "summary": "<3-5 sentence overall risk assessment>"
}"""


def _compute_risk_metrics(ticker: str) -> dict:
    stock_returns = get_returns(ticker, period="1y")
    market_returns = get_returns("^GSPC", period="1y")

    if stock_returns.empty:
        return {"error": "Insufficient price history to compute risk metrics."}

    annual_volatility = float(stock_returns.std() * np.sqrt(252))
    mean_daily_return = float(stock_returns.mean())
    annual_return = mean_daily_return * 252

    sharpe_ratio = None
    if annual_volatility > 0:
        sharpe_ratio = (annual_return - RISK_FREE_RATE_ANNUAL) / annual_volatility

    beta = None
    if not market_returns.empty:
        aligned = stock_returns.align(market_returns, join="inner")
        s, m = aligned
        if len(s) > 1 and m.var() > 0:
            covariance = np.cov(s, m)[0][1]
            beta = float(covariance / m.var())

    # Historical 95% Value at Risk (1-day), expressed as a positive percentage loss
    var_95 = float(-np.percentile(stock_returns, 5)) if len(stock_returns) > 5 else None

    return {
        "annual_volatility_pct": round(annual_volatility * 100, 2),
        "annual_return_pct": round(annual_return * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 3) if sharpe_ratio is not None else None,
        "beta_vs_sp500": round(beta, 3) if beta is not None else None,
        "historical_var_95_1day_pct": round(var_95 * 100, 2) if var_95 is not None else None,
    }


def run_risk_agent(state: ResearchState) -> ResearchState:
    ticker = state["ticker"]
    errors = list(state.get("errors", []))

    metrics = _compute_risk_metrics(ticker)
    if "error" in metrics:
        errors.append(metrics["error"])

    news = state.get("news_analysis", {})
    financial = state.get("financial_analysis", {})
    technical = state.get("technical_analysis", {})

    user_prompt = (
        f"Ticker: {ticker}\n\n"
        f"Quantitative risk metrics:\n{metrics}\n\n"
        f"News analysis summary: {news.get('summary', 'N/A')} "
        f"(sentiment: {news.get('sentiment', 'N/A')})\n\n"
        f"Financial analysis summary: {financial.get('summary', 'N/A')} "
        f"(financial_health: {financial.get('financial_health', 'N/A')})\n\n"
        f"Technical analysis summary: {technical.get('summary', 'N/A')} "
        f"(trend: {technical.get('trend', 'N/A')})"
    )

    analysis = gemini_service.ask_json(SYSTEM_PROMPT, user_prompt)
    analysis["metrics"] = metrics

    return {**state, "risk_analysis": analysis, "errors": errors}
