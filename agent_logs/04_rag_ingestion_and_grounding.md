# Coding Agent Session 04: RAG Ingestion, Grounding, and Hallucination Prevention

## Objective
Build a reliable, verifiable Retrieval-Augmented Generation pipeline grounded strictly in Lenny's Podcast transcripts.

## Architectural Implementation
1. **Validation Layer:** `app/services/ingestion.py` strictly checks:
   - Valid, non-empty `content` and `episode_title`.
   - Genuine HTTP/HTTPS URLs (rejecting `example.com`, `test.com`, or dummy domains).
   - Duplicate prevention via MD5 content hash and vector store document deduplication.
2. **Chunking Strategy:** Sliding window chunker breaking long transcripts into ~1,000-character segments with 200-character overlap to preserve dialogue context.
3. **Embeddings:** Local `SentenceTransformers` (`all-MiniLM-L6-v2`, 384 dimensions) for zero-latency, offline embedding computation.
4. **Cosine Similarity Thresholding:** Queries must surpass a `0.18` similarity threshold. If no chunks match, the system injects strict prompt constraints directing the assistant to refuse to answer rather than hallucinating knowledge not present in the podcast.
