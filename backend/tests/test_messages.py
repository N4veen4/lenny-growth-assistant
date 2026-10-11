from fastapi.testclient import TestClient
import time

def test_create_and_get_messages(client: TestClient):
    convo_res = client.post("/api/v1/conversations", json={"title": "Test Messages Convo"})
    convo_id = convo_res.json()["id"]

    msg1_res = client.post(f"/api/v1/conversations/{convo_id}/messages", json={
        "role": "user",
        "content": "First message"
    })
    assert msg1_res.status_code == 201
    
    time.sleep(0.01)

    msg2_res = client.post(f"/api/v1/conversations/{convo_id}/messages", json={
        "role": "user",
        "content": "Second message"
    })
    assert msg2_res.status_code == 201

    get_res = client.get(f"/api/v1/conversations/{convo_id}/messages")
    assert get_res.status_code == 200
    messages = get_res.json()
    assert len(messages) == 2
    assert messages[0]["content"] == "First message"
    assert messages[1]["content"] == "Second message"
    # Ensure chronological
    assert messages[0]["created_at"] < messages[1]["created_at"]

def test_create_message_invalid_role(client: TestClient):
    convo_res = client.post("/api/v1/conversations", json={"title": "Test Invalid Role"})
    convo_id = convo_res.json()["id"]

    res = client.post(f"/api/v1/conversations/{convo_id}/messages", json={
        "role": "assistant",
        "content": "I am the assistant."
    })
    assert res.status_code == 422

def test_create_message_empty_content(client: TestClient):
    convo_res = client.post("/api/v1/conversations", json={"title": "Test Empty Content"})
    convo_id = convo_res.json()["id"]

    res = client.post(f"/api/v1/conversations/{convo_id}/messages", json={
        "role": "user",
        "content": "   "
    })
    assert res.status_code == 422

def test_create_message_oversized(client: TestClient):
    convo_res = client.post("/api/v1/conversations", json={"title": "Test Oversized"})
    convo_id = convo_res.json()["id"]

    res = client.post(f"/api/v1/conversations/{convo_id}/messages", json={
        "role": "user",
        "content": "A" * 10001
    })
    assert res.status_code == 422

def test_create_message_not_found_convo(client: TestClient):
    res = client.post(f"/api/v1/conversations/00000000-0000-0000-0000-000000000000/messages", json={
        "role": "user",
        "content": "Hello"
    })
    assert res.status_code == 404
