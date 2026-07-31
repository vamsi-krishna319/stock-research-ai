"""
Upload endpoint: lets a user manually upload a financial report /
SEC filing PDF when live EDGAR fetch fails or isn't available for
a given ticker. The file is stored on disk, its metadata saved in
MongoDB, and its text ingested into ChromaDB for RAG.
"""
import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.database.mongodb import get_db
from app.models.schemas import UploadResponse
from app.services import rag_service
from app.services.pdf_service import extract_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["upload"])


def uploaded_files_collection():
    return get_db().uploaded_files


@router.post("", response_model=UploadResponse)
async def upload_pdf(ticker: str = Form(...), doc_type: str = Form("uploaded_pdf"), file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = uuid.uuid4().hex
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    text = extract_text(file_path)
    chunks_ingested = rag_service.ingest_document(
        ticker=ticker, text=text, doc_type=doc_type, source=safe_filename
    )

    uploaded_files_collection().insert_one(
        {
            "file_id": file_id,
            "filename": file.filename,
            "path": file_path,
            "ticker": ticker.upper(),
            "doc_type": doc_type,
            "chunks_ingested": chunks_ingested,
            "created_at": datetime.utcnow(),
        }
    )

    return UploadResponse(
        file_id=file_id, filename=file.filename, ticker=ticker.upper(), chunks_ingested=chunks_ingested
    )


def get_uploaded_pdf_path(file_id: str) -> str | None:
    doc = uploaded_files_collection().find_one({"file_id": file_id})
    return doc["path"] if doc else None
