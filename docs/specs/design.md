# Frontend Design Handoff (for Lovable)

## 1. Product Design Principles
- **Content-First:** The UI should get out of the way. Transcripts, insights, and generated essays are the stars.
- **Trust through Transparency:** Citations must be clearly visible and easily verifiable.
- **Professional & Premium:** Minimalist aesthetic, subtle borders, thoughtful typography.
- **Responsive:** Fully functional on desktop and readable on mobile.

## 2. Information Architecture & Layout
The application features a modern 3-pane IDE-like layout (collapsible):
1. **Left Sidebar (Navigation & Sessions):**
   - "New Chat" button.
   - List of previous chat sessions, grouped by date (Today, Previous 7 Days).
   - Settings toggle at the bottom.
2. **Center Pane (Chat Interface):**
   - Header: Current session title and Model Selector dropdown (Local Ollama vs Cloud).
   - Message Area: Scrollable chat history.
   - Input Area: Text area with dynamic height, submit button.
3. **Right Pane (Artifact Viewer):**
   - Hidden by default. Opens when an artifact (Essay, Code, HTML layout) is generated.
   - Tabs if multiple artifacts are generated.
   - Full-bleed rendering area with a "Copy" and "Download" action bar.

## 3. Chat and Session History Experience
- **User Messages:** Right-aligned, subtle background color (e.g., light gray or primary brand color).
- **Assistant Messages:** Left-aligned, white/transparent background.
- **Source Citations:** Appended below the assistant's text as small, clickable pills.
  - Example: `[1] Episode 142: Brian Chesky` (Clicking shows a popover with the exact transcript snippet).

## 4. Model Selection Controls
- Placed prominently in the center pane header.
- A toggle or dropdown. 
- State 1: ☁️ Cloud (Fast, High Quality)
- State 2: 💻 Local (Ollama) (Private, No API Cost)
- Visual indicator (e.g., a green dot) if Ollama is detected as running.

## 5. Artifact Viewer Layout
- When the Agent triggers the `generate_artifact` skill, the right pane slides open.
- The viewer has a header indicating the artifact type (e.g., "📝 Essay", "🌐 HTML Preview").
- HTML artifacts are rendered inside a sandboxed iframe.
- Markdown artifacts are rendered with rich typography.

## 6. Loading, Empty, Error, and State Handling
- **Empty State (New Chat):** Welcome message with 3-4 suggested prompts (e.g., "What does Lenny say about finding PMF?", "Write an essay on growth loops.").
- **Loading State:** Shimmering skeleton loader for the message bubble while waiting for the first token. Streaming text thereafter.
- **Error State:** If the model fails (e.g., Ollama is down), display a red-tinted alert inside the chat stream: "Connection to Local Model failed. Please ensure Ollama is running."
- **Unavailable Model:** If a Cloud API key is missing, disable the Cloud option in the dropdown and show a tooltip.

## 7. Visual Hierarchy and Typography
- **Font:** Inter, Roboto, or system sans-serif for UI. Merriweather or a serif font for generated Essays in the Artifact Viewer.
- **Colors:** 
  - Background: #F9FAFB (Tailwind Gray 50)
  - Sidebar: #FFFFFF
  - Primary Accent: #0F172A (Slate 900) for buttons and important highlights.
  - Borders: #E2E8F0 (Slate 200).
- **Spacing:** Generous padding around message bubbles (p-4 or p-6).

## 8. Frontend/Backend Integration Expectations
- Frontend expects standard REST for historical data.
- Frontend expects a Server-Sent Events (SSE) endpoint for chat generation, parsing events like:
  - `event: text_delta, data: "Hello"`
  - `event: citation, data: {"id": 1, "title": "Ep 42"}`
  - `event: artifact_start, data: {"type": "essay"}`
- Frontend uses DOMPurify or iframe sandbox for HTML rendering.
