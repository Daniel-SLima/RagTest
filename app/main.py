from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.search import router as search_router
from app.core.config import get_settings
from app.services.qdrant_service import QdrantService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.qdrant = QdrantService(settings)
    app.state.embedding_provider = None
    app.state.llm_provider = None
    try:
        yield
    finally:
        await app.state.qdrant.close()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API REST portável para o módulo RAG do RagTest.",
        lifespan=lifespan,
    )
    application.include_router(health_router)
    application.include_router(search_router)
    application.include_router(chat_router)

    @application.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return application


app = create_app()
