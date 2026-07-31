"""Watchlist page: track tickers and generate daily reports for all of them."""
import streamlit as st

from utils.api_client import generate_daily_reports, get_watchlist, save_watchlist

st.set_page_config(page_title="Watchlist", layout="wide")
st.title("Watchlist")

USER_ID = "default_user"

if "watchlist_tickers" not in st.session_state:
    try:
        existing = get_watchlist(USER_ID)
        st.session_state.watchlist_tickers = [t["ticker"] for t in existing.get("tickers", [])]
    except Exception:
        st.session_state.watchlist_tickers = []

st.subheader("Manage Tickers")

new_ticker = st.text_input("Add a ticker", placeholder="e.g. NVDA").strip().upper()
if st.button("Add to Watchlist"):
    if new_ticker and new_ticker not in st.session_state.watchlist_tickers:
        st.session_state.watchlist_tickers.append(new_ticker)
        st.rerun()

if st.session_state.watchlist_tickers:
    st.write("**Current watchlist:**")
    for t in list(st.session_state.watchlist_tickers):
        c1, c2 = st.columns([4, 1])
        c1.write(t)
        if c2.button("Remove", key=f"remove_watch_{t}"):
            st.session_state.watchlist_tickers.remove(t)
            st.rerun()
else:
    st.info("Your watchlist is empty. Add a ticker above.")

if st.button("Save Watchlist", type="primary"):
    tickers_payload = [{"ticker": t, "note": None} for t in st.session_state.watchlist_tickers]
    try:
        res = save_watchlist(USER_ID, tickers_payload)
        st.success(f"Watchlist saved ({res['ticker_count']} tickers).")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to save watchlist: {exc}")

st.divider()
st.subheader("Daily Report Generation")
st.caption(
    "Runs the full multi-agent research pipeline for every ticker on your saved "
    "watchlist and stores fresh reports. This can take a while for large watchlists."
)
if st.button("Generate Daily Reports Now"):
    with st.spinner("Running research pipeline across your watchlist..."):
        try:
            result = generate_daily_reports(USER_ID)
            st.success("Daily report generation complete.")
            st.json(result)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Daily report generation failed: {exc}")
