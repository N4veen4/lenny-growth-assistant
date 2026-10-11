import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.services.llm import PiFrameworkProvider
from app.services.writing import extract_artifacts, writing_tool, WRITING_SKILL_PROMPT


def test_extract_artifacts_standard():
    response = """Here is the essay you requested:
<artifact type="markdown" title="My Cool Essay">
# Heading
This is an essay with multiple lines.

```python
def foo():
    return "<not a tag>"
```
</artifact>
Hope you like it!"""
    cleaned, artifacts = extract_artifacts(response)
    
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "markdown"
    assert artifacts[0]["title"] == "My Cool Essay"
    assert "This is an essay with multiple lines." in artifacts[0]["content"]
    assert 'return "<not a tag>"' in artifacts[0]["content"]
    assert "<artifact" not in cleaned
    assert "[Generated Artifact: My Cool Essay]" in cleaned
    assert "Here is the essay you requested:" in cleaned


def test_extract_artifacts_reversed_attributes():
    response = """<artifact title="Reversed Title" type="markdown">
# Reversed
Content here.
</artifact>"""
    cleaned, artifacts = extract_artifacts(response)
    assert len(artifacts) == 1
    assert artifacts[0]["title"] == "Reversed Title"
    assert artifacts[0]["type"] == "markdown"
    assert "Content here." in artifacts[0]["content"]


def test_extract_artifacts_unquoted_and_single_quotes():
    response = """<artifact type='html' title='HTML Single Quotes'>
<div>Hello World</div>
</artifact>"""
    cleaned, artifacts = extract_artifacts(response)
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "html"
    assert artifacts[0]["title"] == "HTML Single Quotes"
    assert "<div>Hello World</div>" in artifacts[0]["content"]


def test_extract_artifacts_unclosed_tag():
    """Verify unclosed <artifact> tag captures content safely rather than losing it."""
    response = """Here is your document:
<artifact type="markdown" title="Unclosed Document">
# Unclosed
This artifact was never closed by the model.
Line 2 of document."""
    cleaned, artifacts = extract_artifacts(response)
    assert len(artifacts) == 1
    assert artifacts[0]["title"] == "Unclosed Document"
    assert "This artifact was never closed by the model." in artifacts[0]["content"]


def test_extract_artifacts_malformed_bracket():
    """Verify malformed opening bracket does not lose document content."""
    response = """Here is your draft:
<artifact type="markdown" title="Malformed Tag"
# Title of Document
Content inside malformed artifact."""
    cleaned, artifacts = extract_artifacts(response)
    assert len(artifacts) == 1
    assert "Content inside malformed artifact." in artifacts[0]["content"]


def test_extract_artifacts_fallback_essay_request():
    """Verify essay requested without tags extracts markdown safely."""
    response = """I have written the essay for you:

# The Ultimate Product-Led Growth Playbook
Product-led growth is about user self-serve activation.
Here are the core principles:
1. Shorten time to value.
2. Build virality loops.
3. Align pricing with metric growth.
In conclusion, PLG compounds over time."""
    cleaned, artifacts = extract_artifacts(response, user_request="Write a 1,250-word essay about product-led growth")
    assert len(artifacts) == 1
    assert artifacts[0]["title"] == "The Ultimate Product-Led Growth Playbook"
    assert "Product-led growth is about user self-serve activation." in artifacts[0]["content"]


def test_writing_tool_handler():
    """Verify writing tool handler generates valid artifact XML."""
    result = writing_tool.handler({
        "title": "Tool Generated Document",
        "artifact_type": "markdown",
        "content": "# Hello\nFrom Tool"
    }, None)
    assert '<artifact type="markdown" title="Tool Generated Document">' in result
    assert "# Hello\nFrom Tool" in result
    assert "</artifact>" in result


def mock_ollama_generate_essay(*args, **kwargs):
    response = """I have generated your essay:

<artifact type="markdown" title="Product-Led Growth Playbook">
# Product-Led Growth Playbook
Product-led growth (PLG) is a business methodology wherein user acquisition, expansion, conversion, and retention are all driven primarily by the product itself.

## 1. The Hook: Why PLG Wins
Traditional sales cycles create friction. PLG flips the funnel.

## 2. Core Takeaways
- Measure time to value (TTV).
- Never hide pricing from motivated buyers.
- Drive expansion through organic usage triggers.
</artifact>

Let me know if you would like any revisions!"""
    return response, "local (ollama)", "llama3"


@patch.object(PiFrameworkProvider, '__init__', return_value=None)
@patch.object(PiFrameworkProvider, 'generate_response', side_effect=mock_ollama_generate_essay)
def test_chat_creates_and_persists_artifact(mock_gen, mock_init, client: TestClient):
    res = client.post("/api/v1/chat", json={
        "message": "Write a 1,250-word essay about product-led growth using relevant Lenny sources",
        "provider": "local"
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["artifacts"]) == 1
    art = data["artifacts"][0]
    assert art["title"] == "Product-Led Growth Playbook"
    assert art["artifact_type"] == "markdown"
    assert "Product-Led Growth Playbook" in art["content"]
    assert "conversation_id" in art
    assert art["conversation_id"] == data["conversation_id"]
    assert art["message_id"] == data["assistant_message_id"]
    
    # Test retrieving the individual artifact
    art_res = client.get(f"/api/v1/artifacts/{art['id']}")
    assert art_res.status_code == 200
    assert art_res.json()["title"] == "Product-Led Growth Playbook"
    assert art_res.json()["message_id"] == data["assistant_message_id"]

    # Test listing artifacts for the conversation
    list_res = client.get(f"/api/v1/conversations/{data['conversation_id']}/artifacts")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert list_res.json()[0]["id"] == art["id"]

    # Test that get_messages returns the message with artifact attached
    msg_res = client.get(f"/api/v1/conversations/{data['conversation_id']}/messages")
    assert msg_res.status_code == 200
    messages = msg_res.json()
    assert len(messages) >= 2
    ast_msg = messages[1]
    assert ast_msg["role"] == "assistant"
    assert ast_msg["artifact"] is not None
    assert ast_msg["artifact"]["id"] == art["id"]


def test_get_artifact_not_found(client: TestClient):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/artifacts/{random_id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Artifact not found"


def test_list_artifacts_conversation_not_found(client: TestClient):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/conversations/{random_id}/artifacts")
    assert res.status_code == 404
