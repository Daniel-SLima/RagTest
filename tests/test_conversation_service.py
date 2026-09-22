from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.conversation.models import (
    ConversationSession,
    ConversationTurn,
    NewTurn,
    SessionBusyError,
    SessionLease,
    SessionSnapshot,
    StoredSource,
)
from app.conversation.service import ConversationService, new_turn_from_result
from app.core.config import Settings
from app.llm.base import LLMServiceUnavailableError
from app.rag.chat import ChatResult
from app.rag.vector_store import SearchHit

SESSION_ID = UUID(int=42)
NOW = datetime(2026, 9, 22, tzinfo=UTC)


def sample_chat_result() -> ChatResult:
    return ChatResult(
        answer="Resposta [1].",
        sources=[SearchHit("point-1", 0.9, "Trecho   documental", "guia.pdf", "saude", "mulher", 2, {}, 2)],
        model="fake-model",
        grounded=True,
        citation_ids=[1],
        citation_retry_count=1,
        multi_query_used=True,
        retrieval_queries=["Pergunta contextual"],
        decomposition_status="used",
    )


def empty_snapshot() -> SessionSnapshot:
    return SessionSnapshot(
        ConversationSession(SESSION_ID, NOW, NOW, NOW + timedelta(days=7), 0),
        (),
    )


def snapshot_with_one_turn() -> SessionSnapshot:
    turn = ConversationTurn(
        UUID(int=1), 1, "Quais exames?", "Mamografia [1].", NOW, "fake-model", True,
        (1,), 0, False, ("Quais exames?",), "not-needed", (),
    )
    return replace(empty_snapshot(), turns=(turn,))


def settings() -> Settings:
    return Settings(_env_file=None)


def fixed_clock() -> datetime:
    return NOW


def conversation_turn_from_new(turn: NewTurn, *, sequence: int, now: datetime) -> ConversationTurn:
    return ConversationTurn(
        UUID(int=sequence), sequence, turn.question, turn.answer, now, turn.model,
        turn.grounded, turn.citation_ids, turn.citation_retry_count, turn.multi_query_used,
        turn.retrieval_queries, turn.decomposition_status, turn.sources,
    )


class FakeSessionStore:
    def __init__(self, snapshot: SessionSnapshot) -> None:
        self.snapshot = snapshot
        self.completed: list[NewTurn] = []
        self.released_tokens: list[UUID] = []
        self.last_lease: SessionLease | None = None
        self.calls: list[tuple[object, ...]] = []
        self.acquire_error: Exception | None = None

    async def purge_expired(self, *, now: datetime, limit: int = 100) -> int:
        self.calls.append(("purge", now, limit))
        return 0

    async def create(self, *, now: datetime, expires_at: datetime) -> SessionSnapshot:
        self.calls.append(("create", now, expires_at))
        return self.snapshot

    async def get(self, session_id: UUID, *, now: datetime) -> SessionSnapshot:
        self.calls.append(("get", session_id, now))
        return self.snapshot

    async def delete(self, session_id: UUID, *, now: datetime) -> None:
        self.calls.append(("delete", session_id, now))

    async def acquire(self, session_id: UUID, *, now: datetime, lease_until: datetime) -> SessionLease:
        self.calls.append(("acquire", session_id, now, lease_until))
        if self.acquire_error:
            raise self.acquire_error
        self.last_lease = SessionLease(session_id, UUID(int=99), self.snapshot.session.revision, self.snapshot)
        return self.last_lease

    async def complete(
        self, lease: SessionLease, turn: NewTurn, *, now: datetime,
        expires_at: datetime, max_turns: int,
    ) -> SessionSnapshot:
        self.calls.append(("complete", lease, now, expires_at, max_turns))
        self.completed.append(turn)
        return replace(
            self.snapshot,
            turns=(*self.snapshot.turns, conversation_turn_from_new(turn, sequence=2, now=now)),
        )

    async def release(self, lease: SessionLease) -> None:
        self.released_tokens.append(lease.token)


@pytest.mark.asyncio
async def test_run_turn_builds_context_and_persists_success() -> None:
    store = FakeSessionStore(snapshot_with_one_turn())
    service = ConversationService(store, settings(), clock=fixed_clock)
    answerer = AsyncMock(return_value=sample_chat_result())

    completed = await service.run_turn(SESSION_ID, "E com que frequência?", answerer)

    retrieval_query, prompt_history = answerer.await_args.args
    assert retrieval_query.endswith("Pergunta atual: E com que frequência?")
    assert "[1]" not in prompt_history
    assert completed.snapshot.turns[-1].question == "E com que frequência?"
    assert store.completed == [new_turn_from_result("E com que frequência?", sample_chat_result())]


@pytest.mark.asyncio
async def test_run_turn_releases_lease_without_partial_turn_on_failure() -> None:
    store = FakeSessionStore(empty_snapshot())
    service = ConversationService(store, settings(), clock=fixed_clock)

    async def fail(_query: str, _history: str | None) -> ChatResult:
        raise LLMServiceUnavailableError("unavailable")

    with pytest.raises(LLMServiceUnavailableError):
        await service.run_turn(SESSION_ID, "Pergunta", fail)
    assert store.completed == []
    assert store.released_tokens == [store.last_lease.token]


@pytest.mark.asyncio
async def test_create_get_and_delete_forward_clock_and_retention() -> None:
    store = FakeSessionStore(empty_snapshot())
    service = ConversationService(store, settings(), clock=fixed_clock)

    await service.create_session()
    await service.get_session(SESSION_ID)
    await service.delete_session(SESSION_ID)

    assert store.calls == [
        ("purge", NOW, 100),
        ("create", NOW, NOW + timedelta(days=7)),
        ("get", SESSION_ID, NOW),
        ("delete", SESSION_ID, NOW),
    ]


def test_new_turn_from_result_copies_every_public_chat_field() -> None:
    turn = new_turn_from_result("Pergunta", sample_chat_result())

    assert turn == NewTurn(
        "Pergunta", "Resposta [1].", "fake-model", True, (1,), 1, True,
        ("Pergunta contextual",), "used",
        (StoredSource(1, 0.9, "guia.pdf", "saude", "mulher", 2, 2, "Trecho documental"),),
    )


@pytest.mark.asyncio
async def test_run_turn_propagates_busy_without_calling_answerer() -> None:
    store = FakeSessionStore(empty_snapshot())
    store.acquire_error = SessionBusyError()
    answerer = AsyncMock(return_value=sample_chat_result())

    with pytest.raises(SessionBusyError):
        await ConversationService(store, settings(), clock=fixed_clock).run_turn(
            SESSION_ID, "Pergunta", answerer
        )

    answerer.assert_not_awaited()
