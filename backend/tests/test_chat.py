import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.services.llm import PiFrameworkProvider

def mock_ollama_generate(*args, **kwargs):
    return "Mocked local response", "local (ollama)", "llama3"

def mock_openrouter_generate(*args, **kwargs):
    return "Mocked cloud response", "cloud (openrouter)", "meta-llama/llama-3.3-70b-instruct:free"

@patch.object(PiFrameworkProvider, '__init__', return_value=None)
@patch.object(PiFrameworkProvider, 'generate_response', side_effect=mock_ollama_generate)
def test_chat_local_provider(mock_gen, mock_init, client: TestClient):
    res = client.post("/api/v1/chat", json={
        "message": "Hello",
        "provider": "local"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "local (ollama)"
    assert data["response_text"] == "Mocked local response"
    assert "conversation_id" in data
    
@patch.object(PiFrameworkProvider, '__init__', return_value=None)
@patch.object(PiFrameworkProvider, 'generate_response', side_effect=mock_openrouter_generate)
def test_chat_cloud_provider(mock_gen, mock_init, client: TestClient):
    res = client.post("/api/v1/chat", json={
        "message": "Hello",
        "provider": "cloud"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "cloud (openrouter)"
    assert data["response_text"] == "Mocked cloud response"

def test_chat_invalid_provider(client: TestClient):
    res = client.post("/api/v1/chat", json={
        "message": "Hello",
        "provider": "invalid"
    })
    # Pydantic Literal validation should fail it with 422
    assert res.status_code == 422

@patch.object(PiFrameworkProvider, '__init__', return_value=None)
@patch.object(PiFrameworkProvider, 'generate_response', side_effect=Exception("Connection refused"))
def test_chat_provider_failure(mock_gen, mock_init, client: TestClient):
    res = client.post("/api/v1/chat", json={
        "message": "Hello",
        "provider": "local"
    })
    assert res.status_code == 502

@patch.object(PiFrameworkProvider, '__init__', return_value=None)
@patch.object(PiFrameworkProvider, 'generate_response', side_effect=mock_ollama_generate)
def test_chat_conversation_history(mock_gen, mock_init, client: TestClient):
    res1 = client.post("/api/v1/chat", json={"message": "First message"})
    assert res1.status_code == 200
    conv_id = res1.json()["conversation_id"]
    
    res2 = client.post("/api/v1/chat", json={"message": "Second message", "conversation_id": conv_id})
    assert res2.status_code == 200
    assert res2.json()["conversation_id"] == conv_id
    
    # Verify messages are saved
    history_res = client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 4 # User1, Ast1, User2, Ast2
    assert history[0]["content"] == "First message"
    assert history[2]["content"] == "Second message"

def test_chat_invalid_conversation(client: TestClient):
    import uuid
    res = client.post("/api/v1/chat", json={
        "message": "Hello",
        "conversation_id": str(uuid.uuid4())
    })
    assert res.status_code == 404

@patch.object(PiFrameworkProvider, '__init__', return_value=None)
@patch.object(PiFrameworkProvider, 'generate_response', side_effect=mock_ollama_generate)
def test_chat_creates_new_conversation_when_id_omitted(mock_gen, mock_init, client: TestClient):
    res = client.post("/api/v1/chat", json={
        "message": "Brand new chat without conversation ID"
    })
    assert res.status_code == 200
    data = res.json()
    assert "conversation_id" in data
    assert data["conversation_id"] is not None
    assert data["response_text"] == "Mocked local response"

    # Verify conversation exists and has user + assistant messages
    conv_res = client.get(f"/api/v1/conversations/{data['conversation_id']}/messages")
    assert conv_res.status_code == 200
    msgs = conv_res.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Brand new chat without conversation ID"
    assert msgs[1]["role"] == "assistant"

def test_cors_preflight_allows_frontend_ports(client: TestClient):
    for origin in ["http://localhost:8080", "http://localhost:8081"]:
        res = client.options("/api/v1/chat", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST"
        })
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") == origin
