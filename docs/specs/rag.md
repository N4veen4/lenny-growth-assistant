# Retrieval-Augmented Generation (RAG) Architecture

## Transcript Source and Provenance
- **Source:** For Phase 5, we use a sample subset of parsed podcast JSON objects (`backend/data/transcripts/sample.json`), representing mock records of Lenny's Podcast transcripts.
- **Format:** JSON arrays containing `episode_title`, `url`, `speaker`, `timestamp`, and `content`.
- **Limitations:** This is a limited evaluation dataset to test the ingestion and retrieval pipeline without incurring massive data processing overhead. The actual large-scale dataset will be parsed similarly into this JSON format before ingestion.

## Ingestion Workflow
The ingestion pipeline is handled by `IngestionService` in `app/services/ingestion.py`.
1. It reads the target JSON file.
2. Cleans whitespace and removes noise.
3. Splits text using a sliding window word-based approach.
4. Generates embeddings in batches.
5. Stores the chunks and embeddings into the `VectorStore`.

## Chunking Configuration
- **Chunk Size:** 1000 words (approximately 5000 characters) - Configurable in `IngestionService`.
- **Chunk Overlap:** 200 words (approximately 1000 characters) to preserve context boundaries.
- **Strategy:** Sliding window chunking based on word count to prevent unnatural sentence breaks where possible.

## Embedding Model and Dimensions
- **Model:** `all-MiniLM-L6-v2` via `sentence-transformers`.
- **Dimensions:** 384.
- **Rationale:** This is a fast, local embedding model that runs purely on the CPU, removing the need for cloud API keys (e.g., OpenAI) and reducing costs during local development and testing.

## Vector-Storage Design
- **Current Implementation:** Due to the local PostgreSQL instance (and `pgvector`) being blocked during the evaluation phase, a clean `VectorStore` abstraction has been implemented. The application defaults to an `InMemoryVectorStore` using `numpy` for exact cosine similarity search.
- **Future State:** A `PgVectorStore` can trivially implement the `VectorStore` interface once the PostgreSQL dependency is successfully provisioned.

## Retrieval Parameters
- **Top-K:** Defaults to 5 (configurable via the API).
- **Metric:** Cosine similarity.
- **Filtering:** No metadata pre-filtering is strictly applied in this phase, but the abstraction allows for it.

## API Usage
- **Ingest:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/knowledge/ingest" \
       -H "Content-Type: application/json" \
       -d '{"filepath": "backend/data/transcripts/sample.json"}'
  ```
- **Search:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/knowledge/search" \
       -H "Content-Type: application/json" \
       -d '{"query": "growth and retention", "top_k": 3}'
  ```
- **Status:**
  ```bash
  curl "http://localhost:8000/api/v1/knowledge/status"
  ```

## Known Limitations
- The `InMemoryVectorStore` is ephemeral; knowledge is wiped if the backend restarts.
- Initial load of `SentenceTransformer` requires a one-time download of model weights from HuggingFace.

## Test Commands
Run the complete RAG test suite:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest -v tests/test_rag.py
```
