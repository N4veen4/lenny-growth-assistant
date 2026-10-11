import time
from fastapi.testclient import TestClient

def test_create_conversation(client: TestClient):
    response = client.post("/api/v1/conversations", json={"title": "Test Convo"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Convo"
    assert "id" in data

def test_list_conversations(client: TestClient):
    client.post("/api/v1/conversations", json={"title": "Test Convo 1"})
    client.post("/api/v1/conversations", json={"title": "Test Convo 2"})
    
    response = client.get("/api/v1/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_list_conversations_pagination_and_ordering(client: TestClient):
    client.post("/api/v1/conversations", json={"title": "Convo 1"})
    time.sleep(0.01)
    client.post("/api/v1/conversations", json={"title": "Convo 2"})
    time.sleep(0.01)
    client.post("/api/v1/conversations", json={"title": "Convo 3"})

    # Limit to 2
    response = client.get("/api/v1/conversations?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Should be newest first (Convo 3, then Convo 2)
    assert data[0]["title"] == "Convo 3"
    assert data[1]["title"] == "Convo 2"

    # Skip 1, limit 2
    response2 = client.get("/api/v1/conversations?skip=1&limit=2")
    data2 = response2.json()
    assert len(data2) == 2
    assert data2[0]["title"] == "Convo 2"
    assert data2[1]["title"] == "Convo 1"

def test_get_conversation(client: TestClient):
    create_response = client.post("/api/v1/conversations", json={"title": "Test Convo"})
    convo_id = create_response.json()["id"]

    response = client.get(f"/api/v1/conversations/{convo_id}")
    assert response.status_code == 200
    assert response.json()["id"] == convo_id

def test_get_conversation_not_found(client: TestClient):
    response = client.get(f"/api/v1/conversations/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_rename_conversation(client: TestClient):
    create_response = client.post("/api/v1/conversations", json={"title": "Old Title"})
    convo_id = create_response.json()["id"]

    patch_res = client.patch(f"/api/v1/conversations/{convo_id}", json={"title": "New Title"})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "New Title"

    get_res = client.get(f"/api/v1/conversations/{convo_id}")
    assert get_res.json()["title"] == "New Title"

def test_rename_conversation_not_found(client: TestClient):
    patch_res = client.patch(f"/api/v1/conversations/00000000-0000-0000-0000-000000000000", json={"title": "New Title"})
    assert patch_res.status_code == 404

def test_delete_conversation(client: TestClient):
    create_response = client.post("/api/v1/conversations", json={"title": "To Delete"})
    convo_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/conversations/{convo_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/conversations/{convo_id}")
    assert get_response.status_code == 404
