import logging
import sys
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format='%(name)s: %(levelname)s - %(message)s', force=True, stream=sys.stdout)
logger = logging.getLogger("rag.diag")
logger.setLevel(logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import health, conversations, messages, knowledge, chat, artifacts

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: safely auto-ingest local transcript files and restore vector store
    try:
        from app.services.startup import run_startup_ingestion
        run_startup_ingestion()
    except Exception as e:
        logger.warning("Startup ingestion encountered error: %s", e)
    yield

app = FastAPI(title="The Lenny Growth Assistant API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(messages.router, prefix="/api/v1/conversations", tags=["messages"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(artifacts.router, prefix="/api/v1", tags=["artifacts"])
