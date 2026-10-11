# Coding Agent Session 05: Ship 30 for 30 Writing Skill & Sandboxed Artifact Viewer

## Objective
Implement specialized content generation adhering to the Ship 30 for 30 framework, producing persistent HTML/Markdown artifacts viewable in a dedicated drawer.

## Engineering Challenges & Fixes
- **Challenge:** LLM responses mixing commentary and generated essays made parsing difficult and risked rendering unsanitized HTML in the React application.
- **Artifact Contract:** Established explicit `<artifact type="markdown|html" title="...">` tags.
- **Robust Regex Extraction:** Implemented in `app/services/writing.py`:
  - Handles single quotes, double quotes, unquoted attributes, and reversed attribute ordering (`title` before `type`).
  - Safely handles unclosed tags at end of stream so content is preserved rather than dropped.
  - Replaces raw artifact tags in conversational response text with clean markdown badge links: `*[Generated Artifact: Title]*`.
- **Frontend Security:** In `frontend/src/components/assistant/HtmlPreview.tsx`, HTML artifacts are isolated inside an `<iframe>` configured with:
  `sandbox="" referrerPolicy="no-referrer"`
  This guarantees that arbitrary user-generated or model-generated scripts cannot access localStorage, cookies, parent DOM, or trigger XSS attacks.
