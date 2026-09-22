"""Application service coordinating session lifecycle and completed RAG turns."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.conversation.context import build_conversation_context
from app.conversation.models import NewTurn, SessionSnapshot, StoredSource
from app.conversation.store import SessionStore
from app.core.config import Settings
from app.rag.chat import ChatResult

RagAnswerer = Callable[[str, str | None], Awaitable[ChatResult]]


@dataclass(frozen=True, slots=True)
class CompletedConversationTurn:
    """RAG result paired with the snapshot committed after generation."""

    result: ChatResult
    snapshot: SessionSnapshot


def utc_now() -> datetime:
    """Return the current timezone-aware UTC instant."""
    return datetime.now(UTC)


def new_turn_from_result(question: str, result: ChatResult) -> NewTurn:
    """Copy the public, persistence-safe ChatResult fields into a completed turn."""
    return NewTurn(
        question=question,
        answer=result.answer,
        model=result.model,
        grounded=result.grounded,
        citation_ids=tuple(result.citation_ids),
        citation_retry_count=result.citation_retry_count,
        multi_query_used=result.multi_query_used,
        retrieval_queries=tuple(result.retrieval_queries or (question,)),
        decomposition_status=result.decomposition_status,
        sources=tuple(
            StoredSource(
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
        ),
    )


class ConversationService:
    """Coordinate retention, leases, bounded context and atomic turn completion."""

    def __init__(
        self,
        store: SessionStore,
        settings: Settings,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._store = store
        self._settings = settings
        self._clock = clock

    async def create_session(self) -> SessionSnapshot:
        """Purge a bounded expired batch, then create a fresh session."""
        now = self._clock()
        await self._store.purge_expired(now=now, limit=100)
        return await self._store.create(
            now=now,
            expires_at=now + timedelta(days=self._settings.session_retention_days),
        )

    async def get_session(self, session_id: UUID) -> SessionSnapshot:
        """Load a session using the service clock for expiry decisions."""
        return await self._store.get(session_id, now=self._clock())

    async def delete_session(self, session_id: UUID) -> None:
        """Delete a session using the service clock for expiry decisions."""
        await self._store.delete(session_id, now=self._clock())

    async def run_turn(
        self,
        session_id: UUID,
        question: str,
        answerer: RagAnswerer,
    ) -> CompletedConversationTurn:
        """Generate and persist exactly one completed turn under an exclusive lease."""
        now = self._clock()
        lease = await self._store.acquire(
            session_id,
            now=now,
            lease_until=now + timedelta(seconds=self._settings.session_lease_seconds),
        )
        try:
            context = build_conversation_context(
                lease.snapshot.turns,
                current_question=question,
                max_turns=self._settings.session_context_turns,
                max_chars=self._settings.session_context_max_chars,
            )
            result = await answerer(context.retrieval_query, context.prompt_history)
            completed_at = self._clock()
            snapshot = await self._store.complete(
                lease,
                new_turn_from_result(question, result),
                now=completed_at,
                expires_at=completed_at + timedelta(days=self._settings.session_retention_days),
                max_turns=self._settings.session_max_stored_turns,
            )
            return CompletedConversationTurn(result=result, snapshot=snapshot)
        except Exception:
            await self._store.release(lease)
            raise
