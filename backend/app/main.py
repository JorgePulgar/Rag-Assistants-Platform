import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401 — registers all SQLAlchemy models with Base
from app.api.assistants import router as assistants_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.config import settings
from app.db import create_all_tables
from app.exceptions import AssistantNotFoundError, ConversationNotFoundError, DocumentNotFoundError

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up — creating database tables if needed")
    create_all_tables()
    yield
    logger.info("Shutting down")


app = FastAPI(title="RAG Assistants API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assistants_router)
app.include_router(documents_router)
app.include_router(chat_router)


@app.exception_handler(AssistantNotFoundError)
async def _assistant_not_found(request: Request, exc: AssistantNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DocumentNotFoundError)
async def _document_not_found(request: Request, exc: DocumentNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConversationNotFoundError)
async def _conversation_not_found(
    request: Request, exc: ConversationNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
