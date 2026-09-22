from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.search import router as search_router
from app.api.routes.sessions import router as sessions_router
from app.conversation.service import ConversationService
from app.conversation.sqlite_store import SQLiteSessionStore
from app.core.config import get_settings
from app.services.qdrant_service import QdrantService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.qdrant = QdrantService(settings)
    app.state.session_store = SQLiteSessionStore(settings.session_db_path)
    await app.state.session_store.initialize()
    app.state.conversation_service = ConversationService(app.state.session_store, settings)
    app.state.embedding_provider = None
    app.state.sparse_embedding_provider = None
    app.state.llm_provider = None
    try:
        yield
    finally:
        await app.state.session_store.close()
        await app.state.qdrant.close()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API REST portável para o módulo RAG do RagTest.",
        lifespan=lifespan,
    )
    allowed_origins = [
        origin.strip()
        for origin in settings.cors_allowed_origins.split(",")
        if origin.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.include_router(health_router)
    application.include_router(search_router)
    application.include_router(chat_router)
    application.include_router(sessions_router)

    @application.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return application


app = create_app()
