import os
import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.services.vector_store import get_vector_store
from app.services.startup import run_startup_ingestion
from app.services.llm import PiFrameworkProvider

def test_valid_and_duplicate_ingestion(client: TestClient):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/transcripts"))
    os.makedirs(base_dir, exist_ok=True)
    test_file = os.path.join(base_dir, "test_valid_ingest.json")
    
    initial_status = client.get("/api/v1/knowledge/status").json()
    initial_docs = initial_status["total_documents"]
    initial_chunks = initial_status["total_chunks"]
    
    test_data = [
        {
            "id": "valid_ep1",
            "episode_title": "Brian Chesky on Airbnb Leadership",
            "url": "https://www.lennyspodcast.com/brian-cheskys-new-playbook/#transcript",
            "speaker": "Brian Chesky",
            "timestamp": "05:18",
            "content": "Leaders must be in the details to understand if teams are executing well. It is not micromanagement, it is responsible leadership."
        }
    ]
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)
        
    try:
        # 1. First Ingest (Valid)
        res = client.post("/api/v1/knowledge/ingest", json={"filepath": test_file})
        if res.status_code == 503:
            pytest.skip("Embedding provider not initialized")
        assert res.status_code == 200
        data = res.json()
        assert data["processed"] == 1
        assert data["skipped"] == 0
        assert data["failed"] == 0
        
        status_res = client.get("/api/v1/knowledge/status")
        assert status_res.status_code == 200
        assert status_res.json()["total_documents"] == initial_docs + 1
        assert status_res.json()["total_chunks"] == initial_chunks + 1
        
        # 2. Duplicate Ingest (Same file / same document ID)
        res_dup = client.post("/api/v1/knowledge/ingest", json={"filepath": test_file})
        assert res_dup.status_code == 200
        data_dup = res_dup.json()
        assert data_dup["processed"] == 0
        assert data_dup["skipped"] == 1
        assert data_dup["failed"] == 0
        
        # Chunk and document count must remain unchanged (no duplicate ingestion)
        status_after = client.get("/api/v1/knowledge/status").json()
        assert status_after["total_documents"] == initial_docs + 1
        assert status_after["total_chunks"] == initial_chunks + 1
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_validation_rejection_dummy_url_and_malformed(client: TestClient):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/transcripts"))
    os.makedirs(base_dir, exist_ok=True)
    test_file = os.path.join(base_dir, "test_validation.json")
    
    initial_status = client.get("/api/v1/knowledge/status").json()
    initial_docs = initial_status["total_documents"]
    initial_chunks = initial_status["total_chunks"]
    
    test_data = [
        {
            "id": "dummy_url_1",
            "episode_title": "Dummy URL Episode",
            "url": "https://example.com/test", # Rejected: dummy domain
            "content": "Some meaningful content here."
        },
        {
            "id": "dummy_url_2",
            "episode_title": "Test Domain Episode",
            "url": "http://test.com/bad", # Rejected: dummy domain
            "content": "Some meaningful content here."
        },
        {
            "id": "missing_title",
            "url": "https://www.lennyspodcast.com/ep1",
            "content": "Content with missing episode_title" # Rejected: missing title
        },
        {
            "id": "empty_content",
            "episode_title": "Empty Content Episode",
            "url": "https://www.lennyspodcast.com/ep2",
            "content": "   " # Rejected: empty content
        },
        "not a dictionary record" # Rejected: malformed
    ]
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)
        
    try:
        res = client.post("/api/v1/knowledge/ingest", json={"filepath": test_file})
        if res.status_code == 503:
            pytest.skip("Embedding provider not initialized")
        assert res.status_code == 200
        data = res.json()
        assert data["processed"] == 0
        assert data["skipped"] == 1 # 1 empty content
        assert data["failed"] == 4 # 2 dummy URLs + 1 missing title + 1 non-dict
        
        # Nothing should be added to vector store
        status = client.get("/api/v1/knowledge/status").json()
        assert status["total_documents"] == initial_docs
        assert status["total_chunks"] == initial_chunks
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_empty_dataset(client: TestClient):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/transcripts"))
    os.makedirs(base_dir, exist_ok=True)
    test_file = os.path.join(base_dir, "test_empty.json")
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump([], f)
        
    try:
        res = client.post("/api/v1/knowledge/ingest", json={"filepath": test_file})
        if res.status_code == 503:
            pytest.skip("Embedding provider not initialized")
        assert res.status_code == 200
        data = res.json()
        assert data["processed"] == 0
        assert data["skipped"] == 0
        assert data["failed"] == 0
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_restart_behavior(client: TestClient):
    # Verify that run_startup_ingestion repopulates an empty vector store
    store = get_vector_store()
    store.clear()
    assert store.get_status()["total_chunks"] == 0
    
    # Run startup ingestion against data/transcripts
    result = run_startup_ingestion()
    status = store.get_status()
    assert status["total_documents"] >= 1
    assert status["total_chunks"] >= 1
    
    # Running startup ingestion a second time must be idempotent (no duplicate chunks)
    chunks_before = status["total_chunks"]
    run_startup_ingestion()
    chunks_after = store.get_status()["total_chunks"]
    assert chunks_after == chunks_before

def test_retrieval_known_passage(client: TestClient):
    # Query specific concept known to be in Brian Chesky's genuine transcript
    search_res = client.post("/api/v1/knowledge/search", json={
        "query": "combining inbound product development with product marketing",
        "top_k": 2
    })
    if search_res.status_code == 503:
        pytest.skip("Embedding provider not initialized")
    assert search_res.status_code == 200
    results = search_res.json()
    assert len(results) >= 1
    
    top_result = results[0]
    assert top_result["score"] > 0.3
    assert "product marketing" in top_result["chunk"]["text"].lower()
    meta = top_result["chunk"]["metadata"]
    assert "Brian Chesky" in meta["episode_title"] or meta["speaker"] == "Brian Chesky"
    assert "lennyspodcast.com" in meta["url"]

def mock_llm_response(*args, **kwargs):
    return "Brian Chesky combined inbound product development with outbound product marketing at Airbnb.", "local (ollama)", "llama3"

@patch.object(PiFrameworkProvider, '__init__', return_value=None)
@patch.object(PiFrameworkProvider, 'generate_response', side_effect=mock_llm_response)
def test_citation_correctness(mock_gen, mock_init, client: TestClient):
    chat_res = client.post("/api/v1/chat", json={
        "message": "What did Brian Chesky say about combining inbound product development with outbound product marketing responsibilities at Airbnb?",
        "provider": "local"
    })
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert len(data["citations"]) >= 1
    first_citation = data["citations"][0]
    assert first_citation["episode_title"] is not None
    assert "http" in first_citation["url"]
    assert first_citation["speaker"] is not None
    assert len(first_citation["content"]) > 20

def test_search_empty_query(client: TestClient):
    res = client.post("/api/v1/knowledge/search", json={
        "query": "",
        "top_k": 5
    })
    assert res.status_code == 422

def test_ingest_invalid_path(client: TestClient):
    res = client.post("/api/v1/knowledge/ingest", json={
        "filepath": "/etc/passwd"
    })
    if res.status_code != 503:
        assert res.status_code == 403
