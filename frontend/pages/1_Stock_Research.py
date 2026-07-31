"""Stock Research page: trigger the full multi-agent pipeline for a ticker."""
import pandas as pd
import streamlit as st

from utils.api_client import run_research, upload_pdf

st.set_page_config(page_title="Stock Research", layout="wide")
st.title("Stock Research")

with st.form("research_form"):
    col1, col2 = st.columns([2, 2])
    with col1:
        ticker = st.text_input("Stock Ticker", placeholder="e.g. AAPL, MSFT, TSLA").strip().upper()
    with col2:
        uploaded_file = st.file_uploader(
            "Optional: upload a financial report PDF (used if live SEC EDGAR fetch fails)",
            type=["pdf"],
        )
    submitted = st.form_submit_button("Run Research", type="primary")

if submitted:
    if not ticker:
        st.error("Please enter a ticker symbol.")
    else:
        uploaded_pdf_id = None
        if uploaded_file is not None:
            with st.spinner("Uploading and ingesting PDF..."):
                try:
                    upload_result = upload_pdf(ticker, uploaded_file.getvalue(), uploaded_file.name)
                    uploaded_pdf_id = upload_result["file_id"]
                    st.info(f"Uploaded PDF ingested: {upload_result['chunks_ingested']} chunks.")
                except Exception as exc:  # noqa: BLE001
                    st.warning(f"PDF upload failed, continuing without it: {exc}")

        with st.spinner(f"Running multi-agent research pipeline for {ticker}... this can take a minute."):
            try:
                result = run_research(ticker, uploaded_pdf_id=uploaded_pdf_id)
                st.session_state["last_research_result"] = result
            except Exception as exc:  # noqa: BLE001
                st.error(f"Research pipeline failed: {exc}")
                result = None

if "last_research_result" in st.session_state:
    result = st.session_state["last_research_result"]

    advisor = result.get("advisor_recommendation", {})
    rec = advisor.get("recommendation", "N/A")
    conf = advisor.get("confidence", "N/A")

    st.header(f"Results for {result.get('ticker')}")
    rec_color = {
        "strong_buy": "green", "buy": "green",
        "hold": "orange",
        "sell": "red", "strong_sell": "red",
    }.get(rec, "gray")
    st.markdown(f"### Recommendation: :{rec_color}[{rec.upper() if isinstance(rec, str) else rec}] (confidence: {conf})")
    st.write(advisor.get("rationale", ""))

    tab_news, tab_fin, tab_tech, tab_risk, tab_report = st.tabs(
        ["News & Sentiment", "Financial Report", "Technical Analysis", "Risk Assessment", "Full Report"]
    )

    with tab_news:
        news = result.get("news_analysis", {})
        st.metric("Sentiment", news.get("sentiment", "N/A"), delta=news.get("sentiment_score"))
        st.write(news.get("summary", ""))
        st.write("**Key themes:**", ", ".join(news.get("key_themes", []) or []))
        articles = news.get("articles", [])
        if articles:
            st.write("**Recent headlines:**")
            for a in articles[:8]:
                st.markdown(f"- [{a.get('title')}]({a.get('url')}) — {a.get('source')}")

    with tab_fin:
        fin = result.get("financial_analysis", {})
        st.write(f"**Financial health:** {fin.get('financial_health', 'N/A')}")
        st.write(f"**Source used:** {fin.get('source', 'N/A')}")
        st.write(fin.get("summary", ""))
        if fin.get("key_metrics_mentioned"):
            st.write("**Key metrics mentioned:**")
            for m in fin["key_metrics_mentioned"]:
                st.markdown(f"- {m}")
        if fin.get("risks_flagged"):
            st.write("**Risks flagged:**")
            for r in fin["risks_flagged"]:
                st.markdown(f"- {r}")

    with tab_tech:
        tech = result.get("technical_analysis", {})
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Trend", tech.get("trend", "N/A"))
        col_b.metric("Momentum", tech.get("momentum_signal", "N/A"))
        col_c.metric("Signal Strength", tech.get("signal_strength", "N/A"))
        st.write(tech.get("summary", ""))
        indicators = tech.get("indicators", {})
        history = indicators.get("recent_close_history")
        if history:
            df = pd.Series(history).sort_index()
            st.line_chart(df, height=300)
        st.json({k: v for k, v in indicators.items() if k != "recent_close_history"})

    with tab_risk:
        risk = result.get("risk_analysis", {})
        st.write(f"**Risk rating:** {risk.get('risk_rating', 'N/A')}")
        st.write(risk.get("summary", ""))
        metrics = risk.get("metrics", {})
        if metrics:
            st.write("**Quantitative metrics:**")
            st.json(metrics)
        if risk.get("key_risk_factors"):
            st.write("**Key risk factors:**")
            for f in risk["key_risk_factors"]:
                st.markdown(f"- {f}")

    with tab_report:
        st.markdown(result.get("report_markdown", "No report generated."))

    if result.get("errors"):
        with st.expander("Pipeline warnings / fallback notes"):
            for e in result["errors"]:
                st.write(f"- {e}")
