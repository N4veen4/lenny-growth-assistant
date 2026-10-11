# Lenny Growth Assistant - Backend API

The backend is a high-performance Python application built with **FastAPI**, **SQLAlchemy**, and the **Pi Coding Agent** framework. It orchestrates a RAG (Retrieval-Augmented Generation) pipeline over Lenny Rachitsky's podcast and newsletter transcripts, supports seamless runtime switching between local models (Ollama) and cloud models (OpenRouter), streams conversational responses via Server-Sent Events (SSE), and includes a writing skill that extracts structured essays into dedicated artifacts.

---

## 🛠️ Key Architectural Components

- **Agent Orchestrator:** Powered by `pi-coding-agent` with ReAct tool loops, structured message transcripts, and provider-agnostic LLM execution.
- **Dual LLM Providers:**
  - **Local:** Ollama (default: `llama3`, with automatic capability detection for tool calling).
  - **Cloud:** OpenRouter (e.g., `meta-llama/llama-3.3-70b-instruct:free`, `anthropic/claude-3.5-sonnet`, etc.).
- **RAG & Vector Retrieval:**
  - Semantic vector search with cosine similarity.
  - Hybrid embeddings support (`nomic-embed-text` via Ollama or `sentence-transformers/all-MiniLM-L6-v2` locally).
  - Primary vector store in PostgreSQL (`pgvector`), with automatic in-memory fallback for local development without Docker.
  - Startup auto-ingestion of transcripts in `backend/data/transcripts/`.
- **Writing Skill & Artifacts:**
  - Detects requests for essays, teardowns, guides, and strategic briefs.
  - Extracts structured `<antArtifact>` tags into separate database models and UI viewports.
- **Database & Persistence:**
  - PostgreSQL / SQLite with SQLAlchemy 2.0 ORM and Alembic migrations.
  - Full relational history for conversations, messages, citations, and artifacts.

---

## 📋 Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (optional, recommended for PostgreSQL)
- **Ollama** (optional, for local LLM inference)

---

## 🚀 Setup & Installation

### 1. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Key configuration settings:
- `DEFAULT_LLM_PROVIDER`: `local` or `cloud`
- `OLLAMA_BASE_URL`: Defaults to `http://localhost:11434`
- `OLLAMA_MODEL_NAME`: Defaults to `llama3`
- `OPENROUTER_API_KEY`: Your OpenRouter API key (if using cloud provider)
- `OPENROUTER_MODEL`: Defaults to `meta-llama/llama-3.3-70b-instruct:free`
- `DATABASE_URL`: Connection string for PostgreSQL (falls back to local SQLite automatically if PostgreSQL is unreachable)

---

## 🗄️ Database Setup & Migrations

### Option A: Using Docker (Recommended)
From the project root:
```powershell
docker-compose up -d db
```

### Option B: Local Fallback
If PostgreSQL is not running, the application automatically initializes a local SQLite database (`lenny_assistant.db`) so development and testing can proceed seamlessly.

### Run Alembic Migrations
```powershell
alembic upgrade head
```

---

## 🏃 Running the Server

Start the development server with auto-reload:
```powershell
uvicorn app.main:app --reload --port 8000
```
- **API Base URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`

---

## 🧪 Running Tests & Benchmarks

### Run Automated Tests (Pytest)
```powershell
pytest -v
```

### Run Latency & Quality Benchmarks
```powershell
python benchmark.py
```

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service liveness check |
| `GET` | `/api/v1/health/ready` | Readiness check (database & provider connectivity) |
| `GET` | `/api/v1/conversations` | List conversation threads (paginated) |
| `POST` | `/api/v1/conversations` | Create a new conversation |
| `GET` | `/api/v1/conversations/{id}` | Retrieve conversation with messages & artifacts |
| `PATCH` | `/api/v1/conversations/{id}` | Rename conversation title |
| `DELETE` | `/api/v1/conversations/{id}` | Delete conversation |
| `POST` | `/api/v1/chat` | Send message and receive JSON response with citations & artifacts |
| `GET` | `/api/v1/chat/stream` | Stream chat response in real-time via Server-Sent Events (SSE) |
| `GET` | `/api/v1/conversations/{id}/artifacts` | List all artifacts generated in a conversation |
| `GET` | `/api/v1/artifacts/{id}` | Retrieve specific artifact by ID |
| `POST` | `/api/v1/knowledge/ingest` | Trigger transcript file ingestion into vector store |
