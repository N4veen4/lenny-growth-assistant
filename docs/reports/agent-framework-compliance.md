# Agent Framework Compliance Audit

## 1. Requirement Analysis
The assessment explicitly mandated the use of one of the following two approved frameworks for the agent layer:
1. **Anthropic Claude Agent SDK**
2. **Pi Coding Agent**

## 2. Framework Evaluation & Recommendation
We evaluated both frameworks to determine the most suitable option for the existing Python/FastAPI backend, with the hard constraints of supporting both **Ollama (local inference)** and **OpenRouter (cloud inference)**.

*   **Anthropic Claude Agent SDK**: While powerful and providing a native ReAct loop, it is designed almost exclusively around Anthropic's Claude models. It relies heavily on Anthropic-specific API signatures (such as specific block schemas for tools and responses). Natively supporting Ollama and OpenRouter would require building brittle, unsupported wrapper classes that pretend to be the Anthropic API.
*   **Pi Coding Agent (`pi-coding-agent`)**: This is an open-source agent harness designed explicitly for extensibility and multi-provider support. Its core `Agent` orchestrator runs a provider-neutral internal transcript and uses `LLMProvider` abstractions to translate requests to OpenAI, Anthropic, OpenRouter, and Ollama out of the box. 

**Recommendation: Pi Coding Agent**
Pi Coding Agent is the only framework that satisfies the assessment requirement while genuinely supporting both the local Ollama and cloud OpenRouter endpoints without "pretending" compatibility.

## 3. Implementation Details
The `pi-coding-agent` framework has been invoked directly in the chat workflow:
*   Instead of making raw HTTP calls via `httpx` inside `app/services/llm.py`, we now instantiate `pi_agent.agent.Agent`.
*   We supply the agent with a `Sandbox` and a `ToolRegistry`.
*   The conversation history from FastAPI is mapped into the framework's `NeutralMessage` format.
*   The actual model interaction and tool loop is delegated to `agent.run()`.

## 4. Architectural Distinctions
To clarify the structure of the implemented system:

1.  **Agent Orchestration Framework (Pi Coding Agent)**: Responsible for managing the conversation loop. It receives the prompt, orchestrates the internal ReAct loop, maintains the prompt/history context, and interacts with the provider.
2.  **LLM Provider (Ollama / OpenRouter)**: The actual inference engine. Pi Agent translates its neutral transcript into the specific wire format required by Ollama or OpenRouter.
3.  **RAG Retrieval Service (`RetrievalService`)**: A pre-agent service. It queries the vector database (pgvector) to find relevant transcript chunks and injects them as evidence into the system prompt before the Agent orchestrator is invoked.
4.  **Writing Skill / Artifact Generation**: A post-processing workflow (currently prompt-driven). The LLM is instructed via the system prompt to wrap code/documents in XML tags. After the Agent orchestrator completes its run, the backend parses these tags to extract structured Artifact objects to save to the database.
