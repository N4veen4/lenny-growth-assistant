# Lenny Growth Assistant - Frontend

The frontend is a modern, responsive, and accessible web application built with **React 19**, **TypeScript**, **Tailwind CSS v4**, and **TanStack Router / Start**. It delivers a ChatGPT/Claude-style experience tailored to product growth insights from Lenny Rachitsky's podcast and newsletter library.

---

## ✨ Features

- **Split-Pane Workspace:**
  - **Collapsible Sidebar:** Conversation thread management (create, rename, delete, switch).
  - **Central Chat:** Markdown-rendered conversation with streaming tokens and auto-scroll.
  - **Artifact Viewer:** Dedicated collapsible side pane that renders generated essays, teardowns, and strategic roadmaps in formatted Markdown or live HTML.
- **Realtime SSE Streaming:** Token-by-token response streaming with low-latency Server-Sent Events (SSE).
- **Interactive Source Citations:** Clickable badges linking directly to podcast timestamps, episodes, and transcript excerpts.
- **Dynamic Model Switching:** Fast toggle between **Local (Ollama / Llama 3)** and **Cloud (OpenRouter / Llama 3.3 / Claude)**.
- **Design System:** Rich dark-mode palette, subtle micro-interactions, accessible Radix UI primitives, Lucide icons, and toast feedback (Sonner).

---

## 🛠️ Tech Stack

- **Framework:** [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Routing & State:** [TanStack Router](https://tanstack.com/router) & [TanStack Query](https://tanstack.com/query)
- **Styling:** [Tailwind CSS v4](https://tailwindcss.com/) with curated HSL color tokens
- **Components:** [Radix UI](https://www.radix-ui.com/) + custom accessible wrappers
- **Markdown & Code:** `react-markdown` with GitHub Flavored Markdown (`remark-gfm`)
- **Testing & Tooling:** [Vitest](https://vitest.dev/), [Testing Library](https://testing-library.com/), [ESLint](https://eslint.org/), and [Prettier](https://prettier.io/)

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```
Ensure `VITE_API_BASE_URL` points to your backend instance:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. Run Development Server
```bash
npm run dev
```
The application will launch at `http://localhost:5173` (or `http://localhost:8080` if configured).

---

## 🧪 Testing & Code Quality

### Run Unit & Integration Tests (Vitest)
```bash
npm test
```

### Check Linting & Formatting
```bash
npm run lint
```

### Auto-Format Codebase
```bash
npm run format
```

### Build Production Bundle
```bash
npm run build
```

---

## 📁 Project Structure

```
frontend/src/
├── components/
│   ├── assistant/           # Domain components (Chat, Sidebar, Artifacts, Citations)
│   │   ├── AppLayout.tsx           # Master layout with responsive split-pane
│   │   ├── ArtifactViewer.tsx      # Side drawer for reading essays & HTML
│   │   ├── ChatHeader.tsx          # Model toggle and thread metadata
│   │   ├── ChatMessage.tsx         # Message bubble with markdown & citations
│   │   ├── ConversationSidebar.tsx # Thread list with rename/delete
│   │   ├── MessageComposer.tsx     # Dynamic auto-growing textarea & send controls
│   │   ├── ModelSelector.tsx       # Local vs. Cloud switcher
│   │   ├── SourceCitation.tsx      # Grounding citation cards & episode links
│   │   └── store.tsx               # Client state machine & SSE streaming engine
│   └── ui/                  # Radix-based reusable UI primitives
├── hooks/                   # Custom React hooks (useMobile, etc.)
├── lib/                     # Utility functions (formatting, date-fns, error reporting)
├── routes/                  # TanStack Start file-based routing
├── services/                # API client with REST & SSE streaming
├── styles.css               # Global theme tokens, typography & animations
└── test/                    # Vitest component & integration test specs
```
