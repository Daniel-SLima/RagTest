from datetime import UTC, datetime
from time import monotonic
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import (
    get_audit_sink,
    get_conversation_service,
    get_embedding_provider,
    get_llm_provider,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.catalog.services import load_catalog_or_none
from app.conversation.service import ConversationService
from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.observability.audit import AuditEvent, AuditSink, safe_emit
from app.observability.errors import NormalizedError, normalize_exception
from app.presentation import build_display, local_today, source_location_label, source_title
from app.rag.actions import build_actions, present_action
from app.rag.chat import ChatResult, answer_with_rag
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.retrieval_profiles import get_profile
from app.rag.vector_store import QdrantVectorStore
from app.schemas.chat import (
    ChatAction,
    ChatDisplay,
    ChatRequest,
    ChatResponse,
    ChatSafety,
    ChatSource,
)
from app.security.auth import enforce_chat_rate_limit

router = APIRouter(prefix="/v1", tags=["chat"])

_AUDIT_PROVIDERS = frozenset({"gemini", "groq", "ollama"})
_AUDIT_MODELS = frozenset(
    {
        "gemini-3.6-flash",
        "openai/gpt-oss-120b",
        "qwen3:8b",
    }
)


def _allowlisted_label(value: object, allowed: frozenset[str]) -> str | None:
    return value if isinstance(value, str) and value in allowed else None


def _emit_completed_event(
    request: Request,
    sink: AuditSink,
    settings: Settings,
    result: ChatResult,
    *,
    session_id,
    started_at: float,
) -> None:
    event = AuditEvent(
        event_id=uuid4(),
        timestamp=datetime.now(UTC),
        request_id=request.state.request_id,
        event_type="chat.completed",
        outcome="success",
        operation="chat",
        duration_ms=max(0, round((monotonic() - started_at) * 1000)),
        session_id=session_id,
        provider=_allowlisted_label(settings.llm_provider, _AUDIT_PROVIDERS),
        model=_allowlisted_label(result.model, _AUDIT_MODELS),
        grounded=result.grounded,
        source_count=len(result.sources),
        citation_count=len(result.citation_ids),
        citation_retry_count=result.citation_retry_count,
        retrieval_query_count=len(result.retrieval_queries or ()),
    )
    request.state.audit_event_emitted = True
    safe_emit(sink, event)


def _emit_failed_event(
    request: Request,
    sink: AuditSink,
    normalized: NormalizedError,
    *,
    session_id,
    started_at: float,
) -> None:
    event = AuditEvent(
        event_id=uuid4(),
        timestamp=datetime.now(UTC),
        request_id=request.state.request_id,
        event_type="chat.failed",
        outcome="failure",
        operation="chat",
        duration_ms=max(0, round((monotonic() - started_at) * 1000)),
        session_id=session_id,
        status_code=normalized.status_code,
        error_code=normalized.error_code,
        error_type=normalized.error_type,
    )
    request.state.audit_event_emitted = True
    safe_emit(sink, event)


@router.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(enforce_chat_rate_limit)],
)
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
    http_request: Request = None,
    audit_sink: Annotated[AuditSink | None, Depends(get_audit_sink)] = None,
) -> ChatResponse:
    started_at = monotonic()
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
            min_score=(
                request.min_score
                if request.min_score is not None
                else settings.retrieval_min_score
            ),
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
    except Exception as exc:  # noqa: BLE001 - normalize all chat failures centrally.
        normalized = normalize_exception(exc)
        if http_request is not None and audit_sink is not None:
            _emit_failed_event(
                http_request,
                audit_sink,
                normalized,
                session_id=request.session_id,
                started_at=started_at,
            )
        raise HTTPException(
            status_code=normalized.status_code,
            detail=normalized.public_detail,
        ) from None

    if http_request is not None and audit_sink is not None:
        _emit_completed_event(
            http_request,
            audit_sink,
            settings,
            result,
            session_id=response_session_id,
            started_at=started_at,
        )

    safety = result.safety
    today = local_today(settings.app_timezone)
    actions = [
        present_action(action, today=today)
        for action in build_actions(result, load_catalog_or_none(settings.source_dir))
    ]
    display = build_display(result)

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
                title=source_title(hit.source),
                location_label=source_location_label(hit.page),
            )
            for index, hit in enumerate(result.sources, start=1)
        ],
        safety=ChatSafety(
            triaged=bool(safety and safety.triggered),
            rule_id=safety.rule_id if safety else None,
            out_of_scope=result.out_of_scope,
        ),
        actions=[
            ChatAction(
                type=action.type,
                label=action.label,
                url=action.url,
                service_id=action.service_id,
                suggested_in_days=action.suggested_in_days,
                due_date=action.due_date,
                requires_host_app=action.requires_host_app,
                note=action.note,
            )
            for action in actions
        ],
        display=ChatDisplay(
            status=display.status,
            tone=display.tone,
            title=display.title,
            message=display.message,
        ),
    )
