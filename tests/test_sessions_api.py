from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.conversation.models import (
    ConversationSession,
    SessionExpiredError,
    SessionNotFoundError,
    SessionSnapshot,
)
from app.main import app

SESSION_ID = UUID(int=7)
NOW = datetime(2026, 9, 22, tzinfo=UTC)


def empty_snapshot() -> SessionSnapshot:
    return SessionSnapshot(
        ConversationSession(SESSION_ID, NOW, NOW, NOW + timedelta(days=7), 0),
        (),
    )


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as value:
        yield value


@pytest.fixture
def service():
    return AsyncMock()


def test_create_session_returns_201(client: TestClient, service: AsyncMock) -> None:
    from app.api.dependencies import get_conversation_service

    service.create_session.return_value = empty_snapshot()
    app.dependency_overrides[get_conversation_service] = lambda: service
    try:
        response = client.post("/v1/sessions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["session_id"] == str(SESSION_ID)
    assert response.json()["turns"] == []


def test_get_expired_session_returns_410(client: TestClient, service: AsyncMock) -> None:
    from app.api.dependencies import get_conversation_service

    service.get_session.side_effect = SessionExpiredError()
    app.dependency_overrides[get_conversation_service] = lambda: service
    try:
        response = client.get(f"/v1/sessions/{SESSION_ID}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 410
    assert response.json()["detail"] == "Session expired."


def test_get_missing_session_returns_404(client: TestClient, service: AsyncMock) -> None:
    from app.api.dependencies import get_conversation_service

    service.get_session.side_effect = SessionNotFoundError()
    app.dependency_overrides[get_conversation_service] = lambda: service
    try:
        response = client.get(f"/v1/sessions/{SESSION_ID}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found."


def test_delete_session_returns_204(client: TestClient, service: AsyncMock) -> None:
    from app.api.dependencies import get_conversation_service

    app.dependency_overrides[get_conversation_service] = lambda: service
    try:
        response = client.delete(f"/v1/sessions/{SESSION_ID}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""


def test_invalid_session_uuid_returns_422(client: TestClient) -> None:
    response = client.get("/v1/sessions/not-a-uuid")
    assert response.status_code == 422
