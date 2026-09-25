from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from app.api.dependencies import get_llm_provider
from app.api.routes.chat import chat
from app.conversation.models import (
    SessionBusyError,
    SessionConflictError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.core.config import Settings
from app.llm.base import LLMProviderRequestError, LLMServiceUnavailableError
from app.observability.errors import normalize_exception
from app.schemas.chat import ChatRequest


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
