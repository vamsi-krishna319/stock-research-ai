"""
Financial Report Analyzer Agent
--------------------------------
Attempts to fetch the latest 10-K/10-Q from SEC EDGAR. If that
fails (ticker not found, network issue, etc.), falls back to a
manually uploaded PDF filing (if supplied). The resulting text is
ingested into ChromaDB for RAG, then relevant chunks are retrieved
and summarized by Gemini.
"""
import logging

from app.agents.state import ResearchState
from app.services import gemini_service, rag_service, sec_service
from app.services.pdf_service import extract_text

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a financial statement analysis agent inside a stock research system.
You are given excerpts retrieved from a company's SEC filing (10-K/10-Q) or uploaded financial
report. Produce a JSON object with:
{
  "financial_health": "strong" | "moderate" | "weak" | "unknown",
  "key_metrics_mentioned": [<short strings, e.g. "Revenue grew 12% YoY">],
  "risks_flagged": [<short strings>],
  "summary": "<3-5 sentence summary of the company's financial position based on the excerpts>"
}
If the excerpts are empty or insufficient, say so honestly and set financial_health to "unknown"."""


def run_financial_report_agent(state: ResearchState) -> ResearchState:
    ticker = state["ticker"]
    errors = list(state.get("errors", []))
    uploaded_pdf_path = state.get("uploaded_pdf_path")

    ingested_chunks = 0
    source_used = None

    # 1. Try live SEC EDGAR fetch
    edgar_result = sec_service.get_latest_filing_text(ticker)
    if edgar_result.get("success"):
        ingested_chunks = rag_service.ingest_document(
            ticker=ticker,
            text=edgar_result["text"],
            doc_type=edgar_result["form_type"],
            source=edgar_result["source_url"],
        )
        source_used = f"SEC EDGAR {edgar_result['form_type']} ({edgar_result['filing_date']})"
    else:
        errors.append(f"SEC EDGAR fetch failed: {edgar_result.get('reason')}")

        # 2. Fallback: manually uploaded PDF
        if uploaded_pdf_path:
            text = extract_text(uploaded_pdf_path)
            ingested_chunks = rag_service.ingest_document(
                ticker=ticker, text=text, doc_type="uploaded_pdf", source=uploaded_pdf_path
            )
            source_used = f"Uploaded PDF ({uploaded_pdf_path})"
        else:
            errors.append("No uploaded PDF provided as fallback for financial report analysis.")

    # 3. Retrieve most relevant chunks (whether newly ingested or from a prior ingestion)
    relevant_chunks = rag_service.retrieve_relevant_chunks(
        ticker, query="revenue growth profitability risk financial condition", n_results=6
    )

    if relevant_chunks:
        excerpts_text = "\n\n---\n\n".join(relevant_chunks)
    else:
        excerpts_text = "No financial document excerpts are available for this ticker."

    user_prompt = f"Ticker: {ticker}\nSource: {source_used or 'none'}\n\nExcerpts:\n{excerpts_text}"
    analysis = gemini_service.ask_json(SYSTEM_PROMPT, user_prompt)
    analysis["source"] = source_used
    analysis["chunks_ingested_this_run"] = ingested_chunks

    # return {**state, "financial_analysis": analysis, "errors": errors}
    return {
    "financial_analysis": analysis,
    # "errors": errors,
    }
