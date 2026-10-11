import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.artifact import Artifact
from app.models.message import Message
from app.services.startup import run_startup_ingestion
from app.services.llm import check_native_tool_support, OllamaCompatibleProvider

def test_tool_support_detection_for_llama3():
    """Verify that llama3:latest is correctly detected as NOT supporting native tools."""
    assert check_native_tool_support("local", "llama3:latest") is False
    assert check_native_tool_support("local", "llama3") is False
    assert check_native_tool_support("local", "llama3.1:8b") is True
    assert check_native_tool_support("cloud", "openrouter/free") is True

def test_ollama_compatible_provider_omits_tools():
    """Verify that OllamaCompatibleProvider strips tools from payload when not supported."""
    provider = OllamaCompatibleProvider(
        model="llama3:latest",
        base_url="http://localhost:11434/v1/",
        supports_tools=False
    )
    neutral_messages = [{"role": "user", "content": "hi"}]
    test_tools = [{
        "name": "test_tool",
        "description": "test",
        "input_schema": {"type": "object", "properties": {}}
    }]
    payload = provider._payload("system", neutral_messages, test_tools)
    assert "tools" not in payload
    assert payload["model"] == "llama3:latest"

def test_live_ollama_normal_chat():
    """Test 1: Normal chat question using Local (Ollama) with llama3:latest."""
    # Ensure startup ingestion has run
    run_startup_ingestion()
    
    with TestClient(app) as client:
        res = client.post("/api/v1/chat", json={
            "message": "Hello, can you reply with the word 'Confirmed'?",
            "provider": "local",
            "model": "llama3:latest"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        data = res.json()
        assert data["provider"] == "local (ollama)"
        assert "conversation_id" in data
        assert len(data["response_text"]) > 0

def test_live_ollama_rag_retrieval_and_citations():
    """Test 2 & 3: Question retrieving Lenny source material, citation accuracy, and grounding."""
    run_startup_ingestion()
    
    with TestClient(app) as client:
        # Ask about Brian Chesky's playbook from genuine_transcripts.json
        res = client.post("/api/v1/chat", json={
            "message": "What did Brian Chesky say about product management and leadership at Airbnb?",
            "provider": "local",
            "model": "llama3:latest"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        data = res.json()
        assert data["provider"] == "local (ollama)"
        # Check that citations were returned from the knowledge base
        assert len(data["citations"]) > 0
        citation = data["citations"][0]
        assert citation["episode_title"] is not None
        assert "chesky" in citation["episode_title"].lower() or "chesky" in (citation["speaker"] or "").lower()
        # Verify assistant response is grounded in the retrieved material
        assert len(data["response_text"]) > 50

def test_live_ollama_essay_and_artifact_persistence():
    """Test 4: Essay and artifact generation and database persistence with llama3:latest."""
    with TestClient(app) as client:
        res = client.post("/api/v1/chat", json={
            "message": "Write a short essay on Product-Market Fit. Please follow the writing skill instructions and produce an artifact.",
            "provider": "local",
            "model": "llama3:latest"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        data = res.json()
        assert len(data["artifacts"]) >= 1
        artifact = data["artifacts"][0]
        assert artifact["title"]
        assert len(artifact["content"]) > 50
        assert artifact["message_id"] == data["assistant_message_id"]

        # Verify artifact can be retrieved from /api/v1/artifacts/{id}
        art_res = client.get(f"/api/v1/artifacts/{artifact['id']}")
        assert art_res.status_code == 200
        assert art_res.json()["id"] == artifact["id"]

def test_live_conversation_history_and_sessions():
    """Test 5: Conversation history and independent sessions."""
    with TestClient(app) as client:
        # Create session 1: Ask about Brian Chesky
        res1 = client.post("/api/v1/chat", json={
            "message": "What did Brian Chesky say about product managers?",
            "provider": "local",
            "model": "llama3:latest"
        })
        assert res1.status_code == 200
        conv1_id = res1.json()["conversation_id"]

        # Create session 2 (independent): Ask about Elena Verna
        res2 = client.post("/api/v1/chat", json={
            "message": "What did Elena Verna say about growth teams?",
            "provider": "local",
            "model": "llama3:latest"
        })
        assert res2.status_code == 200
        conv2_id = res2.json()["conversation_id"]
        assert conv1_id != conv2_id

        # Verify that session 1 messages only belong to session 1
        msgs1 = client.get(f"/api/v1/conversations/{conv1_id}/messages").json()
        msgs2 = client.get(f"/api/v1/conversations/{conv2_id}/messages").json()
        assert len(msgs1) == 2  # 1 user + 1 assistant
        assert len(msgs2) == 2  # 1 user + 1 assistant
        assert all(m["conversation_id"] == conv1_id for m in msgs1)
        assert all(m["conversation_id"] == conv2_id for m in msgs2)

        # Follow up in session 1 asking for a brief summary of that discussion
        res1_followup = client.post("/api/v1/chat", json={
            "message": "Can you summarize his main point from our discussion in one short sentence?",
            "conversation_id": conv1_id,
            "provider": "local",
            "model": "llama3:latest"
        })
        assert res1_followup.status_code == 200
        msgs1_after = client.get(f"/api/v1/conversations/{conv1_id}/messages").json()
        assert len(msgs1_after) == 4  # 2 user + 2 assistant in session 1
        # Session 2 must remain untouched
        msgs2_after = client.get(f"/api/v1/conversations/{conv2_id}/messages").json()
        assert len(msgs2_after) == 2

def test_live_provider_switching():
    """Test 6: Switching between Local (Ollama) and Cloud (OpenRouter)."""
    with TestClient(app) as client:
        # First call with local
        res_local = client.post("/api/v1/chat", json={
            "message": "Hello from local",
            "provider": "local",
            "model": "llama3:latest"
        })
        assert res_local.status_code == 200
        assert res_local.json()["provider"] == "local (ollama)"
        conv_id = res_local.json()["conversation_id"]

        # Second call in same conversation switching to cloud
        res_cloud = client.post("/api/v1/chat", json={
            "message": "Hello from cloud",
            "conversation_id": conv_id,
            "provider": "cloud",
            "model": "openrouter/free"
        })
        assert res_cloud.status_code == 200
        assert res_cloud.json()["provider"] == "cloud (openrouter)"

        # Third call switching back to local
        res_back = client.post("/api/v1/chat", json={
            "message": "Back to local",
            "conversation_id": conv_id,
            "provider": "local",
            "model": "llama3:latest"
        })
        assert res_back.status_code == 200
        assert res_back.json()["provider"] == "local (ollama)"
