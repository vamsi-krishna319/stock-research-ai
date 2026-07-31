"""
Reports endpoints: browse previously generated research reports.
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from app.database.mongodb import reports_collection

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def list_reports(limit: int = 20, ticker: str | None = None):
    query = {"ticker": ticker.upper()} if ticker else {}
    cursor = reports_collection().find(query).sort("created_at", -1).limit(limit)
    reports = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        reports.append(doc)
    return {"reports": reports}


@router.get("/{report_id}")
def get_report(report_id: str):
    try:
        oid = ObjectId(report_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Invalid report_id") from exc

    doc = reports_collection().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    doc["_id"] = str(doc["_id"])
    return doc
