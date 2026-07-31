"""
Research endpoints: trigger the multi-agent LangGraph pipeline
for a given ticker and persist agent outputs + the final report.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.agents.supervisor import run_research_pipeline
from app.database.mongodb import agent_outputs_collection, reports_collection
from app.models.schemas import ResearchRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("")
def run_research(payload: ResearchRequest):
    if not payload.ticker or not payload.ticker.strip():
        raise HTTPException(status_code=400, detail="ticker is required")

    uploaded_pdf_path = None
    if payload.uploaded_pdf_id:
        from app.routers.upload import get_uploaded_pdf_path

        uploaded_pdf_path = get_uploaded_pdf_path(payload.uploaded_pdf_id)

    try:
        final_state = run_research_pipeline(
            ticker=payload.ticker, uploaded_pdf_path=uploaded_pdf_path
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Research pipeline failed")
        raise HTTPException(status_code=500, detail=f"Research pipeline failed: {exc}") from exc

    created_at = datetime.utcnow()

    # Persist each agent's raw output (agent_outputs collection)
    agent_names = [
        "news_analysis",
        "financial_analysis",
        "technical_analysis",
        "risk_analysis",
        "portfolio_analysis",
        "advisor_recommendation",
    ]
    for agent_name in agent_names:
        agent_outputs_collection().insert_one(
            {
                "ticker": final_state["ticker"],
                "agent_name": agent_name,
                "output": final_state.get(agent_name, {}),
                "created_at": created_at,
            }
        )

    # Persist the final report (reports collection)
    report_doc = {
        "ticker": final_state["ticker"],
        "user_id": payload.user_id,
        "report_markdown": final_state.get("report_markdown", ""),
        "advisor_recommendation": final_state.get("advisor_recommendation", {}),
        "errors": final_state.get("errors", []),
        "created_at": created_at,
    }
    result = reports_collection().insert_one(report_doc)

    return {
        "ticker": final_state["ticker"],
        "news_analysis": final_state.get("news_analysis", {}),
        "financial_analysis": final_state.get("financial_analysis", {}),
        "technical_analysis": final_state.get("technical_analysis", {}),
        "risk_analysis": final_state.get("risk_analysis", {}),
        "portfolio_analysis": final_state.get("portfolio_analysis", {}),
        "advisor_recommendation": final_state.get("advisor_recommendation", {}),
        "report_markdown": final_state.get("report_markdown", ""),
        "report_id": str(result.inserted_id),
        "created_at": created_at,
        "errors": final_state.get("errors", []),
    }


@router.get("/{ticker}/history")
def get_research_history(ticker: str, limit: int = 10):
    cursor = (
        reports_collection()
        .find({"ticker": ticker.upper()})
        .sort("created_at", -1)
        .limit(limit)
    )
    reports = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        reports.append(doc)
    return {"ticker": ticker.upper(), "reports": reports}
