"""
Multi-Agent Stock Market Research Company - Streamlit Dashboard
Main landing page. Additional pages live in frontend/pages/.
"""
import streamlit as st

from utils.api_client import check_backend_health

st.set_page_config(
    page_title="Stock Research AI",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

st.title("Multi-Agent Stock Market Research Company")
st.caption(
    "An AI-powered virtual research firm: specialized agents analyze news, financial "
    "reports, technicals, and risk to produce data-driven investment research."
)

col1, col2 = st.columns([3, 1])
with col2:
    st.subheader("Backend Status")
    try:
        health = check_backend_health()
        if health.get("mongodb_connected"):
            st.success("Backend connected. MongoDB: OK")
        else:
            st.warning("Backend reachable, but MongoDB is not connected. Check MONGODB_URI.")
    except Exception:
        st.error("Cannot reach backend API. Is it running?")

with col1:
    st.markdown(
        """
### How it works
1. **Stock Research** — enter a ticker, and the Supervisor Agent runs the full
   pipeline: News Reader -> Financial Report Analyzer -> Technical Indicator Agent
   -> Risk Analyzer -> Portfolio Manager -> Investment Advisor -> Report Generator.
2. **Portfolio** — build a portfolio and get diversification / risk insights.
3. **Watchlist** — track tickers and generate daily research reports for all of them.
4. **Reports** — browse previously generated research reports.
5. **Chat Assistant** — ask follow-up questions grounded in ingested financial documents (RAG).

Use the sidebar to navigate between pages.
"""
    )

st.divider()
st.caption(
    "This platform generates AI-assisted research for informational and educational "
    "purposes only. It is not certified financial advice."
)
