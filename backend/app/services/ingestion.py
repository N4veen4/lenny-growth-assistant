import json
import uuid
import re
import logging
from typing import List, Tuple, Set, Optional
from urllib.parse import urlparse
from app.schemas.rag import DocumentChunk, TranscriptMetadata, IngestResponse
from app.services.embeddings import EmbeddingProvider
from app.services.vector_store import VectorStore

logger = logging.getLogger("rag.diag")

DUMMY_DOMAINS = {
    "example.com", "www.example.com",
    "example.org", "www.example.org",
    "example.net", "www.example.net",
    "test.com", "www.test.com",
    "localhost", "127.0.0.1", "0.0.0.0"
}

def is_valid_url(url: Optional[str]) -> Tuple[bool, str]:
    if not url or not isinstance(url, str):
        return False, "URL is missing or not a string"
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "URL must start with http:// or https://"
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if not netloc:
            return False, "URL host is missing"
        host = netloc.split(":")[0]
        if host in DUMMY_DOMAINS or host.endswith(".example") or host.endswith(".invalid") or host.endswith(".test"):
            return False, f"Dummy domain detected in URL: '{host}'"
        if "." not in host:
            return False, f"URL host '{host}' is not a valid domain"
        return True, ""
    except Exception as e:
        return False, f"URL parse error: {e}"

def validate_record(item: any) -> Tuple[bool, str]:
    if not isinstance(item, dict):
        return False, "Record must be a JSON object (dictionary)"
    
    content = item.get("content")
    if not content or not isinstance(content, str) or not content.strip():
        return False, "Content is empty, missing, or not a string"
        
    title = item.get("episode_title")
    if not title or not isinstance(title, str) or not title.strip():
        return False, "episode_title is empty, missing, or not a string"
        
    url = item.get("url")
    is_valid, reason = is_valid_url(url)
    if not is_valid:
        return False, reason
        
    return True, ""

class IngestionService:
    def __init__(self, vector_store: VectorStore, embedding_provider: EmbeddingProvider, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def clean_text(self, text: str) -> str:
        # Normalize whitespace and remove obvious noise
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def chunk_text(self, text: str) -> List[str]:
        # Simple sliding window chunker based on words to preserve meaning better than naive character splits
        words = text.split()
        chunks = []
        # Rough approximation: 1 word ~ 5 characters
        word_chunk_size = self.chunk_size // 5
        word_overlap = self.chunk_overlap // 5
        
        if not words:
            return []
            
        i = 0
        while i < len(words):
            chunk_words = words[i:i + word_chunk_size]
            chunks.append(" ".join(chunk_words))
            i += (word_chunk_size - word_overlap)
            if i >= len(words) or word_chunk_size <= word_overlap:
                break
        return chunks

    def process_file(self, filepath: str) -> IngestResponse:
        processed = 0
        skipped = 0
        failed = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.warning("INGEST FAIL: Unable to read JSON file '%s': %s", filepath, e)
            return IngestResponse(processed=0, skipped=0, failed=1)
            
        if not isinstance(data, list):
            data = [data]
            
        seen_in_batch: Set[str] = set()

        for item in data:
            try:
                # 1. Validate record schema, content, and genuine URL
                is_valid, reason = validate_record(item)
                if not is_valid:
                    logger.warning("INGEST REJECT: %s in file '%s'", reason, filepath)
                    # If content is empty whitespace, treat as skipped; if malformed/dummy URL, treat as failed
                    if "Content is empty" in reason:
                        skipped += 1
                    else:
                        failed += 1
                    continue
                    
                import hashlib
                doc_id = item.get('id')
                if not doc_id:
                    doc_id = hashlib.md5(item['content'].encode('utf-8')).hexdigest()
                    
                # 2. Check for duplicate IDs within batch or already loaded in vector store
                if doc_id in seen_in_batch:
                    logger.warning("INGEST SKIP: Duplicate document ID '%s' found in same file/batch", doc_id)
                    skipped += 1
                    continue
                    
                if hasattr(self.vector_store, 'has_document') and self.vector_store.has_document(doc_id):
                    logger.info("INGEST SKIP: Document ID '%s' already exists in vector store", doc_id)
                    skipped += 1
                    seen_in_batch.add(doc_id)
                    continue

                seen_in_batch.add(doc_id)
                content = self.clean_text(item['content'])
                text_chunks = self.chunk_text(content)
                
                if not text_chunks:
                    skipped += 1
                    continue
                    
                metadata = TranscriptMetadata(
                    episode_title=item.get('episode_title'),
                    url=item.get('url'),
                    speaker=item.get('speaker'),
                    timestamp=item.get('timestamp')
                )
                
                doc_chunks = []
                for idx, t in enumerate(text_chunks):
                    doc_chunks.append(DocumentChunk(
                        id=f"{doc_id}_{idx}",
                        document_id=doc_id,
                        text=t,
                        metadata=metadata,
                        chunk_index=idx
                    ))
                
                embeddings = self.embedding_provider.embed_batch([c.text for c in doc_chunks])
                self.vector_store.add_chunks(doc_chunks, embeddings)
                
                processed += 1
            except Exception as e:
                logger.error("INGEST ERROR processing record: %s", e)
                failed += 1
                
        return IngestResponse(processed=processed, skipped=skipped, failed=failed)
