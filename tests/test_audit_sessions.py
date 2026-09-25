from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_audit_sink, get_conversation_service
from app.conversation.models import (
    ConversationSession,
    ConversationTurn,
    SessionExpiredError,
    SessionNotFoundError,
    SessionSnapshot,
    StoredSource,
)
from app.main import app

SESSION_ID = UUID(int=7)
REQUEST_ID = UUID(int=8)
NOW = datetime(2026, 9, 22, tzinfo=UTC)


class MemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def emit(self, event: Any) -> None:
        self.events.append(event)


def snapshot_with_three_turns() -> SessionSnapshot:
    source = StoredSource(
        citation_id=1,
        score=0.9,
        source="SOURCE_SECRET",
        category="category",
        audience=None,
        page=1,
        chunk_count=1,
        excerpt="EXCERPT_SECRET",
    )
    turns = tuple(
        ConversationTurn(
            turn_id=UUID(int=index),
            sequence=index,
            question="PERGUNTA_SECRET",
            answer="RESPOSTA_SECRET",
            created_at=NOW,
            model="openai/gpt-oss-120b",
            grounded=True,
            citation_ids=(1,),
            citation_retry_count=0,
            multi_query_used=False,
            retrieval_queries=("PERGUNTA_SECRET",),
            decomposition_status="not-needed",
            sources=(source,),
        )
        for index in range(1, 4)
    )
    return SessionSnapshot(
        ConversationSession(SESSION_ID, NOW, NOW, NOW + timedelta(days=7), 3),
        turns,
    )


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as value:
        yield value


@pytest.fixture
def service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def audit_sink() -> MemoryAuditSink:
    return MemoryAuditSink()


@pytest.fixture
def overrides(service: AsyncMock, audit_sink: MemoryAuditSink):
    app.dependency_overrides[get_conversation_service] = lambda: service
    app.dependency_overrides[get_audit_sink] = lambda: audit_sink
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def test_create_session_emits_minimized_event(
    client: TestClient,
    service: AsyncMock,
    audit_sink: MemoryAuditSink,
    overrides,
) -> None:
    service.create_session.return_value = snapshot_with_three_turns()

    response = client.post("/v1/sessions")

    assert response.status_code == 201
    event = audit_sink.events[-1]
    assert event.event_type == "session.created"
    assert event.session_id == SESSION_ID
    assert event.outcome == "success"
    assert event.turn_count is None
    assert event.request_id == UUID(response.headers["X-Request-ID"])
    assert event.duration_ms >= 0
    serialized = event.to_json()
    for sentinel in (
        "PERGUNTA_SECRET",
        "RESPOSTA_SECRET",
        "EXCERPT_SECRET",
        "SOURCE_SECRET",
    ):
        assert sentinel not in serialized


def test_read_session_contains_only_turn_count(
    client: TestClient,
    service: AsyncMock,
    audit_sink: MemoryAuditSink,
    overrides,
) -> None:
    service.get_session.return_value = snapshot_with_three_turns()

    response = client.get(f"/v1/sessions/{SESSION_ID}")

    assert response.status_code == 200
    event = audit_sink.events[-1]
    assert event.event_type == "session.read"
    assert event.session_id == SESSION_ID
    assert event.turn_count == 3
    assert event.request_id == UUID(response.headers["X-Request-ID"])
    assert event.duration_ms >= 0
    serialized = event.to_json()
    assert "question" not in serialized
    assert "answer" not in serialized
    assert "sources" not in serialized
    assert "EXCERPT_SECRET" not in serialized


def test_delete_session_emits_only_after_success(
    client: TestClient,
    service: AsyncMock,
    audit_sink: MemoryAuditSink,
    overrides,
) -> None:
    response = client.delete(f"/v1/sessions/{SESSION_ID}")

    assert response.status_code == 204
    event = audit_sink.events[-1]
    assert event.event_type == "session.deleted"
    assert event.session_id == SESSION_ID
    assert event.turn_count is None


@pytest.mark.parametrize(
    ("method", "side_effect"),
    [("get_session", SessionNotFoundError()), ("delete_session", SessionExpiredError())],
)
def test_failed_session_operation_does_not_emit_success_event(
    client: TestClient,
    service: AsyncMock,
    audit_sink: MemoryAuditSink,
    overrides,
    method: str,
    side_effect: Exception,
) -> None:
    getattr(service, method).side_effect = side_effect

    response = getattr(client, "get" if method == "get_session" else "delete")(
        f"/v1/sessions/{SESSION_ID}"
    )

    assert response.status_code in {404, 410}
    assert audit_sink.events == []
    UUID(response.headers["X-Request-ID"])
