"""Portfolio page: build a portfolio and run diversification/risk analysis."""
import pandas as pd
import streamlit as st

from utils.api_client import analyze_portfolio, create_portfolio, list_portfolios

st.set_page_config(page_title="Portfolio", layout="wide")
st.title("Portfolio Manager")

USER_ID = "default_user"

if "holdings" not in st.session_state:
    st.session_state.holdings = [{"ticker": "", "weight": 0.0}]

st.subheader("Build Your Portfolio")

for i, holding in enumerate(st.session_state.holdings):
    c1, c2, c3 = st.columns([2, 2, 1])
    holding["ticker"] = c1.text_input(
        f"Ticker #{i + 1}", value=holding["ticker"], key=f"ticker_{i}"
    ).strip().upper()
    holding["weight"] = c2.number_input(
        f"Weight #{i + 1} (0-1)", min_value=0.0, max_value=1.0, value=holding["weight"], step=0.05, key=f"weight_{i}"
    )
    if c3.button("Remove", key=f"remove_{i}") and len(st.session_state.holdings) > 1:
        st.session_state.holdings.pop(i)
        st.rerun()

if st.button("Add Holding"):
    st.session_state.holdings.append({"ticker": "", "weight": 0.0})
    st.rerun()

total_weight = sum(h["weight"] for h in st.session_state.holdings)
st.write(f"Total weight: **{round(total_weight, 2)}** (should sum to 1.0)")

col_save, col_analyze = st.columns(2)

with col_save:
    portfolio_name = st.text_input("Portfolio name (for saving)", value="My Portfolio")
    if st.button("Save Portfolio"):
        holdings = [h for h in st.session_state.holdings if h["ticker"]]
        if round(total_weight, 2) != 1.0:
            st.error("Weights must sum to 1.0 to save.")
        else:
            try:
                res = create_portfolio(USER_ID, portfolio_name, holdings)
                st.success(f"Portfolio saved (id: {res['portfolio_id']})")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Failed to save portfolio: {exc}")

with col_analyze:
    st.write(" ")
    st.write(" ")
    if st.button("Analyze Portfolio", type="primary"):
        holdings = [h for h in st.session_state.holdings if h["ticker"]]
        if not holdings:
            st.error("Add at least one holding.")
        else:
            with st.spinner("Running Portfolio Manager agent..."):
                try:
                    analysis = analyze_portfolio(holdings)
                    st.session_state["portfolio_analysis"] = analysis
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Portfolio analysis failed: {exc}")

if "portfolio_analysis" in st.session_state:
    analysis = st.session_state["portfolio_analysis"]
    st.divider()
    st.subheader("Analysis Results")
    st.write(f"**Diversification rating:** {analysis.get('diversification_rating', 'N/A')}")
    st.write(analysis.get("summary", ""))
    st.write(analysis.get("sector_concentration_commentary", ""))
    st.write(analysis.get("correlation_commentary", ""))

    sector_weights = analysis.get("sector_weights", {})
    if sector_weights:
        st.write("**Sector allocation:**")
        st.bar_chart(pd.Series(sector_weights))

    correlation_matrix = analysis.get("correlation_matrix", {})
    if correlation_matrix:
        st.write("**Return correlation matrix:**")
        st.dataframe(pd.DataFrame(correlation_matrix))

st.divider()
st.subheader("Saved Portfolios")
try:
    saved = list_portfolios(USER_ID)
    for p in saved.get("portfolios", []):
        with st.expander(p.get("name", "Unnamed")):
            st.json(p.get("holdings", []))
except Exception as exc:  # noqa: BLE001
    st.info(f"Could not load saved portfolios: {exc}")
