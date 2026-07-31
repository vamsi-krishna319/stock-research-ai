"""
Watchlist endpoints: manage tracked tickers and trigger the Daily
Report Generator agent (full pipeline) across the whole watchlist.
"""
import logging
from datetime import datetime

from fastapi import APIRouter

from app.agents.supervisor import run_research_pipeline
from app.database.mongodb import agent_outputs_collection, reports_collection, watchlists_collection
from app.models.schemas import WatchlistCreateRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.post("")
def save_watchlist(payload: WatchlistCreateRequest):
    doc = {
        "user_id": payload.user_id,
        "tickers": [t.model_dump() for t in payload.tickers],
        "updated_at": datetime.utcnow(),
    }
    watchlists_collection().update_one(
        {"user_id": payload.user_id}, {"$set": doc}, upsert=True
    )
    return {"status": "saved", "ticker_count": len(payload.tickers)}


@router.get("/{user_id}")
def get_watchlist(user_id: str):
    doc = watchlists_collection().find_one({"user_id": user_id})
    if not doc:
        return {"user_id": user_id, "tickers": []}
    doc["_id"] = str(doc["_id"])
    return doc


@router.post("/{user_id}/daily-reports")
def generate_daily_reports(user_id: str):
    """
    Run the full research pipeline for every ticker in the user's
    watchlist and persist a fresh daily report for each.
    """
    doc = watchlists_collection().find_one({"user_id": user_id})
    if not doc or not doc.get("tickers"):
        return {"status": "no_watchlist_tickers", "generated": []}

    generated = []
    for item in doc["tickers"]:
        ticker = item["ticker"]
        try:
            final_state = run_research_pipeline(ticker=ticker)
            created_at = datetime.utcnow()

            for agent_name in [
                "news_analysis",
                "financial_analysis",
                "technical_analysis",
                "risk_analysis",
                "portfolio_analysis",
                "advisor_recommendation",
            ]:
                agent_outputs_collection().insert_one(
                    {
                        "ticker": final_state["ticker"],
                        "agent_name": agent_name,
                        "output": final_state.get(agent_name, {}),
                        "created_at": created_at,
                    }
                )

            result = reports_collection().insert_one(
                {
                    "ticker": final_state["ticker"],
                    "user_id": user_id,
                    "report_markdown": final_state.get("report_markdown", ""),
                    "advisor_recommendation": final_state.get("advisor_recommendation", {}),
                    "errors": final_state.get("errors", []),
                    "created_at": created_at,
                    "daily_report": True,
                }
            )
            generated.append({"ticker": ticker, "report_id": str(result.inserted_id)})
        except Exception as exc:  # noqa: BLE001
            logger.exception("Daily report generation failed for %s", ticker)
            generated.append({"ticker": ticker, "error": str(exc)})

    return {"status": "completed", "generated": generated}
