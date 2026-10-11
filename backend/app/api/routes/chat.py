import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.schemas.rag import SearchQuery
from app.services.llm import get_llm_provider
from app.services.vector_store import get_vector_store
from app.services.retrieval import RetrievalService
from app.services.writing import WRITING_SKILL_PROMPT, extract_artifacts
from app.models.artifact import Artifact
from app.schemas.artifact import ArtifactResponse
from app.core.config import settings
from datetime import datetime, timezone
import json
import time

router = APIRouter()
logger = logging.getLogger("rag.diag")

SYSTEM_PROMPT = """You are The Lenny Growth Assistant. Your job is to answer product management and growth questions using the provided retrieved context from Lenny's Podcast transcripts.
You must strictly prioritize the retrieved evidence. Distinguish clearly between evidence from the context (explicitly citing the speaker/guest and episode) and your own general reasoning or suggestions.

SUMMARIZATION & GROUNDING GUIDELINES:
- When asked to summarize Lenny's podcast or specific episodes, summarize only the key ideas, frameworks, actionable takeaways, and concrete examples from the provided context without inventing claims.
- If the retrieved context contains excerpts from specific episodes (e.g. Brian Chesky, Elena Verna, or Lenny Rachitsky), summarize what they actually said and clearly attribute their points.
- If the retrieved context does not contain sufficient information to answer the question, or if no relevant podcast transcripts were found, explicitly state this limitation and invite the user to ask about specific guests, episodes, or topics. You may then optionally provide general product advice, but clearly indicate that it is not from Lenny's podcast.
- Never invent podcast quotations, episode titles, URLs, timestamps, or citations.
- Do not cite or reuse sources from previous turns unless they are present in the context retrieved for this turn.
- Keep regular conversational answers concise and structured, but when the user requests an essay, article, or document, you must follow the WRITING SKILL INSTRUCTIONS below to generate a comprehensive, structured artifact.

""" + WRITING_SKILL_PROMPT

def is_podcast_summary_query(text: str) -> bool:
    """Detects whether a user prompt requests a general overview or summary of Lenny's podcast."""
    t = text.lower()
    summary_phrases = [
        "summarize lenny's podcast", "summarize lennys podcast",
        "summarize the podcast", "podcast summary", "summarize podcast",
        "overview of the podcast", "what is lenny's podcast about",
        "summarize all episodes", "summary of lenny's podcast",
        "tell me about lenny's podcast", "overview of lenny's podcast",
        "what does lenny discuss", "what is covered in the podcast"
    ]
    return any(p in t for p in summary_phrases)

