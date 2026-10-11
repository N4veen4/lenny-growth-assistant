# The Lenny Growth Assistant — Frontend Prototype

Frontend-only prototype with mock data, local state, and a clean service boundary for a future FastAPI backend. No backend, database, auth, or real AI.

## Visual direction

- Warm neutral "editorial workspace": off-white paper background, ink-dark text, single restrained accent (deep terracotta/orange) used for active states and primary actions.
- Typography: Fraunces-style serif for titles only is avoided in favor of clean pairing — **Geist / Geist Mono** (body + code) with **Instrument Serif** for the app name and empty-state headline only.
- Subtle 1px borders, 10px radius, minimal motion (150ms transitions), visible focus rings. Light theme primary, dark theme tokens included.

## Layout

```text
+------------+---------------------------+------------------+
| Sidebar    | Chat workspace            | Artifact Viewer  |
| logo       | header: title · model     | (opens on demand)|
| New chat   | messages + citations      | tabs Preview/Src |
| search     |                           | copy/download/x  |
| grouped    | composer (multiline)      |                  |
| list       |                           |                  |
+------------+---------------------------+------------------+
```

- Desktop: collapsible sidebar (icon rail), artifact panel side-by-side.
- Tablet: sidebar as overlay drawer; artifact panel side-by-side if width allows.
- Mobile: sidebar drawer, artifact viewer full-screen sheet.

## Features

- **Sidebar**: New Chat, search filter, conversations grouped Today / Yesterday / Previous 7 days / Older, active highlight, rename (inline) and delete (confirm dialog), empty state.
- **Chat**: title, model badge, user/assistant styling, markdown rendering, source citations (labeled "Mock sources") under answers, starter questions for new chats, Enter to send / Shift+Enter newline, Cmd/Ctrl+K new chat, states: empty, loading (thinking), generating (streamed mock text with Stop), error (with Retry; triggerable via a demo prompt like "simulate error").
- **Model selector**: Local Ollama (llama3.1, mistral, qwen2.5) and Cloud provider (configurable name + model input). Clear "Preview only — not connected" note.
- **Artifact Viewer**: opens from artifact cards in assistant messages; Markdown preview and HTML/CSS preview in a sandboxed iframe (`sandbox=""`, `srcdoc`, no scripts, no same-origin); Preview/Source tabs; copy, download (.md/.html); close and reopen; loading, empty, render-error states.
- Mock replies: keyword-matched realistic answers on retention, PLG, pricing, onboarding, PMF; some include a markdown or HTML artifact.
- Persistence: conversations and model choice saved in browser localStorage.

## Technical details

- Single route `/` (rewrite `src/routes/index.tsx`) with proper head metadata; fonts linked in `__root.tsx`.
- Components in `src/components/assistant/`: AppLayout, ConversationSidebar, ConversationItem, ChatHeader, ChatMessage, SourceCitation, MessageComposer, ModelSelector, ArtifactViewer, MarkdownPreview, HtmlPreview, EmptyState, LoadingState, ErrorState.
- State: `useAssistantStore` hook (React context + reducer), hydrated from localStorage in an effect to avoid SSR mismatch.
- Service boundary `src/services/api.ts` defining an `AssistantApi` interface (health, createSession, listSessions, getMessages, sendMessage (async iterator), listModels/selectModel, generateArtifact/getArtifact) with `mockApi` implementation; a future `httpApi` swaps in via one export.
- Types in `src/types/assistant.ts`; mock data in `src/mocks/`.
- Markdown via `react-markdown` + `remark-gfm` (no raw HTML). shadcn primitives (dialog, dropdown, tabs, sheet, tooltip) added as needed.
- Small vitest tests for grouping-by-date and conversation search filter.
- Verify with Playwright at desktop and mobile widths: send message, artifact open/close/tabs, rename/delete, error state.
