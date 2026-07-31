"""
FastAPI application entrypoint for the Multi-Agent Stock Market
Research Company backend.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.mongodb import init_indexes, ping
from app.routers import chat, portfolio, reports, research, upload, watchlist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Agent Stock Market Research Company API",
    description="LangGraph-orchestrated multi-agent financial research platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router)
app.include_router(portfolio.router)
app.include_router(watchlist.router)
app.include_router(reports.router)
app.include_router(upload.router)
app.include_router(chat.router)


@app.on_event("startup")
def on_startup():
    try:
        init_indexes()
        logger.info("MongoDB indexes ensured.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not initialize MongoDB indexes on startup: %s", exc)


@app.get("/")
def root():
    return {"message": "Multi-Agent Stock Market Research Company API is running."}


@app.get("/health")
def health():
    mongo_ok = ping()
    return {"status": "ok" if mongo_ok else "degraded", "mongodb_connected": mongo_ok}
