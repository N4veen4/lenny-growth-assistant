from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
from app.schemas.rag import DocumentChunk
import numpy as np

class VectorStore(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        pass
        
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        pass
        
    @abstractmethod
    def get_status(self) -> Dict[str, int]:
        pass

    def has_document(self, document_id: str) -> bool:
        return False

class InMemoryVectorStore(VectorStore):
    """
    A simple in-memory vector store for testing when Postgres pgvector is blocked.
    Uses numpy for cosine similarity.
    """
    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.embeddings: List[np.ndarray] = []
        self.document_ids = set()
        
    def has_document(self, document_id: str) -> bool:
        return document_id in self.document_ids

    def save_to_disk(self, filepath: str) -> None:
        import pickle
        import os
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {
            "chunks": self.chunks,
            "embeddings": self.embeddings,
            "document_ids": self.document_ids
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def load_from_disk(self, filepath: str) -> bool:
        import pickle
        import os
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "rb") as f:
                data = pickle.load(f)
            self.chunks = data.get("chunks", [])
            self.embeddings = data.get("embeddings", [])
            self.document_ids = set(data.get("document_ids", set()))
            return True
        except Exception:
            return False
        
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings length mismatch")
            
        for chunk, emb in zip(chunks, embeddings):
            # Basic deduplication: check if chunk id already exists
            existing_idx = next((i for i, c in enumerate(self.chunks) if c.id == chunk.id), None)
            
            if existing_idx is not None:
                self.chunks[existing_idx] = chunk
                self.embeddings[existing_idx] = np.array(emb, dtype=np.float32)
            else:
                self.chunks.append(chunk)
                self.embeddings.append(np.array(emb, dtype=np.float32))
                self.document_ids.add(chunk.document_id)
            
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        if not self.embeddings:
            return []
            
        q_emb = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_emb)
        if q_norm == 0:
            return []
            
        scores = []
        for i, emb in enumerate(self.embeddings):
            e_norm = np.linalg.norm(emb)
            if e_norm == 0:
                score = 0.0
            else:
                score = float(np.dot(q_emb, emb) / (q_norm * e_norm))
            scores.append((self.chunks[i], score))
            
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
        
    def get_status(self) -> Dict[str, int]:
        return {
            "total_documents": len(self.document_ids),
            "total_chunks": len(self.chunks)
        }
        
    def clear(self):
        self.chunks.clear()
        self.embeddings.clear()
        self.document_ids.clear()

# Global singleton for testing purposes
_global_vector_store = InMemoryVectorStore()

def get_vector_store() -> VectorStore:
    return _global_vector_store

