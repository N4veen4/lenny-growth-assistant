# Writing Skill

## Overview
The Lenny Growth Assistant supports a dedicated "Writing Skill" tailored for generating long-form content, such as Ship 30 for 30 style essays, articles, and comprehensive product briefs. 

## Invocation Criteria
The skill is intentionally kept separate from generic chat turns to prevent polluting normal conversational answers.
- **Trigger:** The skill is invoked when the user explicitly requests an essay, article, long-form post, or specifically requests an HTML/Markdown document.
- **Mechanism:** The backend `SYSTEM_PROMPT` instructs the LLM to wrap its final output in an `<artifact type="..." title="...">` XML block if these conditions are met. 

## Essay Requirements (Ship 30 for 30 Style)
When writing an essay, the assistant is constrained by the following guidelines injected into the LLM context:
1. Target length of ~1,250 words.
2. Compelling headline and strong opening hook.
3. One central idea with logical progression.
4. Concrete examples and actionable takeaways.
5. Memorable conclusion.
6. Readable paragraphs and clear transitions.
7. Must integrate retrieved podcast evidence when the topic relies on Lenny's knowledge base.
8. Must preserve source metadata/citations and never invent facts.

## Provider Agnosticism
By relying on prompt-based artifact tags (`<artifact>...</artifact>`) rather than complex JSON-based tool calling specifications, the skill gracefully degrades across different model architectures. This ensures the Writing Skill works identically whether the user selects the Local `OllamaProvider` or the Cloud `AnthropicProvider`.

## Output Parsing and Storage
When the backend detects an `<artifact>` block in the LLM response:
1. The block is stripped from the main chat flow and replaced with a placeholder: `*[Generated Artifact: Title]*`.
2. The extracted content is parsed into an `Artifact` record.
3. The artifact is persisted via SQLAlchemy in the `artifacts` table.
4. The artifact is returned inside the `ChatResponse` payload for frontend rendering.
