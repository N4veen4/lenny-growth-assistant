import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

class TranscriptMetadata(BaseModel):
    episode_title: Optional[str] = None
    url: Optional[str] = None
    speaker: Optional[str] = None
    timestamp: Optional[str] = None

class DocumentChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    text: str
    metadata: TranscriptMetadata
    chunk_index: int

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)

class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float

class IngestResponse(BaseModel):
    processed: int
    skipped: int
    failed: int

class StatusResponse(BaseModel):
    total_documents: int
    total_chunks: int
