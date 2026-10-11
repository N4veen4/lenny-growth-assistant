import os
import glob
import logging
from typing import Optional, Dict
from app.services.vector_store import get_vector_store
from app.services.ingestion import IngestionService

logger = logging.getLogger("rag.diag")

def run_startup_ingestion(transcripts_dir: Optional[str] = None) -> Dict[str, int]:
    """
    Safely auto-ingests all valid JSON transcript files found in transcripts_dir.
    Checks vector store for duplicates so that chunks are not multiplied on restarts.
    """
    if transcripts_dir is None:
        transcripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/transcripts"))
        
    if not os.path.exists(transcripts_dir):
        logger.warning("STARTUP INGEST: Directory '%s' does not exist.", transcripts_dir)
        return {"processed": 0, "skipped": 0, "failed": 0, "total_documents": 0, "total_chunks": 0}
        
    vector_store = get_vector_store()
    
    # 1. Try loading from disk cache first if vector store is currently empty
    cache_path = os.path.abspath(os.path.join(transcripts_dir, "../vector_store_cache.pkl"))
    if hasattr(vector_store, "load_from_disk") and vector_store.get_status()["total_chunks"] == 0:
        if os.path.exists(cache_path):
            loaded = vector_store.load_from_disk(cache_path)
            if loaded:
                status = vector_store.get_status()
                logger.info("STARTUP INGEST: Restored %d documents, %d chunks from cache (%s)",
                            status["total_documents"], status["total_chunks"], cache_path)

    # 2. Lazily initialize embedding provider
    try:
        from app.api.routes.knowledge import get_embedding_provider
        provider = get_embedding_provider()
    except Exception as e:
        logger.warning("STARTUP INGEST: Embedding provider initialization failed: %s", e)
        provider = None

    if provider is None:
        logger.warning("STARTUP INGEST: Embedding provider not available. File ingestion skipped.")
        status = vector_store.get_status()
        return {
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "total_documents": status["total_documents"],
            "total_chunks": status["total_chunks"]
        }
        
    ingestion_service = IngestionService(vector_store, provider)
    json_files = sorted(glob.glob(os.path.join(transcripts_dir, "*.json")))
    
    total_processed = 0
    total_skipped = 0
    total_failed = 0
    
    for filepath in json_files:
        # Skip temporary test files
        if os.path.basename(filepath).startswith("test_"):
            continue
            
        logger.info("STARTUP INGEST: Inspecting '%s'", filepath)
        res = ingestion_service.process_file(filepath)
        total_processed += res.processed
        total_skipped += res.skipped
        total_failed += res.failed
        
    # 3. Persist updated vector store to disk cache if new documents were processed
    if total_processed > 0 and hasattr(vector_store, "save_to_disk"):
        try:
            vector_store.save_to_disk(cache_path)
            logger.info("STARTUP INGEST: Persisted updated vector store cache to '%s'", cache_path)
        except Exception as e:
            logger.warning("STARTUP INGEST: Failed to persist vector store cache: %s", e)
            
    status = vector_store.get_status()
    logger.info("STARTUP INGEST COMPLETE: %d docs, %d chunks available (processed=%d, skipped=%d, failed=%d)",
                status["total_documents"], status["total_chunks"], total_processed, total_skipped, total_failed)
                
    return {
        "processed": total_processed,
        "skipped": total_skipped,
        "failed": total_failed,
        "total_documents": status["total_documents"],
        "total_chunks": status["total_chunks"]
    }
