from unittest.mock import AsyncMock

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
from app.core.config import Settings
from app.main import app
from app.rag.chat import ChatResult
from app.security.auth import RateLimiter, get_rate_limiter, parse_api_keys


class MemorySink:
    def __init__(self) -> None:
        self.events = []

    def emit(self, event) -> None:
        self.events.append(event)


def test_parse_api_keys() -> None:
    assert parse_api_keys(None) == {}
    assert parse_api_keys(" seucuida:abc123 , demo:xyz ") == {"abc123": "seucuida", "xyz": "demo"}
    with pytest.raises(ValueError):
        parse_api_keys("semdoispontos")


def test_rate_limiter_uses_sliding_window() -> None:
    now = [0.0]
    limiter = RateLimiter(clock=lambda: now[0])

    assert limiter.check("a", limit=2).allowed
    assert limiter.check("a", limit=2).allowed
    blocked = limiter.check("a", limit=2)
    assert not blocked.allowed
    assert blocked.retry_after_seconds == 60
    assert limiter.check("b", limit=2).allowed
    now[0] = 60.5
    assert limiter.check("a", limit=2).allowed
    assert limiter.check("a", limit=0).allowed


@pytest.fixture
def make_client(monkeypatch: pytest.MonkeyPatch):
    sink = MemorySink()

    def factory(**settings_overrides):
        settings = Settings(_env_file=None, retrieval_auto_decompose=False, **settings_overrides)
        limiter = RateLimiter(clock=lambda: 0.0)
        app.dependency_overrides.update(
            {
                get_embedding_provider: lambda: object(),
                get_sparse_embedding_provider: lambda: object(),
                get_vector_store: lambda: object(),
                get_llm_provider: lambda: object(),
                get_settings: lambda: settings,
                get_conversation_service: lambda: object(),
                get_audit_sink: lambda: sink,
                get_rate_limiter: lambda: limiter,
            }
        )
        monkeypatch.setattr(
            "app.api.routes.chat.answer_with_rag",
            AsyncMock(
                return_value=ChatResult(
                    answer="ok", sources=[], model="m", grounded=False, citation_ids=[]
                )
            ),
        )
        return TestClient(app)

    yield factory, sink
    app.dependency_overrides.clear()


def test_auth_disabled_without_configured_keys(make_client) -> None:
    factory, _ = make_client
    with factory() as client:
        assert client.get("/v1/services").status_code == 200


def test_auth_enabled_requires_valid_key(make_client) -> None:
    factory, _ = make_client
    with factory(api_keys="seucuida:segredo") as client:
        missing = client.get("/v1/services")
        wrong = client.get("/v1/services", headers={"X-API-Key": "errada"})
        right = client.get("/v1/services", headers={"X-API-Key": "segredo"})
        health = client.get("/health")

    assert missing.status_code == 401
    assert missing.json()["detail"] == "Invalid or missing API key."
    assert missing.headers["www-authenticate"] == "ApiKey"
    assert wrong.status_code == 401
    assert right.status_code == 200
    assert health.status_code == 200


def test_chat_unauthorized_stays_401_and_is_audited(make_client) -> None:
    factory, sink = make_client
    with factory(api_keys="seucuida:segredo") as client:
        app.state.audit_sink = sink
        response = client.post("/v1/chat", json={"message": "pergunta"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "ApiKey"
    failures = [event for event in sink.events if event.event_type == "chat.failed"]
    assert [(event.status_code, event.error_code) for event in failures] == [(401, "unauthorized")]


def test_chat_rate_limit_per_client(make_client) -> None:
    factory, sink = make_client
    with factory(api_keys="seucuida:segredo,demo:outra", rate_limit_per_minute=2) as client:
        app.state.audit_sink = sink
        codes = [
            client.post(
                "/v1/chat", json={"message": "pergunta"}, headers={"X-API-Key": "segredo"}
            ).status_code
            for _ in range(3)
        ]
        other = client.post("/v1/chat", json={"message": "pergunta"}, headers={"X-API-Key": "outra"})
        blocked = client.post(
            "/v1/chat", json={"message": "pergunta"}, headers={"X-API-Key": "segredo"}
        )

    assert codes == [200, 200, 429]
    assert other.status_code == 200
    assert blocked.headers["retry-after"] == "60"
    assert blocked.json()["detail"] == "Too many requests."
    assert any(event.error_code == "rate_limited" for event in sink.events)


def test_production_requires_api_keys() -> None:
    from app.security.auth import ensure_production_security

    with pytest.raises(RuntimeError):
        ensure_production_security(Settings(_env_file=None, environment="production", api_keys=None))
    ensure_production_security(Settings(_env_file=None, environment="production", api_keys="a:b"))
    ensure_production_security(Settings(_env_file=None, environment="development", api_keys=None))
