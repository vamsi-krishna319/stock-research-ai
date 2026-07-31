"""
News Reader Agent
-----------------
Fetches recent news for the ticker via NewsAPI, then asks Gemini
to summarize overall sentiment and key themes.
"""
import logging

from app.agents.state import ResearchState
from app.services import gemini_service, news_service
from app.services.yfinance_service import get_company_info

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a financial news analyst agent inside a stock research system.
Given a list of recent news headlines/descriptions about a company, produce a JSON object with:
{
  "sentiment": "positive" | "neutral" | "negative",
  "sentiment_score": <float from -1.0 (very negative) to 1.0 (very positive)>,
  "key_themes": [<short strings>],
  "summary": "<2-4 sentence plain-English summary of what's happening>"
}
Base your analysis only on the provided articles. If no articles are provided, say so honestly
in the summary and set sentiment to "neutral" with sentiment_score 0.0."""


def run_news_agent(state: ResearchState) -> ResearchState:
    ticker = state["ticker"]
    errors = list(state.get("errors", []))

    company_info = get_company_info(ticker)
    company_name = company_info.get("shortName") or ticker
    query = f"{ticker} OR \"{company_name}\""

    articles = news_service.fetch_news(query)

    if not articles:
        articles_text = "No recent articles were retrieved."
    else:
        articles_text = "\n".join(
            f"- {a['title']} ({a['source']}, {a['published_at']}): {a['description']}"
            for a in articles
            if a.get("title")
        )

    user_prompt = f"Ticker: {ticker}\nCompany: {company_name}\n\nRecent articles:\n{articles_text}"

    analysis = gemini_service.ask_json(SYSTEM_PROMPT, user_prompt)
    analysis["articles"] = articles

    # return {**state, "news_analysis": analysis, "errors": errors}
    return {
    "news_analysis": analysis,
    # "errors": errors,
    }
