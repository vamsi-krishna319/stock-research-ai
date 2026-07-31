"""
Daily Report Generator Agent
------------------------------
Produces the final, human-readable Markdown research report by
combining every upstream agent's output using Gemini Pro.
"""
import logging

from app.agents.state import ResearchState
from app.services import gemini_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Daily Report Generator agent in a multi-agent stock research
system. Combine the structured outputs from all specialist agents into a single, well
organized Markdown research report for a retail investor. Use headings for each section:

# Stock Research Report: <TICKER>
## Executive Summary
## News & Sentiment Analysis
## Financial Report Analysis
## Technical Analysis
## Risk Assessment
## Portfolio Considerations (only include if portfolio data was provided)
## Investment Recommendation
## Disclaimer

Keep it concise but information-dense. Do not invent data not present in the inputs.
End with a short disclaimer that this is AI-generated research for informational
purposes only and not certified financial advice. Respond with plain Markdown text only
(no JSON, no code fences)."""


def run_report_agent(state: ResearchState) -> ResearchState:
    ticker = state["ticker"]
    errors = list(state.get("errors", []))

    user_prompt = (
        f"Ticker: {ticker}\n\n"
        f"News Analysis: {state.get('news_analysis', {})}\n\n"
        f"Financial Report Analysis: {state.get('financial_analysis', {})}\n\n"
        f"Technical Analysis: {state.get('technical_analysis', {})}\n\n"
        f"Risk Analysis: {state.get('risk_analysis', {})}\n\n"
        f"Portfolio Analysis: {state.get('portfolio_analysis', {})}\n\n"
        f"Advisor Recommendation: {state.get('advisor_recommendation', {})}"
    )

    report_markdown = gemini_service.ask(SYSTEM_PROMPT, user_prompt, use_pro=True)

    return {**state, "report_markdown": report_markdown, "errors": errors}
