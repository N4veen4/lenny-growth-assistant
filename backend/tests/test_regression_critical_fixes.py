import json
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.artifact import Artifact
from app.schemas.chat import Citation
from app.schemas.rag import SearchQuery, SearchResult, DocumentChunk, TranscriptMetadata
from app.services.retrieval import RetrievalService
from app.services.writing import extract_artifacts
from app.services.llm import is_writing_request
from app.services.startup import run_startup_ingestion
from app.api.routes.chat import is_podcast_summary_query

def test_citation_metadata_preservation():
    """Issue 1: Test that retrieved citation metadata (title, URL, speaker, timestamp) is preserved intact."""
    meta = TranscriptMetadata(
        episode_title="Brian Chesky’s new playbook for product, leadership, and growth",
        url="https://www.lennyspodcast.com/brian-cheskys-new-playbook/#transcript",
        speaker="Brian Chesky",
        timestamp="00:05:56"
    )
    chunk = DocumentChunk(
        id="test_chunk_1",
        document_id="lenny_ep_brian_chesky",
        text="Leaders need to be in the details.",
        metadata=meta,
        chunk_index=0
    )
    citation = Citation(
        episode_title=meta.episode_title,
        url=meta.url,
        speaker=meta.speaker,
        timestamp=meta.timestamp,
        content=chunk.text
    )
    dumped = citation.model_dump()
    assert dumped["episode_title"] == "Brian Chesky’s new playbook for product, leadership, and growth"
    assert dumped["url"] == "https://www.lennyspodcast.com/brian-cheskys-new-playbook/#transcript"
    assert dumped["speaker"] == "Brian Chesky"
    assert dumped["timestamp"] == "00:05:56"
    assert dumped["content"] == "Leaders need to be in the details."

def test_unrelated_queries_produce_no_citations():
    """Issue 1 & 2: Irrelevant queries must not attach irrelevant citations."""
    run_startup_ingestion()
    from app.services.vector_store import get_vector_store
    from app.api.routes.knowledge import get_embedding_provider
    vs = get_vector_store()
    ep = get_embedding_provider()
    rs = RetrievalService(vs, ep)

    unrelated_query = SearchQuery(query="What is the capital of France and how to make a chocolate cake?", top_k=3)
    results = rs.search(unrelated_query)
    # Cosine score on unrelated query must be filtered out by the 0.18 threshold
    filtered = [r for r in results if r.score >= 0.18]
    assert len(filtered) == 0

def test_broad_podcast_summary_retrieval():
    """Issue 2: 'summarize Lenny\'s podcast' queries must retrieve representative chunks across episodes."""
    run_startup_ingestion()
    from app.services.vector_store import get_vector_store
    from app.api.routes.knowledge import get_embedding_provider
    vs = get_vector_store()
    ep = get_embedding_provider()
    rs = RetrievalService(vs, ep)

    assert is_podcast_summary_query("summarize Lenny's podcast") is True
    assert is_podcast_summary_query("What is Lenny's podcast about?") is True
    assert is_podcast_summary_query("How to calculate churn rate?") is False

    rep_chunks = rs.get_representative_chunks(limit=3)
    assert len(rep_chunks) >= 2
    # Ensure distinct episodes are represented
    episodes = {r.chunk.metadata.episode_title for r in rep_chunks}
    assert len(episodes) >= 2
    for r in rep_chunks:
        assert r.chunk.metadata.episode_title is not None
        assert r.chunk.metadata.url is not None
        assert r.chunk.metadata.speaker is not None

