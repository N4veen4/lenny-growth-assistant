# Coding Agent Session 03: OpenRouter Dual Provider Routing & Fail-Safe Defaults

## Objective
Support seamless switching between local Ollama and cloud OpenRouter inference in both frontend and backend.

## Problem & Failed Attempt
- **Initial Setup:** The frontend passed the string `"openrouter"` as both provider and model name.
- **Failure Symptom:** OpenRouter returned a 400 error indicating that `"openrouter"` is not a valid model slug. Furthermore, when `OPENROUTER_API_KEY` was missing in early tests, an unintentional fallback occurred where requests defaulted to Ollama, creating confusion about which model responded.

## Corrective Engineering
1. **Model Slug Disambiguation:** In `app/services/llm.py`, added safety guards:
   ```python
   if not model or model.strip().lower() == "openrouter":
       self.model = settings.OPENROUTER_MODEL
   ```
2. **Explicit Authentication Assertion:** If `provider="cloud"` is selected but `OPENROUTER_API_KEY` is not present, the backend explicitly raises `ValueError("OPENROUTER_API_KEY is not set.")` with HTTP 400/500, refusing to silently fake responses or silently redirect to local models.
3. **Active Endpoint Verification:** Discovered during audit that OpenRouter retired the free slug `meta-llama/llama-3.3-70b-instruct:free`. Corrected default configuration to active free endpoint `nvidia/nemotron-3.5-lightning:free` and validated live inference with HTTP 200.
