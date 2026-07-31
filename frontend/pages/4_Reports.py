"""Reports page: browse previously generated research reports."""
import streamlit as st

from utils.api_client import get_report, list_reports

st.set_page_config(page_title="Reports", layout="wide")
st.title("Research Reports History")

filter_ticker = st.text_input("Filter by ticker (optional)", placeholder="e.g. AAPL").strip().upper()

try:
    data = list_reports(ticker=filter_ticker or None)
    reports = data.get("reports", [])
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load reports: {exc}")
    reports = []

if not reports:
    st.info("No reports found yet. Run a stock research first.")
else:
    for r in reports:
        rec = r.get("advisor_recommendation", {}).get("recommendation", "N/A")
        label = f"{r.get('ticker')} — {r.get('created_at')} — recommendation: {rec}"
        with st.expander(label):
            st.markdown(r.get("report_markdown", "No content."))
            if r.get("errors"):
                st.caption("Warnings: " + "; ".join(r["errors"]))
