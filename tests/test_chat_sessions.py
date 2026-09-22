from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_conversation_service,
    get_embedding_provider,
    get_llm_provider,
    get_settings,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.conversation.models import ConversationSession, SessionSnapshot
from app.conversation.service import CompletedConversationTurn
from app.main import app
from app.rag.chat import ChatResult
from app.rag.vector_store import SearchHit

SESSION_ID = UUID(int=8)


def sample_result() -> ChatResult:
    return ChatResult(
        answer="Resposta atual [1].",
        sources=[SearchHit("1", 0.9, "Trecho", "guia.pdf", None, None, 1, {})],
        model="fake-model",
        grounded=True,
        citation_ids=[1],
        retrieval_queries=["Pergunta"],
    )


def empty_snapshot() -> SessionSnapshot:
    now = datetime(2026, 9, 22, tzinfo=UTC)
    return SessionSnapshot(
        ConversationSession(SESSION_ID, now, now, now + timedelta(days=7), 0), (),
    )


@pytest.fixture
def overrides(monkeypatch: pytest.MonkeyPatch):
    service = AsyncMock()
    answer = AsyncMock(return_value=sample_result())
    monkeypatch.setattr("app.api.routes.chat.answer_with_rag", answer)
    app.dependency_overrides.update(
        {
            get_embedding_provider: lambda: object(),
            get_sparse_embedding_provider: lambda: object(),
            get_vector_store: lambda: object(),
            get_llm_provider: lambda: object(),
            get_settings: lambda: __import__("app.core.config", fromlist=["Settings"]).Settings(
                _env_file=None, retrieval_auto_decompose=False
            ),
            get_conversation_service: lambda: service,
        }
    )
    with TestClient(app) as client:
        yield client, service, answer
    app.dependency_overrides.clear()


def test_chat_without_session_keeps_stateless_path(overrides) -> None:
    client, service, answer = overrides
    response = client.post("/v1/chat", json={"message": "Quais vacinas?"})

    assert response.status_code == 200
    assert response.json()["session_id"] is None
    service.run_turn.assert_not_awaited()
    answer.assert_awaited_once()


def test_chat_with_session_uses_service_and_returns_same_id(overrides) -> None:
    client, service, answer = overrides

    async def execute(_session_id, question, answerer):
        result = await answerer("consulta contextual", "histórico sanitizado")
        return CompletedConversationTurn(result, empty_snapshot())

    service.run_turn.side_effect = execute
    response = client.post(
        "/v1/chat",
        json={"message": "E com que frequência?", "session_id": str(SESSION_ID)},
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == str(SESSION_ID)
    service.run_turn.assert_awaited_once()
    answer.assert_awaited_once()
    assert answer.await_args.args == ("E com que frequência?",)
    assert answer.await_args.kwargs["retrieval_question"] == "consulta contextual"
    assert answer.await_args.kwargs["conversation_context"] == "histórico sanitizado"
