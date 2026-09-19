from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_embedding_provider, get_vector_store
from app.rag.embeddings.base import EmbeddingProvider
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore
from app.schemas.search import (
    SemanticSearchHit,
    SemanticSearchRequest,
    SemanticSearchResponse,
)

router = APIRouter(prefix="/v1", tags=["retrieval"])


@router.post(
    "/search",
    response_model=SemanticSearchResponse,
    summary="Semantic search over indexed source documents",
)
async def search_documents(
    request: SemanticSearchRequest,
    embeddings: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    vector_store: Annotated[QdrantVectorStore, Depends(get_vector_store)],
) -> SemanticSearchResponse:
    try:
        hits = await semantic_search(
            request.query,
            embeddings=embeddings,
            vector_store=vector_store,
            limit=request.limit,
            category=request.category,
            audience=request.audience,
            min_score=request.min_score,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return SemanticSearchResponse(
        query=request.query,
        results=[
            SemanticSearchHit(
                score=hit.score,
                content=hit.content,
                source=hit.source,
                category=hit.category,
                audience=hit.audience,
                page=hit.page,
                metadata=hit.metadata,
            )
            for hit in hits
        ],
    )
