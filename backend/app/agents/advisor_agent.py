"""
Investment Advisor Agent
-------------------------
Synthesizes all upstream agent outputs (news, financial, technical,
risk, portfolio) into a final buy/hold/sell recommendation using
the stronger Gemini Pro model.
"""
import logging

from app.agents.state import ResearchState
from app.services import gemini_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the lead Investment Advisor agent in a multi-agent stock research
system. You receive structured analysis from specialist agents (news sentiment, financial
report analysis, technical analysis, risk assessment, and optionally portfolio analysis).
Synthesize these into a final JSON object:
{
  "recommendation": "strong_buy" | "buy" | "hold" | "sell" | "strong_sell",
  "confidence": "low" | "medium" | "high",
  "rationale": "<4-6 sentence explanation citing specific points from each agent>",
  "key_positives": [<short strings>],
  "key_risks": [<short strings>],
  "suggested_time_horizon": "short_term" | "medium_term" | "long_term"
}
This is for educational/informational research purposes, not certified financial advice -
keep that framing implicit in tone (measured, not overconfident)."""


def run_advisor_agent(state: ResearchState) -> ResearchState:
    ticker = state["ticker"]
    errors = list(state.get("errors", []))

    news = state.get("news_analysis", {})
    financial = state.get("financial_analysis", {})
    technical = state.get("technical_analysis", {})
    risk = state.get("risk_analysis", {})
    portfolio = state.get("portfolio_analysis", {})

    user_prompt = (
        f"Ticker: {ticker}\n\n"
        f"News Analysis: {news}\n\n"
        f"Financial Report Analysis: {financial}\n\n"
        f"Technical Analysis: {technical}\n\n"
        f"Risk Analysis: {risk}\n\n"
        f"Portfolio Analysis: {portfolio}"
    )

    analysis = gemini_service.ask_json(SYSTEM_PROMPT, user_prompt, use_pro=True)

    return {**state, "advisor_recommendation": analysis, "errors": errors}
