from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.conversation.service import ConversationService
from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.factory import create_llm_provider
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def get_qdrant_service(request: Request) -> QdrantService:
    service = getattr(request.app.state, "qdrant", None)
    if service is None:
        raise RuntimeError("Qdrant service was not initialized")
    return service


def get_conversation_service(request: Request) -> ConversationService:
    service = getattr(request.app.state, "conversation_service", None)
    if service is None:
        raise RuntimeError("Conversation service was not initialized")
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


def get_sparse_embedding_provider(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> SparseEmbeddingProvider:
    provider = getattr(request.app.state, "sparse_embedding_provider", None)
    if provider is None:
        provider = create_sparse_embedding_provider(settings)
        request.app.state.sparse_embedding_provider = provider
    return provider


def get_llm_provider(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> LLMProvider:
    provider = getattr(request.app.state, "llm_provider", None)
    if provider is None:
        try:
            provider = create_llm_provider(settings)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        request.app.state.llm_provider = provider
    return provider


def get_vector_store(
    qdrant: Annotated[QdrantService, Depends(get_qdrant_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> QdrantVectorStore:
    return QdrantVectorStore(qdrant.client, settings.qdrant_collection)
