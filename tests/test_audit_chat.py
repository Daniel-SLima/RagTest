from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_audit_sink,
    get_conversation_service,
    get_embedding_provider,
    get_llm_provider,
    get_settings,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.conversation.models import ConversationSession, SessionSnapshot
from app.conversation.service import CompletedConversationTurn
from app.core.config import Settings
from app.main import app
from app.rag.chat import ChatResult
from app.rag.vector_store import SearchHit

SESSION_ID = UUID(int=17)


def completed_result() -> ChatResult:
    return ChatResult(
        answer="RESPOSTA_SECRET [1].",
        sources=[
            SearchHit(
                id="point-1",
                score=0.9,
                content="EXCERPT_SECRET",
                source="SOURCE_SECRET",
                category="category",
                audience=None,
                page=1,
                metadata={},
            )
        ],
        model="openai/gpt-oss-120b",
        grounded=True,
        citation_ids=[1],
        citation_retry_count=0,
        retrieval_queries=["retrieval query"],
    )


def completed_snapshot() -> SessionSnapshot:
    now = datetime(2026, 9, 25, tzinfo=UTC)
    return SessionSnapshot(
        ConversationSession(SESSION_ID, now, now, now + timedelta(days=7), 1),
        (),
    )


class MemoryAuditSink:
    def __init__(self, service: "PersistingService | None" = None) -> None:
        self.events = []
        self.service = service

    def emit(self, event) -> None:
        if self.service is not None:
            assert self.service.completed_before_audit is True
        self.events.append(event)


class PersistingService:
    def __init__(self) -> None:
        self.completed_before_audit = False

    async def run_turn(self, session_id, question, answerer):
        result = await answerer("contextual retrieval", "persisted history")
        self.completed_before_audit = True
        return CompletedConversationTurn(result, completed_snapshot())


@pytest.fixture
def fake_dependencies(monkeypatch: pytest.MonkeyPatch):
    answer = AsyncMock(return_value=completed_result())
    settings = Settings(_env_file=None, llm_provider="groq", retrieval_auto_decompose=False)
    app.dependency_overrides.update(
        {
            get_embedding_provider: lambda: object(),
            get_sparse_embedding_provider: lambda: object(),
            get_vector_store: lambda: object(),
            get_llm_provider: lambda: object(),
            get_settings: lambda: settings,
            get_conversation_service: lambda: PersistingService(),
        }
    )
    monkeypatch.setattr("app.api.routes.chat.answer_with_rag", answer)
    try:
        yield answer
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as value:
        yield value


@pytest.fixture
def audit_sink() -> MemoryAuditSink:
    return MemoryAuditSink()


def only_completed_event(audit_sink: MemoryAuditSink):
    events = [event for event in audit_sink.events if event.event_type == "chat.completed"]
    assert len(events) == 1
    return events[0]


def test_stateless_chat_emits_completed_event(
    client: TestClient,
    audit_sink: MemoryAuditSink,
    fake_dependencies,
) -> None:
    app.dependency_overrides[get_audit_sink] = lambda: audit_sink

    response = client.post("/v1/chat", json={"message": "PERGUNTA_SECRET"})

    assert response.status_code == 200
    fake_dependencies.assert_awaited_once()
    event = only_completed_event(audit_sink)
    assert event.session_id is None
    assert event.provider == "groq"
    assert event.model == "openai/gpt-oss-120b"
    assert event.grounded is True
    assert event.source_count == 1
    assert event.citation_count == 1
    assert event.citation_retry_count == 0
    assert event.retrieval_query_count == 1
    assert event.request_id == UUID(response.headers["X-Request-ID"])
    assert event.duration_ms >= 0
    serialized = event.to_json()
    for sentinel in ("PERGUNTA_SECRET", "RESPOSTA_SECRET", "EXCERPT_SECRET", "SOURCE_SECRET"):
        assert sentinel not in serialized


def test_session_chat_emits_after_turn_persistence(
    client: TestClient,
    audit_sink: MemoryAuditSink,
    fake_dependencies,
) -> None:
    service = PersistingService()
    audit_sink.service = service
    app.dependency_overrides[get_conversation_service] = lambda: service
    app.dependency_overrides[get_audit_sink] = lambda: audit_sink

    response = client.post(
        "/v1/chat",
        json={"message": "PERGUNTA_SECRET", "session_id": str(SESSION_ID)},
    )

    assert response.status_code == 200
    fake_dependencies.assert_awaited_once()
    event = only_completed_event(audit_sink)
    assert service.completed_before_audit is True
    assert event.session_id == SESSION_ID
