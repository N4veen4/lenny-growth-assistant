import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.services.llm import (
    get_llm_provider,
    PiFrameworkProvider,
)
from app.services.writing import extract_artifacts

# ==============================================================================
# Unit Tests for Provider Resolution and Configuration
# ==============================================================================

def test_provider_resolution_local():
    """Verify 'local' provider maps to PiFrameworkProvider with ollama."""
    provider = get_llm_provider("local")
    assert isinstance(provider, PiFrameworkProvider)
    assert provider.display_provider == "local (ollama)"

def test_provider_resolution_cloud(monkeypatch):
    """Verify 'cloud' provider maps to PiFrameworkProvider with openrouter."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-mock-key")
    provider = get_llm_provider("cloud")
    assert isinstance(provider, PiFrameworkProvider)
    assert provider.display_provider == "cloud (openrouter)"

def test_openrouter_missing_credentials(monkeypatch):
    """Verify missing OPENROUTER_API_KEY raises a clear ValueError without faking."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from app.core.config import settings
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None)
    with pytest.raises(ValueError) as excinfo:
        PiFrameworkProvider("cloud")
    assert "OPENROUTER_API_KEY is not set" in str(excinfo.value)

def test_provider_model_separation_defaults_and_override(monkeypatch):
    """Verify model and provider separation and fallback when provider name is erroneously passed as model ID."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-mock-key")
    from app.core.config import settings

    # Case 1: model is None -> defaults to settings.OPENROUTER_MODEL
    p1 = get_llm_provider("cloud", model=None)
    assert p1.model == settings.OPENROUTER_MODEL
    assert p1.display_provider == "cloud (openrouter)"

    # Case 2: model is 'openrouter' (the bug reported) -> recovers to settings.OPENROUTER_MODEL
    p2 = get_llm_provider("cloud", model="openrouter")
    assert p2.model == settings.OPENROUTER_MODEL
    assert p2.model != "openrouter"

    # Case 3: valid explicit model -> preserved
    p3 = get_llm_provider("cloud", model="openai/gpt-4o-mini")
    assert p3.model == "openai/gpt-4o-mini"

    # Case 4: local provider with model='ollama' or 'local' -> recovers to settings.OLLAMA_MODEL_NAME
    p4 = get_llm_provider("local", model="ollama")
    assert p4.model == settings.OLLAMA_MODEL_NAME
    assert p4.display_provider == "local (ollama)"

    p5 = get_llm_provider("local", model="local")
    assert p5.model == settings.OLLAMA_MODEL_NAME

def test_openrouter_no_silent_fallback_to_ollama(monkeypatch):
    """Verify cloud provider failure never silently defaults to local Ollama."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from app.core.config import settings
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None)

    with pytest.raises(ValueError) as excinfo:
        get_llm_provider("cloud")
    assert "OPENROUTER_API_KEY is not set" in str(excinfo.value)

# ==============================================================================
# Integration Test with Chat Endpoint and Artifact Extraction
# ==============================================================================

def test_chat_endpoint_with_openrouter_and_artifact(client: TestClient):
    """Verify chat endpoint extracts artifacts and returns OpenRouter metadata."""
    artifact_text = (
        "Here is your growth strategy guide:\n\n"
        '<artifact type="markdown" title="Growth Strategy Playbook">\n'
        "# Growth Playbook\n"
        "Focus on retention before acquisition.\n"
        "</artifact>\n\n"
        "Hope this helps!"
    )

    def mock_generate(*args, **kwargs):
        return artifact_text, "cloud (openrouter)", "openrouter/free"

    with patch.object(PiFrameworkProvider, "__init__", return_value=None):
        with patch.object(PiFrameworkProvider, "generate_response", side_effect=mock_generate):
            res = client.post("/api/v1/chat", json={
                "message": "Write a growth guide",
                "provider": "cloud"
            })

    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "cloud (openrouter)"
    assert data["model"] == "openrouter/free"
    assert "*[Generated Artifact: Growth Strategy Playbook]*" in data["response_text"]
    assert len(data["artifacts"]) == 1
    assert data["artifacts"][0]["title"] == "Growth Strategy Playbook"
    assert data["artifacts"][0]["artifact_type"] == "markdown"
    assert "Focus on retention before acquisition." in data["artifacts"][0]["content"]

# ==============================================================================
# Optional Live Smoke Test (Runs ONLY when OPENROUTER_API_KEY is configured)
# ==============================================================================

@pytest.fixture()
def openrouter_preflight():
    """Safe preflight check for OpenRouter credentials."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key.startswith("your_"):
        pytest.fail(
            "BLOCKED: OPENROUTER_API_KEY is missing or invalid.\n"
            "MANUAL STEP REQUIRED: Please edit backend/.env and set OPENROUTER_API_KEY to a valid key."
        )
    print("\nPreflight check passed: OPENROUTER_API_KEY is securely configured.")

def test_live_openrouter_smoke(openrouter_preflight):
    """Live smoke test executing real inference against OpenRouter."""
    provider = PiFrameworkProvider("cloud")
    response_text, provider_name, model_name = provider.generate_response(
        system_prompt="You are a helpful assistant. Reply with one word: 'READY'.",
        messages=[{"role": "user", "content": "Ping"}]
    )
    assert response_text and len(response_text) > 0
    assert provider_name == "cloud (openrouter)"
    assert model_name == provider.model
