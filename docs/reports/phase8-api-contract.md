# Phase 8 API Contracts and Frontend Integration Guide

This document provides the API schemas, backend endpoints, and required frontend integration instructions to connect the Lovable frontend to the FastAPI backend for Phase 8B.

## 1. Centralized API Client setup

Create a centralized API service in the Lovable project (e.g., `src/lib/api.ts`).
Configure it to use the base URL defined in the `.env` file (e.g., `VITE_API_BASE_URL`).

```typescript
// src/lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function fetchWithValidation(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorMsg = "API Error";
    try {
      const errorData = await response.json();
      errorMsg = errorData.detail || errorMsg;
    } catch {
      errorMsg = response.statusText;
    }
    throw new ApiError(response.status, errorMsg);
  }

  return response.json();
}
```

## 2. API Endpoints and Schemas

### 2.1 Conversations

**Create Conversation**
- `POST /conversations`
- Request: `{ "title": "string (optional)" }`
- Response: 
```typescript
interface Conversation {
  id: string; // UUID
  title: string | null;
  created_at: string; // ISO format
  updated_at: string;
}
```

**List Conversations**
- `GET /conversations?skip=0&limit=100`
- Response: `Conversation[]`

**Get Conversation History**
- `GET /conversations/{id}/messages`
- Response: `Message[]`
```typescript
interface Message {
  id: string; // UUID
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}
```

### 2.2 Chat & Artifact Generation

**Send Message**
- `POST /chat`
- Request:
```typescript
interface ChatRequest {
  message: string;
  conversation_id?: string; // Optional UUID
  provider: "local" | "cloud";
}
```
- Response:
```typescript
interface Citation {
  episode_title?: string;
  url?: string;
  speaker?: string;
  timestamp?: string;
  content: string;
}

interface ChatResponse {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  response_text: string;
  citations: Citation[];
  artifacts: Artifact[];
  provider: string;
  model: string;
}
```

### 2.3 Artifacts

**List Artifacts for Conversation**
- `GET /conversations/{id}/artifacts`
- Response: `Artifact[]`

**Get Specific Artifact**
- `GET /artifacts/{id}`
- Response: `Artifact`
```typescript
interface Artifact {
  id: string;
  conversation_id: string;
  title: string;
  artifact_type: "markdown" | "html" | "text";
  content: string;
  version: number;
  created_at: string;
  updated_at: string;
}
```

## 3. Provider Switching Integration
Bind your frontend's model selector to the `provider` property of `ChatRequest`. 
- When the user selects "Local Ollama", send `"local"`.
- When the user selects "Cloud (Anthropic)", send `"cloud"`.
- In the chat interface, display the `provider` and `model` fields returned from `ChatResponse` below the assistant's message.

## 4. Citation Rendering
When rendering messages from `ChatResponse`, check if the `citations` array has elements. If it does, render them below the assistant's response.
- Create a `CitationCard` component that maps through the array.
- Display `episode_title` and `speaker`.
- Make the `url` clickable if provided.
- Ensure citations remain visually distinct from the standard markdown response (e.g., using a smaller font, a different background color, or a collapsed accordion).

## 5. Artifact Viewer Integration & Security Rules

When a `ChatResponse` contains `artifacts`, render an `ArtifactCard` inside the chat flow indicating an artifact was generated. Provide an "Open" button.

When opened:
- Render the `ArtifactViewer` component as a side panel (on desktop) or a drawer (on mobile).
- Ensure the `ArtifactViewer` can toggle between "Preview" and "Code" modes.
- Implement "Copy" and "Download" buttons using standard Web APIs.

**Security Constraints for Artifact Preview:**
- **Markdown (`artifact_type: "markdown"`):** Use `react-markdown` in combination with `DOMPurify` to heavily sanitize HTML. Do NOT execute scripts.
- **HTML (`artifact_type: "html"`):** You MUST render this inside an isolated iframe.
  ```tsx
  <iframe
    sandbox="allow-scripts allow-same-origin" // OR just "allow-scripts" if origin access isn't strictly needed
    srcDoc={artifact.content}
    style={{ width: "100%", height: "100%", border: "none" }}
  />
  ```
- **Never inject `artifact.content` directly into the DOM using `dangerouslySetInnerHTML`.**

## 6. Frontend State & Loading Indicators
- Ensure "Send" button is disabled while `fetchWithValidation` is executing.
- Render skeleton loaders or spinners for the chat window and the artifact viewer.
- If `ApiError` is thrown, display a toast or inline error message with the error details (e.g., "Provider timeout", "Cannot reach Ollama").
