"""
Portfolio endpoints: save/list portfolios and run the Portfolio
Manager agent standalone (without the full research pipeline).
"""
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.agents.portfolio_agent import run_portfolio_agent
from app.database.mongodb import portfolios_collection
from app.models.schemas import PortfolioAnalyzeRequest, PortfolioCreateRequest

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("")
def create_portfolio(payload: PortfolioCreateRequest):
    total_weight = sum(h.weight for h in payload.holdings)
    if round(total_weight, 2) != 1.0:
        raise HTTPException(
            status_code=400, detail=f"Holding weights must sum to 1.0 (got {total_weight})"
        )
    doc = {
        "user_id": payload.user_id,
        "name": payload.name,
        "holdings": [h.model_dump() for h in payload.holdings],
        "created_at": datetime.utcnow(),
    }
    result = portfolios_collection().insert_one(doc)
    return {"portfolio_id": str(result.inserted_id)}


@router.get("/{user_id}")
def list_portfolios(user_id: str):
    cursor = portfolios_collection().find({"user_id": user_id})
    portfolios = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        portfolios.append(doc)
    return {"portfolios": portfolios}


@router.post("/analyze")
def analyze_portfolio(payload: PortfolioAnalyzeRequest):
    state = {
        "ticker": "PORTFOLIO",
        "portfolio_holdings": [h.model_dump() for h in payload.holdings],
        "errors": [],
    }
    result_state = run_portfolio_agent(state)
    return result_state.get("portfolio_analysis", {})
