"""Chat Assistant page: ask follow-up questions grounded in ingested documents (RAG)."""
import uuid

import streamlit as st

from utils.api_client import send_chat_message

st.set_page_config(page_title="Chat Assistant", layout="wide")
st.title("Financial Research Chat Assistant")
st.caption(
    "Ask questions about tickers you've researched. Answers are grounded in financial "
    "documents (SEC filings / uploaded PDFs) ingested into the RAG knowledge base."
)

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = uuid.uuid4().hex

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

ticker_context = st.text_input(
    "Optional ticker context (limits retrieval to this ticker's documents)", placeholder="e.g. AAPL"
).strip().upper()

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ask a question about a stock or financial report...")

if user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = send_chat_message(
                    st.session_state.chat_session_id, user_input, ticker_context or None
                )
                reply = result.get("reply", "No response.")
            except Exception as exc:  # noqa: BLE001
                reply = f"Chat request failed: {exc}"
            st.write(reply)

    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
