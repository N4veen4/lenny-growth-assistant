# Coding Agent Session 06: Official GitHub Archive Sync & Large-Scale Transcript Indexing

## Objective
Expand the knowledge corpus from initial mock excerpts to the genuine, official archive of Lenny's Podcast transcripts.

## Source & Synchronization
- **Source Repository:** `https://github.com/LennysNewsletter/lennys-newsletterpodcastdata`
- **Implementation:** Created automated synchronization script `backend/scripts/sync_lenny_transcripts.py`.
- **Parsing Strategy:**
  - Scans all 50 markdown transcripts in the repository (`adam-mosseri`, `peter-sellis`, `molly-graham`, `elena-verna`, `roman-ugarte`, `tom-verrilli`, `tara-seshan`, etc.).
  - Extracts YAML frontmatter for canonical episode titles, guest speaker identities, and newsletter/podcast URLs.
  - Groups turn-by-turn dialogue into cohesive conversational blocks (~900 characters each) preserving exact timestamps and speaker attributions.
  - Generates 300 rich transcript sections into `backend/data/transcripts/lenny_podcasts_archive.json`.
- **Vector Ingestion Performance:**
  - Ran `run_startup_ingestion()` over the 300 documents.
  - Successfully generated 609 dense embedding vectors using SentenceTransformers in ~30 seconds.
  - Persisted the index to `backend/data/vector_store_cache.pkl` for instantaneous cold starts.
