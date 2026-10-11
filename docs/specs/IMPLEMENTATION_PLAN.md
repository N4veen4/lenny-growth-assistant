# Phase 1: Project Foundation & Requirements
- [x] Inspect existing workspace.
- [x] Create PRD.md.
- [x] Create architecture.md.
- [x] Create design.md.
- [x] Create .env.example.
- [x] Create README.md.
- [x] Create .gitignore.
- [x] Create IMPLEMENTATION_PLAN.md.
- **Acceptance Criteria:** All foundational documents exist, are clear, and adhere to constraints.

# Phase 2: Frontend Design in Lovable
- [ ] Hand off `design.md` to Lovable.
- [ ] Generate React application scaffolding.
- [ ] Implement UI layout (Sidebar, Chat, Artifact Viewer).
- [ ] Implement Model Selection toggle.
- **Acceptance Criteria:** Frontend renders locally, static UI matches design specs, responsive layout works.

# Phase 3: FastAPI Backend Foundation
- [ ] Setup Python virtual environment & dependencies (FastAPI, Uvicorn, SQLAlchemy).
- [ ] Create basic project structure (routers, models, schemas).
- [ ] Implement health check endpoint.
- [ ] Configure CORS and environment variable loading.
- **Acceptance Criteria:** Backend starts successfully, `/health` returns 200 OK.

# Phase 4: PostgreSQL and Conversation Management
- [ ] Setup PostgreSQL with pgvector via Docker.
- [ ] Define SQLAlchemy ORM models (Session, Message).
- [ ] Create Alembic migrations.
- [ ] Implement REST endpoints for session CRUD and retrieving message history.
- **Acceptance Criteria:** Can create sessions and fetch chat history via API.

# Phase 5: Transcript Ingestion and RAG
- [ ] Define Document and DocumentChunk database models.
- [ ] Write ingestion script to parse, chunk, and embed transcripts using Ollama embeddings.
- [ ] Implement RAG retrieval logic (vector similarity search).
- **Acceptance Criteria:** Ingestion script populates DB; retrieval function successfully returns relevant chunks based on a query.

# Phase 6: Agent Layer and Local/Cloud Model Switching
- [ ] Integrate Agent SDK.
- [ ] Implement `LLMProvider` abstraction for Ollama and Cloud LLM.
- [ ] Implement system prompts and tool binding for the Agent.
- [ ] Expose chat endpoint with streaming response.
- **Acceptance Criteria:** Can chat with the API using either Ollama or Cloud LLM; responses stream correctly.

# Phase 7: Writing Skill and Artifact Viewer
- [ ] Implement `write_ship_30_essay` tool logic.
- [ ] Implement `generate_artifact` tool logic.
- [ ] Ensure Agent formats artifacts correctly in output.
- **Acceptance Criteria:** Asking for an essay triggers the skill, retrieves context, and outputs properly tagged artifact markup.

# Phase 8: Frontend/Backend Integration
- [ ] Connect React frontend to FastAPI backend.
- [ ] Implement SSE/streaming message parsing in frontend.
- [ ] Implement citation rendering.
- [ ] Wire up Artifact Viewer to render received HTML/Markdown.
- **Acceptance Criteria:** End-to-end chat works; citations are clickable; artifacts render in the side pane.

# Phase 9: Testing, Documentation, and Submission
- [ ] Write backend unit tests (pytest).
- [ ] Verify error handling and local fallback.
- [ ] Finalize `docker-compose.yml` for end-to-end deployment.
- [ ] Update README with final run instructions.
- **Acceptance Criteria:** Project builds with `docker-compose up`, passes tests, and satisfies all requirements for the take-home assessment.
