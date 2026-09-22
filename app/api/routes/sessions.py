"""REST lifecycle endpoints for opaque conversation sessions."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_conversation_service
from app.conversation.models import SessionExpiredError, SessionNotFoundError, SessionSnapshot
from app.conversation.service import ConversationService
from app.schemas.chat import ChatSource
from app.schemas.session import SessionResponse, SessionTurnResponse

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


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
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> SessionResponse:
    return to_session_response(await service.create_session())


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> SessionResponse:
    try:
        return to_session_response(await service.get_session(session_id))
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found.") from exc
    except SessionExpiredError as exc:
        raise HTTPException(status_code=410, detail="Session expired.") from exc


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> None:
    try:
        await service.delete_session(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found.") from exc
    except SessionExpiredError as exc:
        raise HTTPException(status_code=410, detail="Session expired.") from exc
