from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_embedding_provider,
    get_llm_provider,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.rag.chat import answer_with_rag
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.vector_store import QdrantVectorStore
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    embeddings: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    sparse_embeddings: Annotated[
        SparseEmbeddingProvider,
        Depends(get_sparse_embedding_provider),
    ],
    vector_store: Annotated[QdrantVectorStore, Depends(get_vector_store)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse:
    try:
        result = await answer_with_rag(
            request.message,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings,
            vector_store=vector_store,
            llm=llm,
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
            hybrid_dense_weight=settings.hybrid_dense_weight,
            hybrid_sparse_weight=settings.hybrid_sparse_weight,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider request failed.",
        ) from exc

    return ChatResponse(
        answer=result.answer,
        model=result.model,
        sources=[
            ChatSource(
                citation_id=index,
                score=hit.score,
                source=hit.source,
                category=hit.category,
                audience=hit.audience,
                page=hit.page,
                chunk_count=hit.chunk_count,
                excerpt=" ".join(hit.content.split())[:500],
            )
            for index, hit in enumerate(result.sources, start=1)
        ],
    )
