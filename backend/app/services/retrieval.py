import logging
import time
from typing import List
from app.schemas.rag import SearchQuery, SearchResult
from app.services.embeddings import EmbeddingProvider
from app.services.vector_store import VectorStore

logger = logging.getLogger("rag.diag")

class RetrievalService:
    def __init__(self, vector_store: VectorStore, embedding_provider: EmbeddingProvider):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    def search(self, query: SearchQuery) -> List[SearchResult]:
        if not query.query.strip():
            return []
            
        embed_start = time.perf_counter()
        query_embedding = self.embedding_provider.embed_text(query.query)
        embed_time = time.perf_counter() - embed_start
        logger.info(f"TIMING: [retrieval] Embed Latency: {embed_time:.4f}s")
        
        # VectorStore handles cosine similarity and returning top_k
        search_start = time.perf_counter()
        results = self.vector_store.search(query_embedding, top_k=query.top_k)
        search_time = time.perf_counter() - search_start
        logger.info(f"TIMING: [retrieval] Vector Search Latency: {search_time:.4f}s")
        logger.info("RETRIEVAL: query='%s' embedding_dim=%d top_k=%d -> %d results",
                    query.query[:80], len(query_embedding), query.top_k, len(results))
        
        return [SearchResult(chunk=chunk, score=score) for chunk, score in results]
        
    def prepare_grounded_evidence(self, query: SearchQuery) -> str:
        results = self.search(query)
        if not results:
            return "No relevant evidence found."
            
        evidence_texts = []
        for res in results:
            meta = res.chunk.metadata
            source_info = f"Source: {meta.episode_title or 'Unknown Episode'}"
            if meta.url:
                source_info += f" ({meta.url})"
            if meta.speaker:
                source_info += f" - {meta.speaker}"
            if meta.timestamp:
                source_info += f" @ {meta.timestamp}"
                
            evidence_texts.append(f"[{source_info}]\n{res.chunk.text}")
            
        return "\n\n".join(evidence_texts)

    def get_representative_chunks(self, limit: int = 3) -> List[SearchResult]:
        """
        Retrieves representative chunks from distinct episodes in the archive.
        Used for broad queries like 'summarize Lenny's podcast'.
        """
        if not hasattr(self.vector_store, "chunks") or not self.vector_store.chunks:
            return []
            
        seen_episodes = set()
        representative = []
        
        for chunk in self.vector_store.chunks:
            ep_key = chunk.metadata.episode_title or chunk.document_id
            if ep_key not in seen_episodes:
                seen_episodes.add(ep_key)
                representative.append(SearchResult(chunk=chunk, score=1.0))
                if len(representative) >= limit:
                    break
                    
        return representative
