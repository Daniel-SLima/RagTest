from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_conversation_service,
    get_embedding_provider,
    get_llm_provider,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.conversation.models import (
    SessionBusyError,
    SessionConflictError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.conversation.service import ConversationService
from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider, LLMServiceUnavailableError
from app.rag.chat import answer_with_rag
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.retrieval_profiles import get_profile
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
    conversation_service: Annotated[
        ConversationService, Depends(get_conversation_service)
    ],
) -> ChatResponse:
    profile = get_profile(settings.retrieval_mode)
    auto_decompose = (
        settings.retrieval_auto_decompose
        if request.auto_decompose is None
        else request.auto_decompose
    )

    async def run_rag(retrieval_question: str, conversation_context: str | None):
        return await answer_with_rag(
            request.message,
            retrieval_question=retrieval_question,
            conversation_context=conversation_context,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings if profile.use_sparse else None,
            vector_store=vector_store,
            llm=llm,
            limit=request.limit,
            category=request.category,
            audience=request.audience,
            min_score=request.min_score,
            candidate_multiplier=profile.candidate_multiplier,
            score_margin=profile.score_margin,
            merge_same_page=settings.retrieval_merge_same_page,
            max_group_chars=settings.retrieval_max_group_chars,
            source_lexical_weight=profile.source_lexical_weight,
            content_lexical_weight=profile.content_lexical_weight,
            hybrid_dense_weight=profile.dense_weight,
            hybrid_sparse_weight=profile.sparse_weight,
            auto_decompose=auto_decompose,
            max_subqueries=settings.retrieval_max_subqueries,
        )

    try:
        if request.session_id is None:
            result = await run_rag(request.message, None)
            response_session_id = None
        else:
            completed = await conversation_service.run_turn(
                request.session_id,
                request.message,
                run_rag,
            )
            result = completed.result
            response_session_id = request.session_id
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found.") from exc
    except SessionBusyError as exc:
        raise HTTPException(status_code=409, detail="Session is busy.") from exc
    except SessionConflictError as exc:
        raise HTTPException(status_code=409, detail="Session conflict.") from exc
    except SessionExpiredError as exc:
        raise HTTPException(status_code=410, detail="Session expired.") from exc
    except LLMServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider request failed.",
        ) from exc

    return ChatResponse(
        session_id=response_session_id,
        answer=result.answer,
        model=result.model,
        grounded=result.grounded,
        citation_ids=result.citation_ids,
        citation_retry_count=result.citation_retry_count,
        multi_query_used=result.multi_query_used,
        retrieval_queries=result.retrieval_queries or [request.message],
        decomposition_status=result.decomposition_status,
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
