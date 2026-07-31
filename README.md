# Multi-Agent Stock Market Research Company

An AI-powered multi-agent platform that automates stock research: news
sentiment, SEC financial report analysis (with RAG), technical indicators,
risk assessment, portfolio evaluation, and a final AI-generated investment
recommendation and research report.

## Architecture

```
Streamlit (frontend) -> FastAPI (backend) -> LangGraph Supervisor
                                                  |
        +------------------+------------------+  |
        |                  |                  |  |
   News Reader   Financial Report Agent   Technical Agent   (run in parallel)
        |                  |                  |
        +------------------+------------------+
                           |
                      Risk Analyzer  (fan-in)
                           |
                     Portfolio Manager
                           |
                    Investment Advisor
                           |
                 Daily Report Generator  ->  Gemini  ->  MongoDB
```

- **Frontend:** Streamlit
- **Backend:** FastAPI
- **Multi-agent framework:** LangGraph
- **Agent framework:** LangChain
- **LLM:** Gemini 2.5 Pro / Flash (via `langchain-google-genai`)
- **Vector DB (RAG):** ChromaDB, embeddings via Gemini Embeddings
- **Database:** MongoDB Atlas
- **Market data:** Yahoo Finance (`yfinance`)
- **News:** NewsAPI
- **Financial reports:** SEC EDGAR (live fetch) with manual PDF upload fallback
- **Technical analysis:** pandas-ta
- **PDF processing:** PyPDF
- **Containerization:** Docker / Docker Compose

## Project Structure

```
stock-research-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entrypoint
│   │   ├── config.py                # env-driven settings
│   │   ├── database/                # MongoDB + ChromaDB clients
│   │   ├── models/schemas.py        # Pydantic request/response models
│   │   ├── agents/                  # all LangGraph agents + supervisor graph
│   │   ├── services/                # Gemini, NewsAPI, yfinance, SEC EDGAR,
│   │   │                             # pandas-ta, PyPDF, RAG service wrappers
│   │   └── routers/                 # /api/research, /portfolio, /watchlist,
│   │                                 # /reports, /upload, /chat
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                       # Streamlit landing page
│   ├── pages/                       # multipage Streamlit app
│   ├── utils/api_client.py          # backend REST wrapper
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Prerequisites

1. **Gemini API key** — https://aistudio.google.com/app/apikey
2. **NewsAPI key** — https://newsapi.org/register
3. **MongoDB Atlas cluster** — https://www.mongodb.com/cloud/atlas
   - Create a free cluster, add a database user, and allow network access
     (add `0.0.0.0/0` for local testing, or your IP).
   - Copy the connection string (`mongodb+srv://...`).
4. **Docker + Docker Compose** (for the containerized run), or **Python 3.11+**
   (for running locally without Docker).

SEC EDGAR filings are fetched live and require no API key, only a descriptive
`SEC_USER_AGENT` (SEC's usage policy requires a real contact identifier).

## Setup

1. Copy the environment template and fill in your keys:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at minimum:
   - `GEMINI_API_KEY`
   - `NEWSAPI_KEY`
   - `MONGODB_URI` (your Atlas connection string)
   - `SEC_USER_AGENT` (e.g. `"MyResearchApp myemail@example.com"`)

### Option A — Run with Docker (recommended)

```bash
docker compose up --build
```

- Backend API: http://localhost:8000 (docs at http://localhost:8000/docs)
- Frontend dashboard: http://localhost:8501

### Option B — Run locally without Docker

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (in a second terminal):

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BACKEND_URL=http://localhost:8000   # Windows: set BACKEND_URL=...
streamlit run app.py
```

## Using the Platform

1. **Stock Research** page — enter a ticker (e.g. `AAPL`). Optionally upload a
   financial report PDF, used automatically if the live SEC EDGAR fetch for
   that ticker fails. The Supervisor Agent runs the full pipeline and displays
   news sentiment, financial analysis, technical indicators, risk metrics, the
   final recommendation, and a full Markdown research report.
2. **Portfolio** page — build a portfolio of tickers + weights, save it, and
   run the Portfolio Manager agent for diversification/correlation analysis.
3. **Watchlist** page — save a list of tickers and trigger daily research
   report generation across the whole watchlist in one click.
4. **Reports** page — browse all previously generated research reports.
5. **Chat Assistant** page — ask follow-up questions; answers are grounded via
   RAG over ingested SEC filings / uploaded PDFs stored in ChromaDB.

## MongoDB Collections

`users`, `portfolios`, `watchlists`, `reports`, `agent_outputs`, `chat_history`,
`uploaded_files` (upload metadata).

## ChromaDB

A single persistent collection (`financial_documents`) stores chunked text
from SEC filings and uploaded PDFs, tagged with `ticker` and `doc_type`
metadata, embedded with Gemini Embeddings, and used for RAG retrieval by the
Financial Report Agent and the Chat Assistant.

## Notes & Limitations

- SEC EDGAR fetch works for companies covered by SEC's `company_tickers.json`
  mapping (US-listed companies filing with the SEC). If it fails, upload a PDF
  filing manually via the Stock Research page.
- Gemini and NewsAPI calls will return graceful fallback messages if their
  respective API keys are not configured, so the app won't crash without keys
  — but the analysis quality will be limited until you add them.
- This platform produces AI-generated research for informational/educational
  purposes only and is **not** certified financial advice.
