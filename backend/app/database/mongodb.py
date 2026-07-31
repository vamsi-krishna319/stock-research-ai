"""
MongoDB Atlas connection and collection accessors.

Collections:
    users, portfolios, watchlists, reports, agent_outputs, chat_history
"""
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure

from app.config import settings

_client: MongoClient | None = None
_db = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=8000)
    return _client


def get_db():
    global _db
    if _db is None:
        _db = get_client()[settings.MONGODB_DB_NAME]
    return _db


def ping() -> bool:
    try:
        get_client().admin.command("ping")
        return True
    except ConnectionFailure:
        return False


def init_indexes():
    """Create useful indexes. Safe to call multiple times (idempotent)."""
    db = get_db()
    db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
    db.portfolios.create_index([("user_id", ASCENDING)])
    db.watchlists.create_index([("user_id", ASCENDING)])
    db.reports.create_index([("ticker", ASCENDING), ("created_at", ASCENDING)])
    db.agent_outputs.create_index([("ticker", ASCENDING), ("agent_name", ASCENDING)])
    db.chat_history.create_index([("session_id", ASCENDING), ("created_at", ASCENDING)])


# ---- Convenience collection accessors ----
def users_collection():
    return get_db().users


def portfolios_collection():
    return get_db().portfolios


def watchlists_collection():
    return get_db().watchlists


def reports_collection():
    return get_db().reports


def agent_outputs_collection():
    return get_db().agent_outputs


def chat_history_collection():
    return get_db().chat_history
