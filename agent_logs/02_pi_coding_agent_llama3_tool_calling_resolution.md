# Coding Agent Session 02: Pi Coding Agent & Llama 3 Tool Calling Fix

## Objective
Integrate the mandatory `pi-coding-agent` framework (`0.6.0`) with local Ollama daemon for the mandatory offline demo.

## Problem & Failed Attempt
- **Initial Setup:** We connected `pi_agent.llm.OpenAIProvider` to `http://localhost:11434/v1/` and registered the Ship 30 for 30 `writing_tool` in `ToolRegistry`.
- **Failure Symptom:** When testing with Ollama's `llama3:latest` (the base 8.0B model without tool-call templates in its Modelfile), Ollama rejected the request with:
  `HTTP 400 Bad Request: {"error": "llama3 does not support tools"}`.
- **Root Cause:** Base Llama 3 does not include the Go template syntax `{{ .Tools }}` in Ollama, so any payload containing `"tools": [...]` triggers a hard 400 rejection from Ollama's `/v1/chat/completions` endpoint.

## Corrective Engineering
1. **Dynamic Capability Probing:** Added `check_native_tool_support(provider_type, model, base_url)` in `app/services/llm.py` that queries Ollama's `/api/show` endpoint or inspects the model slug.
2. **Custom Provider Subclass:** Created `OllamaCompatibleProvider(OpenAIProvider)` which overrides `_payload()`:
   ```python
   def _payload(self, system: str, messages: List[NeutralMessage], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
       payload = super()._payload(system, messages, tools)
       if not self.supports_tools or not tools:
           payload.pop("tools", None)
       payload.setdefault("extra_body", {})["keep_alive"] = "1h"
       return payload
   ```
3. **Outcome:** Allowed `llama3:latest` to conduct conversations and generate structured artifacts via prompt directives, completely eliminating the HTTP 400 error.
