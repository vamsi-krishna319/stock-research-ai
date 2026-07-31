"""
Technical Indicator Agent
--------------------------
Pulls OHLCV history from Yahoo Finance, computes indicators with
pandas-ta, and asks Gemini to interpret the signal.
"""
import logging

from app.agents.state import ResearchState
from app.services import gemini_service
from app.services.indicator_service import compute_indicators
from app.services.yfinance_service import get_history

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a technical analysis agent inside a stock research system.
Given computed technical indicators (RSI, MACD, moving averages, Bollinger Bands, ADX),
produce a JSON object with:
{
  "trend": "bullish" | "bearish" | "sideways",
  "momentum_signal": "overbought" | "oversold" | "neutral",
  "signal_strength": "strong" | "moderate" | "weak",
  "summary": "<3-4 sentence plain-English interpretation of the indicators>"
}"""


def run_technical_agent(state: ResearchState) -> ResearchState:
    ticker = state["ticker"]
    errors = list(state.get("errors", []))

    history = get_history(ticker, period="6mo", interval="1d")
    indicators = compute_indicators(history)

    if "error" in indicators:
        errors.append(f"Technical indicator computation issue: {indicators['error']}")

    user_prompt = f"Ticker: {ticker}\n\nIndicators:\n{indicators}"
    analysis = gemini_service.ask_json(SYSTEM_PROMPT, user_prompt)
    analysis["indicators"] = indicators

    # return {**state, "technical_analysis": analysis, "errors": errors}
    return {
    "technical_analysis": analysis,
    # "errors": errors,
  }
