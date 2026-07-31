"""
Thin HTTP client wrapping the FastAPI backend endpoints, used by
all Streamlit pages.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 120


def run_research(ticker: str, uploaded_pdf_id: str | None = None, user_id: str = "default_user") -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/api/research",
        json={"ticker": ticker, "uploaded_pdf_id": uploaded_pdf_id, "user_id": user_id},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_research_history(ticker: str, limit: int = 10) -> dict:
    resp = requests.get(f"{BACKEND_URL}/api/research/{ticker}/history", params={"limit": limit}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def upload_pdf(ticker: str, file_bytes: bytes, filename: str) -> dict:
    files = {"file": (filename, file_bytes, "application/pdf")}
    data = {"ticker": ticker}
    resp = requests.post(f"{BACKEND_URL}/api/upload", files=files, data=data, timeout=60)
    resp.raise_for_status()
    return resp.json()


def create_portfolio(user_id: str, name: str, holdings: list[dict]) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/api/portfolio",
        json={"user_id": user_id, "name": name, "holdings": holdings},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def list_portfolios(user_id: str) -> dict:
    resp = requests.get(f"{BACKEND_URL}/api/portfolio/{user_id}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def analyze_portfolio(holdings: list[dict]) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/api/portfolio/analyze", json={"holdings": holdings}, timeout=DEFAULT_TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()


def save_watchlist(user_id: str, tickers: list[dict]) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/api/watchlist", json={"user_id": user_id, "tickers": tickers}, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def get_watchlist(user_id: str) -> dict:
    resp = requests.get(f"{BACKEND_URL}/api/watchlist/{user_id}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def generate_daily_reports(user_id: str) -> dict:
    resp = requests.post(f"{BACKEND_URL}/api/watchlist/{user_id}/daily-reports", timeout=600)
    resp.raise_for_status()
    return resp.json()


def list_reports(ticker: str | None = None, limit: int = 20) -> dict:
    params = {"limit": limit}
    if ticker:
        params["ticker"] = ticker
    resp = requests.get(f"{BACKEND_URL}/api/reports", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_report(report_id: str) -> dict:
    resp = requests.get(f"{BACKEND_URL}/api/reports/{report_id}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_chat_message(session_id: str, message: str, ticker_context: str | None = None) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/api/chat",
        json={"session_id": session_id, "message": message, "ticker_context": ticker_context},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def check_backend_health() -> dict:
    resp = requests.get(f"{BACKEND_URL}/health", timeout=10)
    resp.raise_for_status()
    return resp.json()
