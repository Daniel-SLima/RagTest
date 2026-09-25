from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.dependencies import (
    get_audit_sink,
    get_conversation_service,
    get_embedding_provider,
    get_llm_provider,
    get_settings,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.api.routes.chat import chat
from app.conversation.models import (
    ConversationSession,
    SessionBusyError,
    SessionConflictError,
    SessionExpiredError,
    SessionNotFoundError,
    SessionSnapshot,
)
from app.core.config import Settings
from app.llm.base import LLMProviderRequestError, LLMServiceUnavailableError
from app.main import app
from app.observability.errors import normalize_exception
from app.observability.middleware import RequestContextMiddleware
from app.rag.chat import ChatResult
from app.rag.vector_store import SearchHit
from app.schemas.chat import ChatRequest

SESSION_ID = UUID(int=17)


class MemoryAuditSink:
    def __init__(self) -> None:
        self.events = []

    def emit(self, event) -> None:
        self.events.append(event)


class FailingAuditSink:
    def __init__(self) -> None:
        self.attempts = 0

    def emit(self, event) -> None:
        self.attempts += 1
        raise RuntimeError(
            "QUESTION_SECRET ANSWER_SECRET PROMPT_SECRET HISTORY_SECRET "
            "EXCERPT_SECRET SOURCE_SECRET DETAIL_SECRET PROVIDER_BODY_SECRET "
            "Authorization API_KEY_SECRET TRACEBACK_SECRET"
        )


def completed_result(*, retrieval_queries: list[str] | None = None) -> ChatResult:
    return ChatResult(
        answer="ANSWER_SECRET [1].",
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
        retrieval_queries=retrieval_queries,
    )


def empty_snapshot() -> SessionSnapshot:
    now = datetime(2026, 9, 25, tzinfo=UTC)
    return SessionSnapshot(
        ConversationSession(SESSION_ID, now, now, now + timedelta(days=7), 0),
        (),
    )


@pytest.fixture
def chat_failure_context(monkeypatch: pytest.MonkeyPatch):
    service = AsyncMock()
    answer = AsyncMock(return_value=completed_result(retrieval_queries=["query"]))
    monkeypatch.setattr("app.api.routes.chat.answer_with_rag", answer)
    settings = Settings(_env_file=None, llm_provider="groq", retrieval_auto_decompose=False)
    app.dependency_overrides.update(
        {
            get_embedding_provider: lambda: object(),
            get_sparse_embedding_provider: lambda: object(),
            get_vector_store: lambda: object(),
            get_llm_provider: lambda: object(),
            get_settings: lambda: settings,
            get_conversation_service: lambda: service,
        }
    )
    try:
        with TestClient(app) as client:
            yield client, service, answer
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def pre_route_context():
    sink = MemoryAuditSink()
    with TestClient(app) as client:
        previous_sink = app.state.audit_sink
        app.state.audit_sink = sink
        try:
            yield client, sink
        finally:
            app.state.audit_sink = previous_sink


def only_failure_event(sink: MemoryAuditSink):
    events = [event for event in sink.events if event.event_type == "chat.failed"]
    assert len(events) == 1
    return events[0]


def test_provider_error_normalizes_without_raw_detail() -> None:
    normalized = normalize_exception(
        LLMProviderRequestError(
            provider="groq",
            status_code=502,
        )
    )

    assert normalized.status_code == 502
    assert normalized.error_code == "provider_error"
    assert normalized.error_type == "provider"
    assert normalized.public_detail == "LLM provider request failed."
    assert "PROMPT_SECRET" not in normalized.public_detail


def test_unexpected_error_uses_stable_internal_class() -> None:
    normalized = normalize_exception(RuntimeError("ANSWER_SECRET"))

    assert normalized.status_code == 502
    assert normalized.error_code == "internal_error"
    assert normalized.error_type == "unhandled"
    assert "ANSWER_SECRET" not in normalized.public_detail


def test_provider_error_marker_and_internal_runtime_are_distinct() -> None:
    provider_error = normalize_exception(
        LLMProviderRequestError(provider="ollama", status_code=401)
    )
    internal_error = normalize_exception(RuntimeError("INTERNAL_SECRET"))

    assert (provider_error.error_code, provider_error.error_type) == (
        "provider_error",
        "provider",
    )
    assert (internal_error.error_code, internal_error.error_type) == (
        "internal_error",
        "unhandled",
    )
    assert "INTERNAL_SECRET" not in internal_error.public_detail


def test_chat_runtime_error_has_fixed_public_detail(monkeypatch) -> None:
    async def fail_with_internal_error(**kwargs: object) -> None:
        raise RuntimeError("ANSWER_SECRET")

    monkeypatch.setattr("app.api.routes.chat.answer_with_rag", fail_with_internal_error)

    async def invoke() -> None:
        await chat(
            request=ChatRequest(message="PROMPT_SECRET"),
            embeddings=object(),
            sparse_embeddings=object(),
            vector_store=object(),
            llm=object(),
            settings=Settings(_env_file=None, retrieval_auto_decompose=False),
            conversation_service=object(),
        )

    import asyncio

    try:
        asyncio.run(invoke())
    except HTTPException as exc:
        assert exc.status_code == 502
        assert exc.detail == "Internal server error."
        assert "ANSWER_SECRET" not in str(exc.detail)
    else:
        raise AssertionError("chat should have raised HTTPException")


def test_llm_factory_error_has_fixed_dependency_detail(monkeypatch) -> None:
    request = Request(
        {
            "type": "http",
            "app": FastAPI(),
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "client": ("test", 1),
            "server": ("test", 80),
        }
    )

    def fail_factory(settings: Settings) -> object:
        raise RuntimeError("FACTORY_SECRET")

    monkeypatch.setattr("app.api.dependencies.create_llm_provider", fail_factory)

    try:
        get_llm_provider(request, Settings(_env_file=None))
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "LLM provider is temporarily unavailable."
        assert "FACTORY_SECRET" not in str(exc.detail)
    else:
        raise AssertionError("get_llm_provider should have raised HTTPException")


def test_known_session_and_provider_failures_keep_stable_taxonomy() -> None:
    cases = [
        (SessionNotFoundError("DETAIL_SECRET"), 404, "session_not_found", "session"),
        (SessionBusyError("DETAIL_SECRET"), 409, "session_busy", "session"),
        (SessionConflictError("DETAIL_SECRET"), 409, "session_conflict", "session"),
        (SessionExpiredError("DETAIL_SECRET"), 410, "session_expired", "session"),
        (
            LLMServiceUnavailableError("DETAIL_SECRET"),
            503,
            "provider_unavailable",
            "provider",
        ),
    ]

    for exception, status_code, error_code, error_type in cases:
        normalized = normalize_exception(exception)

        assert (normalized.status_code, normalized.error_code, normalized.error_type) == (
            status_code,
            error_code,
            error_type,
        )
        assert "DETAIL_SECRET" not in normalized.public_detail


@pytest.mark.parametrize(
    ("status", "error_code", "error_type"),
    [
        (404, "session_not_found", "session"),
        (409, "session_busy", "session"),
        (410, "session_expired", "session"),
        (503, "provider_unavailable", "provider"),
        (502, "provider_error", "provider"),
    ],
)
def test_chat_failure_emits_stable_classification(
    chat_failure_context,
    status: int,
    error_code: str,
    error_type: str,
) -> None:
    client, service, answer = chat_failure_context
    sink = MemoryAuditSink()
    app.dependency_overrides[get_audit_sink] = lambda: sink

    if status == 404:
        service.run_turn.side_effect = SessionNotFoundError("DETAIL_SECRET")
    elif status == 409:
        service.run_turn.side_effect = SessionBusyError("DETAIL_SECRET")
    elif status == 410:
        service.run_turn.side_effect = SessionExpiredError("DETAIL_SECRET")
    elif status == 503:
        answer.side_effect = LLMServiceUnavailableError("DETAIL_SECRET")
    else:
        answer.side_effect = LLMProviderRequestError(provider="groq", status_code=502)

    payload = {"message": "QUESTION_SECRET"}
    if status in {404, 409, 410}:
        payload["session_id"] = str(SESSION_ID)
    response = client.post("/v1/chat", json=payload)

    assert response.status_code == status
    if status == 409:
        assert response.json() == {"detail": "Session is busy."}
    event = only_failure_event(sink)
    assert event.status_code == status
    assert event.error_code == error_code
    assert event.error_type == error_type
    assert event.request_id == UUID(response.headers["X-Request-ID"])
    assert event.duration_ms >= 0
    serialized = event.to_json()
    for sentinel in (
        "QUESTION_SECRET",
        "ANSWER_SECRET",
        "PROMPT_SECRET",
        "HISTORY_SECRET",
        "EXCERPT_SECRET",
        "SOURCE_SECRET",
        "DETAIL_SECRET",
        "PROVIDER_BODY_SECRET",
        "Authorization",
        "API_KEY_SECRET",
        "TRACEBACK_SECRET",
    ):
        assert sentinel not in serialized


def test_validation_error_is_a_single_pre_route_chat_failed(pre_route_context) -> None:
    client, sink = pre_route_context

    response = client.post("/v1/chat", json={"message": "x"})

    assert response.status_code == 422
    event = only_failure_event(sink)
    assert event.status_code == 422
    assert event.error_code == "validation_error"
    assert event.error_type == "validation"
    assert event.request_id == UUID(response.headers["X-Request-ID"])
    assert event.duration_ms >= 0
    assert "x" not in event.to_json()


def test_http_exception_dependency_is_a_single_pre_route_failure(pre_route_context) -> None:
    client, sink = pre_route_context
    app.dependency_overrides.update(
        {
            get_embedding_provider: lambda: object(),
            get_sparse_embedding_provider: lambda: object(),
            get_vector_store: lambda: object(),
            get_settings: lambda: Settings(_env_file=None),
            get_conversation_service: lambda: object(),
            get_llm_provider: lambda: _raise_http_503(),
        }
    )
    try:
        response = client.post("/v1/chat", json={"message": "QUESTION_SECRET"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "LLM provider is temporarily unavailable."}
    event = only_failure_event(sink)
    assert (event.status_code, event.error_code, event.error_type) == (
        503,
        "provider_unavailable",
        "provider",
    )
    assert "DETAIL_SECRET" not in event.to_json()


def test_unexpected_dependency_error_is_fixed_and_audited(pre_route_context) -> None:
    client, sink = pre_route_context
    app.dependency_overrides.update(
        {
            get_embedding_provider: lambda: object(),
            get_sparse_embedding_provider: lambda: object(),
            get_vector_store: lambda: object(),
            get_settings: lambda: Settings(_env_file=None),
            get_conversation_service: lambda: object(),
            get_llm_provider: lambda: _raise_unexpected_dependency(),
        }
    )
    try:
        response = client.post("/v1/chat", json={"message": "QUESTION_SECRET"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {"detail": "Internal server error."}
    assert "TRACEBACK_SECRET" not in response.text
    event = only_failure_event(sink)
    assert (event.status_code, event.error_code, event.error_type) == (
        502,
        "internal_error",
        "unhandled",
    )
    assert event.request_id == UUID(response.headers["X-Request-ID"])


def _raise_http_503() -> object:
    raise HTTPException(status_code=503, detail="DETAIL_SECRET")


def _raise_unexpected_dependency() -> object:
    raise RuntimeError("TRACEBACK_SECRET")


@pytest.mark.asyncio
async def test_middleware_fixed_response_keeps_request_id_and_does_not_read_body() -> None:
    sink = MemoryAuditSink()
    owner = FastAPI()
    owner.state.audit_sink = sink
    received_body = False
    messages = []

    async def raising_app(scope, receive, send) -> None:
        raise RuntimeError("TRACEBACK_SECRET")

    async def receive():
        nonlocal received_body
        received_body = True
        return {"type": "http.request", "body": b"QUESTION_SECRET", "more_body": False}

    async def send(message) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "app": owner,
        "method": "POST",
        "path": "/v1/chat",
        "raw_path": b"/v1/chat",
        "headers": [],
        "query_string": b"",
        "scheme": "http",
        "client": ("test", 1),
        "server": ("test", 80),
    }

    await RequestContextMiddleware(raising_app)(scope, receive, send)

    response_start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    headers = dict(response_start["headers"])
    assert response_start["status"] == 502
    assert headers[b"x-request-id"]
    assert b"Internal server error." in response_body
    assert b"TRACEBACK_SECRET" not in response_body
    assert received_body is False
    event = only_failure_event(sink)
    assert event.status_code == 502
    assert event.error_code == "internal_error"
    assert event.request_id == UUID(headers[b"x-request-id"].decode())
    assert event.duration_ms >= 0


def test_response_failure_after_completed_does_not_emit_a_second_terminal_event(
    chat_failure_context,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _service, answer = chat_failure_context
    sink = MemoryAuditSink()
    app.dependency_overrides[get_audit_sink] = lambda: sink
    answer.return_value = completed_result(retrieval_queries=["query"])

    def fail_response(**kwargs: object):
        raise RuntimeError("RESPONSE_TRACEBACK_SECRET")

    monkeypatch.setattr("app.api.routes.chat.ChatResponse", fail_response)

    response = client.post("/v1/chat", json={"message": "QUESTION_SECRET"})

    assert response.status_code == 502
    assert [event.event_type for event in sink.events] == ["chat.completed"]


def test_failing_sink_does_not_change_stateless_chat_or_repeat_pipeline(chat_failure_context) -> None:
    client, _service, answer = chat_failure_context
    sink = FailingAuditSink()
    app.dependency_overrides[get_audit_sink] = lambda: sink

    response = client.post("/v1/chat", json={"message": "QUESTION_SECRET"})

    assert response.status_code == 200
    answer.assert_awaited_once()
    assert sink.attempts == 1
