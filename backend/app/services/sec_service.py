"""
SEC EDGAR access.

Strategy:
    1. Resolve ticker -> CIK using SEC's company_tickers.json
    2. Pull the company's recent filings index (10-K / 10-Q) via the
       EDGAR "submissions" API
    3. Fetch the primary document of the most recent 10-K/10-Q and
       return its raw text (HTML is stripped down to text)

If any step fails (ticker not covered, network issue, filing not
parseable), the caller should fall back to a manually uploaded PDF
(handled by the financial_report_agent).
"""
import logging
import re

import requests

from app.config import settings

logger = logging.getLogger(__name__)

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

_ticker_cik_cache: dict[str, str] | None = None


def _headers():
    return {"User-Agent": settings.SEC_USER_AGENT}


def _load_ticker_cik_map() -> dict[str, str]:
    global _ticker_cik_cache
    if _ticker_cik_cache is not None:
        return _ticker_cik_cache
    try:
        resp = requests.get(TICKERS_URL, headers=_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        mapping = {}
        for entry in data.values():
            mapping[entry["ticker"].upper()] = str(entry["cik_str"]).zfill(10)
        _ticker_cik_cache = mapping
        return mapping
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load SEC ticker->CIK map: %s", exc)
        _ticker_cik_cache = {}
        return {}


def get_cik(ticker: str) -> str | None:
    mapping = _load_ticker_cik_map()
    return mapping.get(ticker.upper())


def get_latest_filing_text(ticker: str, max_chars: int = 40000) -> dict:
    """
    Returns dict: {success, form_type, filing_date, text, source_url}
    On failure, {success: False, reason: "..."}
    """
    cik = get_cik(ticker)
    if not cik:
        return {"success": False, "reason": f"No CIK found for ticker {ticker}"}

    try:
        resp = requests.get(SUBMISSIONS_URL.format(cik=cik), headers=_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        filing_dates = recent.get("filingDate", [])

        target_idx = None
        for i, form in enumerate(forms):
            if form in ("10-K", "10-Q"):
                target_idx = i
                break

        if target_idx is None:
            return {"success": False, "reason": "No 10-K/10-Q filings found"}

        accession = accession_numbers[target_idx].replace("-", "")
        primary_doc = primary_docs[target_idx]
        form_type = forms[target_idx]
        filing_date = filing_dates[target_idx]

        doc_url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}"
        )
        doc_resp = requests.get(doc_url, headers=_headers(), timeout=20)
        doc_resp.raise_for_status()

        text = _strip_html(doc_resp.text)
        return {
            "success": True,
            "form_type": form_type,
            "filing_date": filing_date,
            "text": text[:max_chars],
            "source_url": doc_url,
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("SEC EDGAR fetch failed for %s: %s", ticker, exc)
        return {"success": False, "reason": str(exc)}


def _strip_html(html: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
