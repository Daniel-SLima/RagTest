"""REST lifecycle endpoints for opaque conversation sessions."""

from datetime import UTC, datetime
from time import monotonic
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_audit_sink, get_conversation_service
from app.conversation.models import SessionExpiredError, SessionNotFoundError, SessionSnapshot
from app.conversation.service import ConversationService
from app.observability.audit import AuditEvent, AuditSink, safe_emit
from app.schemas.chat import ChatSource
from app.schemas.session import SessionResponse, SessionTurnResponse

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


def _request_duration_ms(request: Request) -> int:
    started_at = request.state.request_started_at
    return max(0, round((monotonic() - started_at) * 1000))


def _emit_session_event(
    request: Request,
    sink: AuditSink,
    *,
    event_type: str,
    operation: str,
    session_id: UUID,
    turn_count: int | None = None,
) -> None:
    safe_emit(
        sink,
        AuditEvent(
            event_id=uuid4(),
            timestamp=datetime.now(UTC),
            request_id=request.state.request_id,
            event_type=event_type,
            outcome="success",
            operation=operation,
            duration_ms=_request_duration_ms(request),
            session_id=session_id,
            turn_count=turn_count,
        ),
    )


def to_session_response(snapshot: SessionSnapshot) -> SessionResponse:
    return SessionResponse(
        session_id=snapshot.session.session_id,
        created_at=snapshot.session.created_at,
        updated_at=snapshot.session.updated_at,
        expires_at=snapshot.session.expires_at,
        turns=[
            SessionTurnResponse(
                turn_id=turn.turn_id,
                sequence=turn.sequence,
                question=turn.question,
                answer=turn.answer,
                created_at=turn.created_at,
                model=turn.model,
                grounded=turn.grounded,
                citation_ids=list(turn.citation_ids),
                citation_retry_count=turn.citation_retry_count,
                multi_query_used=turn.multi_query_used,
                retrieval_queries=list(turn.retrieval_queries),
                decomposition_status=turn.decomposition_status,
                sources=[
                    ChatSource(
                        citation_id=source.citation_id,
                        score=source.score,
                        source=source.source,
                        category=source.category,
                        audience=source.audience,
                        page=source.page,
                        chunk_count=source.chunk_count,
                        excerpt=source.excerpt,
                    )
                    for source in turn.sources
                ],
            )
            for turn in snapshot.turns
        ],
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: Request,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    audit_sink: Annotated[AuditSink, Depends(get_audit_sink)],
) -> SessionResponse:
    snapshot = await service.create_session()
    _emit_session_event(
        request,
        audit_sink,
        event_type="session.created",
        operation="session.create",
        session_id=snapshot.session.session_id,
    )
    return to_session_response(snapshot)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    request: Request,
    session_id: UUID,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    audit_sink: Annotated[AuditSink, Depends(get_audit_sink)],
) -> SessionResponse:
    try:
        snapshot = await service.get_session(session_id)
        _emit_session_event(
            request,
            audit_sink,
            event_type="session.read",
            operation="session.read",
            session_id=snapshot.session.session_id,
            turn_count=len(snapshot.turns),
        )
        return to_session_response(snapshot)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found.") from exc
    except SessionExpiredError as exc:
        raise HTTPException(status_code=410, detail="Session expired.") from exc


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    request: Request,
    session_id: UUID,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    audit_sink: Annotated[AuditSink, Depends(get_audit_sink)],
) -> None:
    try:
        await service.delete_session(session_id)
        _emit_session_event(
            request,
            audit_sink,
            event_type="session.deleted",
            operation="session.delete",
            session_id=session_id,
        )
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found.") from exc
    except SessionExpiredError as exc:
        raise HTTPException(status_code=410, detail="Session expired.") from exc
