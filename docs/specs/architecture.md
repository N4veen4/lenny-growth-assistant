# System Architecture: The Lenny Growth Assistant

## 1. System Overview
The system follows a modern three-tier architecture tailored for AI applications:
- **Presentation Layer (Frontend):** React-based Single Page Application (built via Lovable).
- **Application Layer (Backend):** Python/FastAPI service orchestrating the Agent, RAG, and APIs.
- **Data Layer:** PostgreSQL storing sessions, messages, and vectorized transcripts.

## 2. Component Responsibilities
- **React Frontend:** UI state management, chat interface, artifact rendering, markdown parsing, model selection.
- **FastAPI Backend:** RESTful endpoints for CRUD operations on sessions/messages. Manages the Agent runtime and handles RAG retrieval logic.
- **Agent Framework (Anthropic SDK / Pi):** Receives user input, decides whether to use tools (Search Transcripts, Write Essay, Generate Artifact), and constructs the final response.
- **LLM Abstraction Layer:** An interface within the backend that routes prompts to either the local Ollama instance or the Cloud LLM API based on user preference.
- **PostgreSQL (with pgvector):** Relational storage for chat history and vector storage for transcript embeddings.

## 3. Frontend-to-Backend Communication
- **Protocol:** HTTP/REST for session management and standard interactions. Server-Sent Events (SSE) or WebSockets for streaming LLM responses to provide a snappy UX.
- **API Boundaries:**
  - `GET /sessions` - List chat sessions.
  - `POST /sessions` - Create a new session.
  - `GET /sessions/{id}/messages` - Get chat history.
  - `POST /sessions/{id}/chat` - Send a message (returns streaming response).
  - `GET /models` - List available models (Local/Cloud).

## 4. Session and Conversation Data Flow
1. User creates a new session. Frontend calls `POST /sessions`. Backend saves to DB.
2. User sends message. Frontend calls `POST /sessions/{id}/chat` with payload `{"message": "...", "model": "ollama"}`.
3. Backend retrieves session history from DB.
4. Backend formats history and current message, passes to Agent.
5. Agent generates response, Backend streams it to Frontend and saves final message to DB.

## 5. PostgreSQL Persistence Approach
- **Table `sessions`:** `id`, `title`, `created_at`, `updated_at`.
- **Table `messages`:** `id`, `session_id`, `role` (user/assistant), `content`, `metadata` (stores citations, artifact data), `created_at`.
- **Table `documents`:** `id`, `title`, `source_url`, `published_date`.
- **Table `document_chunks`:** `id`, `document_id`, `content`, `embedding` (vector type).

## 6. Transcript Ingestion & RAG
- **Ingestion:** A standalone Python script (run via CLI) reads transcript files, chunks them using LangChain's RecursiveCharacterTextSplitter, generates embeddings (using a local embedding model like `nomic-embed-text` via Ollama to avoid cloud costs for ingestion), and inserts into PostgreSQL via `pgvector`.
- **Retrieval:** When a user asks a question, the backend embeds the query and performs a cosine similarity search on the `document_chunks` table, retrieving the top K chunks.

## 7. Agent Framework & Skill Boundaries
The Agent is instantiated with specific tools/functions:
1. `search_knowledge_base(query)`: Executes the RAG pipeline.
2. `write_ship_30_essay(topic)`: Uses a specialized sub-prompt to generate the 1,250-word essay.
3. `generate_artifact(type, content)`: Signals the frontend to render specific content (HTML/Markdown) in the Artifact Viewer.

## 8. Provider Abstraction
A `LLMProvider` interface will be implemented with two concrete classes:
- `OllamaProvider`: Uses `httpx` to call the local Ollama API (`http://localhost:11434/api/generate` or `/api/chat`).
- `CloudProvider`: Uses the official SDK (e.g., Anthropic or OpenAI) for cloud execution.

## 9. Artifact Generation and Secure Rendering
When the Agent creates an artifact, it outputs a structured block (e.g., `<artifact type="html">...</artifact>`).
The backend parses this, saves it in message metadata, and sends it to the frontend.
The frontend renders HTML artifacts inside a sandboxed `<iframe>` (`sandbox="allow-scripts"`) to prevent XSS attacks while allowing basic interactivity.

## 10. Local Development & Deployment Topology
- **Docker Compose** will orchestrate:
  1. `db`: PostgreSQL + pgvector container.
  2. `api`: FastAPI Python container.
  3. `web`: Node/React container (or statically served by FastAPI in prod, but Node for dev).
- **Ollama** will run on the host machine (not in Docker, to easily utilize host GPU/Metal), exposed to the containers via `host.docker.internal`.

## 11. Important Architecture Decisions & Trade-offs
- **Decision:** Use `pgvector` instead of a dedicated vector DB (like Pinecone/Chroma).
  - *Trade-off:* Simplifies infrastructure to a single database service, perfect for an evaluation project, though might be slightly less performant at massive scale.
- **Decision:** Stream LLM responses.
  - *Trade-off:* Increases backend complexity (async generators) but drastically improves perceived performance for the user.
- **Decision:** Host Ollama outside Docker.
  - *Trade-off:* Requires users to install Ollama manually, but avoids complex GPU passthrough issues in Docker Desktop, ensuring reliable local inference.
