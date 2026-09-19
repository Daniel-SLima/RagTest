from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.rag.embeddings.base import EmbeddingProvider
from app.rag.embeddings.factory import create_embedding_provider
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def get_qdrant_service(request: Request) -> QdrantService:
    service = getattr(request.app.state, "qdrant", None)
    if service is None:
        raise RuntimeError("Qdrant service was not initialized")
    return service


def get_embedding_provider(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmbeddingProvider:
    provider = getattr(request.app.state, "embedding_provider", None)
    if provider is None:
        provider = create_embedding_provider(settings)
        request.app.state.embedding_provider = provider
    return provider


def get_vector_store(
    qdrant: Annotated[QdrantService, Depends(get_qdrant_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> QdrantVectorStore:
    return QdrantVectorStore(qdrant.client, settings.qdrant_collection)
