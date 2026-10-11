# Project Documentation

Welcome to the **Lenny Growth Assistant** documentation hub. This directory contains architectural specifications, product requirements, and audit reports for all implementation phases.

---

## 📐 Specifications & Architecture (`/docs/specs`)

| Document | Description |
| :--- | :--- |
| **[Product Requirements Document (PRD)](./specs/PRD.md)** | Core product vision, user personas, functional & non-functional requirements, and constraints. |
| **[System Architecture](./specs/architecture.md)** | End-to-end technical architecture, component diagrams, data flows, and technology choices. |
| **[Frontend Design Specification](./specs/design.md)** | Design tokens, typography, dark mode palette, component hierarchy, and responsive layout guidelines. |
| **[Implementation Plan](./specs/IMPLEMENTATION_PLAN.md)** | 9-phase development roadmap and acceptance criteria from foundation to delivery. |
| **[RAG Pipeline Specification](./specs/rag.md)** | Chunking strategies, vector embeddings (Nomic/SentenceTransformers), and citation retrieval logic. |
| **[Writing Skill & Artifacts](./specs/writing-skill.md)** | Essay generation protocol, ReAct tool loop, structured XML schema, and database persistence. |
| **[Artifact Viewer UI](./specs/artifact-viewer.md)** | Side-by-side artifact rendering pane, HTML/Markdown preview, copy/download interactions. |

---

## 📋 Audit Reports & Compliance (`/docs/reports`)

| Report | Description |
| :--- | :--- |
| **[Agent Framework Compliance](./reports/agent-framework-compliance.md)** | Evaluation of Pi Coding Agent (`pi-coding-agent`) and compliance with multi-provider constraints. |
| **[OpenRouter Integration Report](./reports/openrouter-integration-report.md)** | Cloud inference integration, fallback policies, rate limits, and live verification. |
| **[Phase 4 Audit Report](./reports/phase4-audit-report.md)** | PostgreSQL & pgvector schema, Alembic migrations, and conversation session CRUD testing. |
| **[Phase 5 Audit Report](./reports/phase5-audit-report.md)** | Podcast transcript ingestion, embedding generation, and vector search benchmarks. |
| **[Phase 6 Audit Report](./reports/phase6-audit-report.md)** | Dual LLM provider switching (Ollama local vs. OpenRouter cloud) and ReAct tool binding. |
| **[Phase 7 Audit Report](./reports/phase7-audit-report.md)** | Structured essay generation, regex/fallback XML tag parsing, and artifact persistence. |
| **[Phase 8 API Contract](./reports/phase8-api-contract.md)** | Formal REST & SSE streaming contract between FastAPI backend and React frontend. |
| **[Phase 8 Audit Report](./reports/phase8-audit-report.md)** | Frontend/backend integration audit, error boundaries, state sync, and CORS verification. |
| **[Phase 8 Integration Report](./reports/phase8-integration-report.md)** | End-to-end user flow verification (message streaming, citation badges, artifact pane). |