@router.post("", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    req_start_time = time.perf_counter()
    logger.info(f"TIMING: [chat_endpoint] Start request provider={req.provider} model={req.model}")
    # 1. Conversation Management
    conversation_id = req.conversation_id
    if conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        conv = Conversation(title=req.message[:50])
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = conv.id

    # Add User Message to DB
    user_msg = Message(conversation_id=conversation_id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Retrieval & Grounding
    rag_start = time.perf_counter()
    citations = []
    retrieved_text = "No relevant context found in Lenny's Podcast transcripts."
    
    try:
        from app.api.routes.knowledge import get_embedding_provider as knowledge_get_embed
        emb_provider = knowledge_get_embed()
    except Exception:
        emb_provider = None

    context_blocks = []
    if emb_provider:
        vs = get_vector_store()
        retrieval_service = RetrievalService(vs, emb_provider)
        
        if is_podcast_summary_query(req.message):
            results = retrieval_service.get_representative_chunks(limit=3)
            logger.info("RAG_DIAG: Broad podcast summary query detected - retrieved %d representative chunks", len(results))
        else:
            raw_results = retrieval_service.search(SearchQuery(query=req.message, top_k=3))
            # Relevance filtering: only retain chunks with cosine similarity >= 0.22
            results = [r for r in raw_results if r.score >= 0.22]
            logger.info("RAG_DIAG: query='%s' raw_results=%d filtered_results=%d (threshold=0.22)",
                        req.message[:80], len(raw_results), len(results))

        for i, r in enumerate(results):
            meta = r.chunk.metadata
            logger.info("RAG_DIAG: chunk[%d] score=%.4f title='%s' speaker='%s' ts='%s' doc_id='%s'",
                        i, r.score,
                        meta.episode_title or 'N/A',
                        meta.speaker or 'N/A',
                        meta.timestamp or 'N/A',
                        r.chunk.document_id)
            citations.append(Citation(
                episode_title=meta.episode_title,
                url=meta.url,
                speaker=meta.speaker,
                timestamp=meta.timestamp,
                content=r.chunk.text
            ))
            source_parts = [f"Source: {meta.episode_title or 'Unknown'}"]
            if meta.speaker:
                source_parts.append(f"Speaker: {meta.speaker}")
            if meta.timestamp:
                source_parts.append(f"Timestamp: {meta.timestamp}")
            if meta.url:
                source_parts.append(f"URL: {meta.url}")
            source_str = " | ".join(source_parts)
            context_blocks.append(f"[{source_str}]\n{r.chunk.text}")
            
        if results:
            retrieved_text = "\n\n".join(context_blocks)
            logger.info("RAG_DIAG: context_length=%d chars reached LLM", len(retrieved_text))
        else:
            logger.info("RAG_DIAG: NO chunks passed relevance threshold - LLM will receive no context")
            retrieved_text = "No relevant context found in Lenny's Podcast transcripts."
    else:
        logger.warning("RAG_DIAG: embedding_provider is None - retrieval skipped")
        retrieved_text = "No relevant context found in Lenny's Podcast transcripts."
        
    rag_time = time.perf_counter() - rag_start
    logger.info(f"TIMING: [chat_endpoint] RAG Total Latency: {rag_time:.4f}s")

    # 3. LLM Generation
    try:
        llm = get_llm_provider(req.provider, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider configuration error: {e}")

    history = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    messages = [{"role": h.role, "content": h.content} for h in history[:-1]]

    user_prompt = f"Context Information:\n{retrieved_text}\n\nUser Question:\n{req.message}"
    messages.append({"role": "user", "content": user_prompt})

    if getattr(req, "stream", False):
        from fastapi.responses import StreamingResponse
        import threading
        import queue
        from app.db.session import SessionLocal

        def stream_generator():
            q = queue.Queue()
            state = {"in_think": False, "buffer": ""}
            
            def on_event(event_type, payload):
                if event_type == "assistant_delta":
                    state["buffer"] += payload
                    while True:
                        if not state["in_think"]:
                            if "<think>" in state["buffer"]:
                                pre, post = state["buffer"].split("<think>", 1)
                                if pre:
                                    q.put({"type": "text_delta", "text": pre})
                                state["in_think"] = True
                                state["buffer"] = post
                                q.put({"type": "status", "message": "Thinking..."})
                            elif any(state["buffer"].endswith("<" + s) for s in ["", "t", "th", "thi", "thin", "think"]):
                                break
                            else:
                                if state["buffer"]:
                                    q.put({"type": "text_delta", "text": state["buffer"]})
                                    state["buffer"] = ""
                                break
                        else:
                            if "</think>" in state["buffer"]:
                                pre, post = state["buffer"].split("</think>", 1)
                                state["in_think"] = False
                                state["buffer"] = post
                                q.put({"type": "status", "message": "Generating your answer..."})
                            else:
                                prefixes = ["</think", "</thin", "</thi", "</th", "</t", "</", "<"]
                                match = ""
                                for p in prefixes:
                                    if state["buffer"].endswith(p):
                                        match = p
                                        break
                                state["buffer"] = match
                                break
                elif event_type == "tool_call":
                    tool_name = getattr(payload, "name", "")
                    if tool_name in ["write_artifact", "create_artifact"]:
                        q.put({"type": "status", "message": "Drafting your artifact..."})

            def run_agent():
                try:
                    q.put({"type": "status", "message": "Generating your answer..."})
                    resp_text, actual_prov, mod_name = llm.generate_streamed_response(SYSTEM_PROMPT, messages, on_event)
                    if state["buffer"]:
                        q.put({"type": "text_delta", "text": state["buffer"]})
                        state["buffer"] = ""
                    q.put({"type": "agent_done", "response_text": resp_text, "provider": actual_prov, "model": mod_name})
                except Exception as e:
                    q.put({"type": "error", "message": str(e)})

            thread = threading.Thread(target=run_agent, daemon=True)
            thread.start()
            
            yield f"data: {json.dumps({'type': 'init', 'conversationId': str(conversation_id), 'citations': [c.model_dump() for c in citations]})}\n\n"
            
            while True:
                try:
                    event = q.get(timeout=settings.LLM_TIMEOUT_SECONDS)
                except queue.Empty:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Response generation timed out. Please try again.'})}\n\n"
                    break

                if event["type"] == "agent_done":
                    db_stream = SessionLocal()
                    try:
                        resp_text = event["response_text"]
                        actual_provider = event["provider"]
                        model_name = event["model"]
                        
                        cleaned, extracted = extract_artifacts(resp_text, user_request=req.message)
                        
                        ast_msg_stream = Message(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=cleaned,
                            citations_json=json.dumps([c.model_dump() for c in citations]) if citations else None
                        )
                        db_stream.add(ast_msg_stream)
                        db_stream.commit()
                        db_stream.refresh(ast_msg_stream)
                        
                        saved_artifacts = []
                        for art in extracted:
                            db_art = Artifact(
                                conversation_id=conversation_id,
                                message_id=ast_msg_stream.id,
                                title=art["title"],
                                artifact_type=art["type"],
                                content=art["content"]
                            )
                            db_stream.add(db_art)
                            db_stream.commit()
                            db_stream.refresh(db_art)
                            saved_artifacts.append(ArtifactResponse(
                                id=db_art.id, conversation_id=db_art.conversation_id,
                                message_id=db_art.message_id, title=db_art.title,
                                artifact_type=db_art.artifact_type, content=db_art.content,
                                version=db_art.version, created_at=db_art.created_at, updated_at=db_art.updated_at
                            ))
                        
                        conv_stream = db_stream.query(Conversation).filter(Conversation.id == conversation_id).first()
                        if conv_stream:
                            conv_stream.updated_at = datetime.now(timezone.utc)
                            db_stream.commit()
                            
                        # Format dates properly using pydantic model_dump with mode='json'
                        yield f"data: {json.dumps({'type': 'done', 'data': {'id': str(ast_msg_stream.id), 'content': cleaned, 'artifacts': [a.model_dump(mode='json') for a in saved_artifacts], 'citations': [c.model_dump(mode='json') for c in citations]}})}\n\n"
                        yield "data: [DONE]\n\n"
                    finally:
                        db_stream.close()
                    break
                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']})}\n\n"
                    break
                else:
                    yield f"data: {json.dumps(event)}\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    llm_start = time.perf_counter()
    try:
        response_text, actual_provider, model_name = llm.generate_response(SYSTEM_PROMPT, messages)
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "Authentication" in error_str:
            raise HTTPException(status_code=401, detail=f"Authentication error: {e}")
        elif "404" in error_str or "not found" in error_str.lower() or "invalid model" in error_str.lower():
            raise HTTPException(status_code=400, detail=f"Model unavailable or invalid: {e}")
        raise HTTPException(status_code=502, detail=f"Provider request failed: {e}")

    llm_time = time.perf_counter() - llm_start
    logger.info(f"TIMING: [chat_endpoint] LLM Total Latency: {llm_time:.4f}s")
    
    cleaned_response_text, extracted_artifacts = extract_artifacts(response_text, user_request=req.message)

    ast_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=cleaned_response_text,
        citations_json=json.dumps([c.model_dump() for c in citations]) if citations else None
    )
    db.add(ast_msg)
    db.commit()
    db.refresh(ast_msg)
    
    saved_artifacts = []
    try:
        for art in extracted_artifacts:
            db_art = Artifact(
                conversation_id=conversation_id,
                message_id=ast_msg.id,
                title=art["title"],
                artifact_type=art["type"],
                content=art["content"]
            )
            db.add(db_art)
            db.commit()
            db.refresh(db_art)
            saved_artifacts.append(
                ArtifactResponse(
                    id=db_art.id,
                    conversation_id=db_art.conversation_id,
                    message_id=db_art.message_id,
                    title=db_art.title,
                    artifact_type=db_art.artifact_type,
                    content=db_art.content,
                    version=db_art.version,
                    created_at=db_art.created_at,
                    updated_at=db_art.updated_at
                )
            )
    except Exception as e:
        db.rollback()
        logger.error("Failed to persist artifacts: %s", e)

    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ast_msg)

    req_time = time.perf_counter() - req_start_time
    logger.info(f"TIMING: [chat_endpoint] Request Total Latency: {req_time:.4f}s")

    return ChatResponse(
        conversation_id=conversation_id,
        user_message_id=user_msg.id,
        assistant_message_id=ast_msg.id,
        response_text=cleaned_response_text,
        citations=citations,
        artifacts=saved_artifacts,
        provider=actual_provider,
        model=model_name
    )

