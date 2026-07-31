"""
Yahoo Finance (via the `yfinance` package) data access helpers.
"""
import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def get_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Return OHLCV history as a DataFrame (empty DataFrame on failure)."""
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period=period, interval=interval)
        return hist
    except Exception as exc:  # noqa: BLE001
        logger.error("yfinance history fetch failed for %s: %s", ticker, exc)
        return pd.DataFrame()


def get_company_info(ticker: str) -> dict:
    """Return a simplified company info dict (sector, industry, market cap, etc.)."""
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        return {
            "shortName": info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "marketCap": info.get("marketCap"),
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "dividendYield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "longBusinessSummary": info.get("longBusinessSummary"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("yfinance info fetch failed for %s: %s", ticker, exc)
        return {}


def get_returns(ticker: str, period: str = "1y") -> pd.Series:
    """Daily percentage returns for a ticker, used for volatility/beta/Sharpe/VaR."""
    hist = get_history(ticker, period=period, interval="1d")
    if hist.empty or "Close" not in hist:
        return pd.Series(dtype=float)
    return hist["Close"].pct_change().dropna()
