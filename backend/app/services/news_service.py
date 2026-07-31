"""
NewsAPI (https://newsapi.org) wrapper for fetching recent news
articles related to a stock ticker / company.
"""
import logging
from datetime import datetime, timedelta

import requests

from app.config import settings

logger = logging.getLogger(__name__)

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"


def fetch_news(query: str, days_back: int = 7, page_size: int = 10) -> list[dict]:
    """
    Fetch recent news articles mentioning `query` (typically the
    ticker and/or company name). Returns a list of simplified
    article dicts: {title, description, source, url, published_at}.
    """
    if not settings.NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY not set; skipping live news fetch.")
        return []

    from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": page_size,
        "apiKey": settings.NEWSAPI_KEY,
    }
    try:
        resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        return [
            {
                "title": a.get("title"),
                "description": a.get("description"),
                "source": (a.get("source") or {}).get("name"),
                "url": a.get("url"),
                "published_at": a.get("publishedAt"),
            }
            for a in articles
        ]
    except requests.RequestException as exc:
        logger.error("NewsAPI request failed: %s", exc)
        return []
