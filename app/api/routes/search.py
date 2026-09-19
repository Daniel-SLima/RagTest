from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_embedding_provider, get_vector_store
from app.core.config import Settings, get_settings
from app.rag.embeddings.base import EmbeddingProvider
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore
from app.schemas.search import SemanticSearchHit, SemanticSearchRequest, SemanticSearchResponse

router = APIRouter(prefix="/v1", tags=["retrieval"])


@router.post("/search", response_model=SemanticSearchResponse)
async def search_documents(
    request: SemanticSearchRequest,
    embeddings: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    vector_store: Annotated[QdrantVectorStore, Depends(get_vector_store)],
    settings: Annotated[Settings, Depends(get_settings)],
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
            candidate_multiplier=settings.retrieval_candidate_multiplier,
            score_margin=settings.retrieval_score_margin,
            merge_same_page=settings.retrieval_merge_same_page,
            max_group_chars=settings.retrieval_max_group_chars,
            source_lexical_weight=settings.retrieval_source_lexical_weight,
            content_lexical_weight=settings.retrieval_content_lexical_weight,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return SemanticSearchResponse(
        query=request.query,
        results=[
            SemanticSearchHit(
                score=hit.score,
                rank_score=hit.rank_score,
                content=hit.content,
                source=hit.source,
                category=hit.category,
                audience=hit.audience,
                page=hit.page,
                chunk_count=hit.chunk_count,
                metadata=hit.metadata,
            )
            for hit in hits
        ],
    )
