"""
Chat endpoint: a RAG-backed conversational assistant that can
answer follow-up questions using previously ingested financial
documents in ChromaDB, with history persisted in MongoDB.
"""
from datetime import datetime

from fastapi import APIRouter

from app.database.mongodb import chat_history_collection
from app.models.schemas import ChatRequest, ChatResponse
from app.services import gemini_service, rag_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

SYSTEM_PROMPT = """You are a helpful financial research assistant embedded in a stock
research platform. Answer the user's question using the provided context excerpts from
ingested financial documents when relevant. If the context doesn't contain the answer,
say so honestly and answer from general financial knowledge, being clear about which is
which. Keep answers concise and avoid definitive "you should buy/sell" directives - frame
things as informational analysis."""


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    query = payload.message
    if payload.ticker_context:
        chunks = rag_service.retrieve_relevant_chunks(payload.ticker_context, query, n_results=4)
    else:
        chunks = rag_service.retrieve_any(query, n_results=4)

    context_text = "\n\n---\n\n".join(chunks) if chunks else "No relevant documents found."

    # Pull recent history for this session for conversational continuity
    history_cursor = (
        chat_history_collection()
        .find({"session_id": payload.session_id})
        .sort("created_at", -1)
        .limit(6)
    )
    history = list(history_cursor)[::-1]
    history_text = "\n".join(f"User: {h['message']}\nAssistant: {h['reply']}" for h in history)

    user_prompt = (
        f"Conversation history:\n{history_text}\n\n"
        f"Retrieved context:\n{context_text}\n\n"
        f"User question: {query}"
    )

    reply = gemini_service.ask(SYSTEM_PROMPT, user_prompt)

    chat_history_collection().insert_one(
        {
            "session_id": payload.session_id,
            "message": query,
            "reply": reply,
            "ticker_context": payload.ticker_context,
            "created_at": datetime.utcnow(),
        }
    )

    return ChatResponse(session_id=payload.session_id, reply=reply, sources=chunks[:3])
