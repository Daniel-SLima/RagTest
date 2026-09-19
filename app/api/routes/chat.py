from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_embedding_provider,
    get_llm_provider,
    get_vector_store,
)
from app.llm.base import LLMProvider
from app.rag.chat import answer_with_rag
from app.rag.embeddings.base import EmbeddingProvider
from app.rag.vector_store import QdrantVectorStore
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Grounded RAG chat over the indexed document base",
)
async def chat(
    request: ChatRequest,
    embeddings: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    vector_store: Annotated[QdrantVectorStore, Depends(get_vector_store)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> ChatResponse:
    try:
        result = await answer_with_rag(
            request.message,
            embeddings=embeddings,
            vector_store=vector_store,
            llm=llm,
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
                excerpt=" ".join(hit.content.split())[:500],
            )
            for index, hit in enumerate(result.sources, start=1)
        ],
    )
