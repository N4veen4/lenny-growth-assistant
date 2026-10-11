import os
import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.schemas.rag import SearchQuery, SearchResult, StatusResponse, IngestResponse
from app.services.vector_store import get_vector_store
from app.services.embeddings import SentenceTransformerProvider
from app.services.ingestion import IngestionService
from app.services.retrieval import RetrievalService

router = APIRouter()
logger = logging.getLogger("rag.diag")

# Initialize services lazily
_embedding_provider = None

def get_embedding_provider():
    global _embedding_provider
    if _embedding_provider is None:
        try:
            _embedding_provider = SentenceTransformerProvider()
            logger.info("EMBEDDING: SentenceTransformerProvider initialized (model=all-MiniLM-L6-v2)")
        except RuntimeError as e:
            logger.warning("EMBEDDING: SentenceTransformerProvider failed: %s", e)
            pass
    return _embedding_provider

@router.post("/search", response_model=List[SearchResult])
def search_knowledge(query: SearchQuery):
    provider = get_embedding_provider()
    if provider is None:
        raise HTTPException(status_code=503, detail="Embedding provider not initialized (sentence-transformers missing)")
    
    vector_store = get_vector_store()
    retrieval_service = RetrievalService(vector_store, provider)
    return retrieval_service.search(query)

@router.get("/status", response_model=StatusResponse)
def get_status():
    vector_store = get_vector_store()
    return vector_store.get_status()

class IngestRequest(BaseModel):
    filepath: str

@router.post("/ingest", response_model=IngestResponse)
def ingest_knowledge(req: IngestRequest):
    provider = get_embedding_provider()
    if provider is None:
        raise HTTPException(status_code=503, detail="Embedding provider not initialized (sentence-transformers missing)")
        
    # Security: only allow files from backend/data/transcripts/
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/transcripts"))
    target_path = os.path.abspath(req.filepath)
    
    if not target_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Invalid ingestion path. Must be within data/transcripts/")
        
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    logger.info("INGEST: filepath='%s' (resolved=%s)", req.filepath, target_path)
    vector_store = get_vector_store()
    vs_status_before = vector_store.get_status()
    logger.info("INGEST: vector_store before -> docs=%d chunks=%d", vs_status_before["total_documents"], vs_status_before["total_chunks"])
    ingestion_service = IngestionService(vector_store, provider)
    result = ingestion_service.process_file(target_path)
    vs_status_after = vector_store.get_status()
    logger.info("INGEST: result processed=%d skipped=%d failed=%d | vector_store after -> docs=%d chunks=%d",
                result.processed, result.skipped, result.failed,
                vs_status_after["total_documents"], vs_status_after["total_chunks"])
    return result
