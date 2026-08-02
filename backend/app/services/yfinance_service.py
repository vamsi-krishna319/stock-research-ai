"""
Yahoo Finance (via the `yfinance` package) data access helpers.

Yahoo Finance aggressively rate-limits/blocks traffic that looks like a bot,
which is especially common when running from a cloud host (Render, Heroku,
AWS, etc.) where many different apps share the same outbound IP addresses.
To make this resilient, this module:

  1. Uses a curl_cffi session that impersonates a real Chrome browser's TLS
     fingerprint (the current recommended workaround from yfinance's own
     maintainers/community for avoiding Yahoo's bot detection).
  2. Retries transient failures (429 / rate-limit errors) a few times with
     exponential backoff + jitter instead of failing on the first hit.
  3. Caches results for a short time (in-process, TTL-based) so multiple
     agents in the same research run - and multiple research runs close
     together - don't refetch identical data (e.g. every ticker's risk
     calculation re-pulling the same ^GSPC benchmark history).

If Yahoo still blocks a request after all retries, functions fall back to
returning empty data (empty DataFrame / dict / Series) rather than raising,
so the pipeline degrades gracefully instead of crashing.
"""
import logging
import threading
import time

import pandas as pd
import yfinance as yf
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 15 * 60  # 15 minutes - reused across agents/tickers within this window

_cache_lock = threading.Lock()
_cache: dict[str, tuple[float, object]] = {}

_session = None
_session_lock = threading.Lock()


def _get_session():
    """
    Lazily build a single shared curl_cffi session that impersonates Chrome's
    TLS/HTTP fingerprint, which meaningfully reduces Yahoo Finance's rate
    limiting/bot-blocking compared to yfinance's default requests session.
    Falls back to yfinance's default (no custom session) if curl_cffi isn't
    installed for any reason.
    """
    global _session
    if _session is not None:
        return _session
    with _session_lock:
        if _session is None:
            try:
                from curl_cffi import requests as curl_requests

                _session = curl_requests.Session(impersonate="chrome")
            except Exception as exc:  # noqa: BLE001
                logger.warning("curl_cffi session unavailable, using default: %s", exc)
                _session = False  # sentinel meaning "no custom session"
    return _session


def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            _cache.pop(key, None)
            return None
        return value


def _cache_set(key: str, value):
    with _cache_lock:
        _cache[key] = (time.time() + CACHE_TTL_SECONDS, value)


def _is_rate_limit_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return "rate limit" in message or "too many requests" in message or "429" in message


def _ticker(symbol: str) -> yf.Ticker:
    session = _get_session()
    if session:
        return yf.Ticker(symbol, session=session)
    return yf.Ticker(symbol)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=2, max=20),
    retry=retry_if_exception(_is_rate_limit_error),
    reraise=True,
)
def _fetch_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    tk = _ticker(ticker)
    return tk.history(period=period, interval=interval)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=2, max=20),
    retry=retry_if_exception(_is_rate_limit_error),
    reraise=True,
)
def _fetch_info(ticker: str) -> dict:
    tk = _ticker(ticker)
    return tk.info or {}


def get_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Return OHLCV history as a DataFrame (empty DataFrame on failure)."""
    cache_key = f"history:{ticker.upper()}:{period}:{interval}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        hist = _fetch_history(ticker, period, interval)
        _cache_set(cache_key, hist)
        return hist
    except Exception as exc:  # noqa: BLE001
        logger.error("yfinance history fetch failed for %s: %s", ticker, exc)
        return pd.DataFrame()


def get_company_info(ticker: str) -> dict:
    """Return a simplified company info dict (sector, industry, market cap, etc.)."""
    cache_key = f"info:{ticker.upper()}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        info = _fetch_info(ticker)
        result = {
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
        _cache_set(cache_key, result)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.error("yfinance info fetch failed for %s: %s", ticker, exc)
        return {}


def get_returns(ticker: str, period: str = "1y") -> pd.Series:
    """Daily percentage returns for a ticker, used for volatility/beta/Sharpe/VaR."""
    hist = get_history(ticker, period=period, interval="1d")
    if hist.empty or "Close" not in hist:
        return pd.Series(dtype=float)
    return hist["Close"].pct_change().dropna()