def test_message_and_citations_database_persistence(client: TestClient, db_session):
    """Issue 1 & 3: Citations and artifacts must persist across conversation reopen / reload."""
    conv_res = client.post("/api/v1/conversations", json={"title": "Test Persistence Chat"})
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    sample_citations = [
        {
            "episode_title": "10 growth tactics that never work | Elena Verna",
            "url": "https://www.lennysnewsletter.com/p/10-growth-tactics-that-never-work",
            "speaker": "Elena Verna",
            "timestamp": "00:00:26",
            "content": "There is a huge misconception in tech that in order to get growth going..."
        }
    ]
    msg = Message(
        conversation_id=uuid.UUID(conv_id),
        role="assistant",
        content="*[Generated Artifact: Elena Verna Growth Guide]*",
        citations_json=json.dumps(sample_citations)
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)

    art = Artifact(
        conversation_id=uuid.UUID(conv_id),
        message_id=msg.id,
        title="Elena Verna Growth Guide",
        artifact_type="markdown",
        content="# Elena Verna Growth Guide\n\nKey takeaways from the podcast."
    )
    db_session.add(art)
    db_session.commit()
    db_session.refresh(art)
    art_id = str(art.id)

    # Retrieve messages via API endpoint (simulating page reload / reopening conversation)
    msgs_res = client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert msgs_res.status_code == 200
    msgs = msgs_res.json()
    assert len(msgs) == 1
    ast_msg = msgs[0]
    assert ast_msg["role"] == "assistant"
    # Citations must be present and correctly populated
    assert len(ast_msg["citations"]) == 1
    c = ast_msg["citations"][0]
    assert c["episode_title"] == "10 growth tactics that never work | Elena Verna"
    assert c["url"] == "https://www.lennysnewsletter.com/p/10-growth-tactics-that-never-work"
    assert c["speaker"] == "Elena Verna"
    assert c["timestamp"] == "00:00:26"

    # Artifact must be associated with the message and retrievable directly
    assert ast_msg["artifact"] is not None
    assert ast_msg["artifact"]["id"] == art_id
    assert ast_msg["artifact"]["title"] == "Elena Verna Growth Guide"
    assert ast_msg["artifact"]["type"] == "markdown"
    assert ast_msg["artifact"]["artifact_type"] == "markdown"

    # Direct artifact endpoint check
    single_art_res = client.get(f"/api/v1/artifacts/{art_id}")
    assert single_art_res.status_code == 200
    single_art = single_art_res.json()
    assert single_art["id"] == art_id
    assert single_art["title"] == "Elena Verna Growth Guide"
    assert single_art["type"] == "markdown"

def test_writing_request_detection():
    """Issue 3 & 4: Detection of writing requests ensures tools are only declared when appropriate."""
    assert is_writing_request("Write an essay on product leadership") is True
    assert is_writing_request("Draft an article about product market fit in Ship 30 style") is True
    assert is_writing_request("Create a guide on PLG tactics") is True
    assert is_writing_request("Create an HTML page demonstrating conversion funnels") is True
    assert is_writing_request("What did Brian Chesky say about product management?") is False
    assert is_writing_request("Hello, can you help me?") is False
    assert is_writing_request("How to prioritize a roadmap?") is False

def test_extract_artifacts_cleans_content_and_extracts_metadata():
    """Issue 3: Test that extract_artifacts properly isolates artifact blocks and returns clean text."""
    raw_response = (
        "Here is the essay you requested:\n\n"
        '<artifact type="markdown" title="Product Leadership Playbook">\n'
        "# Product Leadership Playbook\n\n"
        "Great leaders manage by influence and remain grounded in the details.\n"
        "</artifact>\n\n"
        "Let me know if you need any adjustments!"
    )
    cleaned, extracted = extract_artifacts(raw_response)
    assert len(extracted) == 1
    assert extracted[0]["title"] == "Product Leadership Playbook"
    assert extracted[0]["type"] == "markdown"
    assert "Great leaders manage by influence" in extracted[0]["content"]
    assert "<artifact" not in cleaned
    assert "</artifact>" not in cleaned
    assert "*[Generated Artifact: Product Leadership Playbook]*" in cleaned

def test_streaming_sse_event_format_and_citations(client: TestClient):
    """Issue 1, 3, 4: SSE streaming endpoint yields valid JSON events with citations and done payload."""
    with patch("app.api.routes.chat.get_llm_provider") as mock_get_llm:
        mock_llm = MagicMock()
        def mock_stream(system_prompt, messages, on_event):
            on_event("assistant_delta", "According to Brian Chesky, ")
            on_event("assistant_delta", "leaders must stay in the details.")
            return "According to Brian Chesky, leaders must stay in the details.", "local (ollama)", "qwen3:4b"
        mock_llm.generate_streamed_response.side_effect = mock_stream
        mock_get_llm.return_value = mock_llm

        res = client.post("/api/v1/chat", json={
            "message": "What did Brian Chesky say about details?",
            "provider": "local",
            "model": "qwen3:4b",
            "stream": True
        })
        assert res.status_code == 200
        lines = [line.strip() for line in res.text.split("\n") if line.startswith("data: ")]
        assert len(lines) >= 3

        # Parse first event ('init')
        init_event = json.loads(lines[0][6:])
        assert init_event["type"] == "init"
        assert "conversationId" in init_event
        assert "citations" in init_event
        assert len(init_event["citations"]) > 0
        c0 = init_event["citations"][0]
        assert "Brian Chesky" in (c0.get("speaker") or "") or "Chesky" in (c0.get("episode_title") or "")
        assert c0.get("url") is not None

        # Parse 'done' event (last before [DONE])
        done_line = lines[-2] if lines[-1] == "data: [DONE]" else lines[-1]
        done_event = json.loads(done_line[6:])
        assert done_event["type"] == "done"
        assert "content" in done_event["data"]
        assert "citations" in done_event["data"]
        assert "artifacts" in done_event["data"]
