from io import BytesIO
from unittest.mock import AsyncMock
from urllib.error import HTTPError

import pytest

from app.llm.base import LLMServiceUnavailableError
from app.llm.groq_provider import GroqProvider, _GroqRequestError


def _provider(*, retries: int = 2) -> GroqProvider:
    return GroqProvider(
        api_key="test-key",
        model_name="openai/gpt-oss-120b",
        base_url="https://api.groq.com/openai/v1",
        reasoning_effort="low",
        request_timeout_seconds=60,
        service_retry_attempts=retries,
        service_retry_base_delay_seconds=0,
    )


def test_groq_headers_use_explicit_user_agent() -> None:
    provider = _provider()

    headers = provider._headers()

    assert headers["Authorization"] == "Bearer test-key"
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"
    assert headers["User-Agent"].startswith("Mozilla/5.0")
    assert "RagTest/0.5.23" in headers["User-Agent"]


def test_groq_payload_keeps_rag_messages_and_hides_reasoning() -> None:
    provider = _provider()

    payload = provider._payload(
        system_prompt="system",
        user_prompt="user",
    )

    assert payload["model"] == "openai/gpt-oss-120b"
    assert payload["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"},
    ]
    assert payload["stream"] is False
    assert payload["include_reasoning"] is False
    assert payload["reasoning_effort"] == "low"
    assert payload["citation_options"] == "disabled"


@pytest.mark.asyncio
async def test_groq_returns_message_content_and_records_usage(monkeypatch) -> None:
    provider = _provider()
    request = AsyncMock(
        return_value={
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "Resposta Groq [1].",
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 900,
                "completion_tokens": 100,
            },
        }
    )
    monkeypatch.setattr(provider, "_post_json", request)

    answer = await provider.generate(
        system_prompt="system",
        user_prompt="user",
    )

    assert answer == "Resposta Groq [1]."
    assert len(provider.generation_metrics) == 1
    metrics = provider.generation_metrics[0]
    assert metrics.prompt_tokens == 900
    assert metrics.output_tokens == 100
    assert metrics.done_reason == "stop"
    assert metrics.total_seconds is not None


@pytest.mark.asyncio
async def test_groq_retries_transient_429_and_recovers(monkeypatch) -> None:
    provider = _provider(retries=2)
    request = AsyncMock(
        side_effect=[
            _GroqRequestError("rate limited", status_code=429, retry_after_seconds=0),
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": "recuperou"},
                    }
                ],
                "usage": {},
            },
        ]
    )
    monkeypatch.setattr(provider, "_post_json", request)

    answer = await provider.generate(
        system_prompt="system",
        user_prompt="user",
    )

    assert answer == "recuperou"
    assert request.await_count == 2


@pytest.mark.asyncio
async def test_groq_raises_domain_error_after_transient_retries(monkeypatch) -> None:
    provider = _provider(retries=1)
    request = AsyncMock(
        side_effect=[
            _GroqRequestError("busy", status_code=503),
            _GroqRequestError("busy", status_code=503),
        ]
    )
    monkeypatch.setattr(provider, "_post_json", request)

    with pytest.raises(LLMServiceUnavailableError, match="Groq permaneceu indisponível"):
        await provider.generate(
            system_prompt="system",
            user_prompt="user",
        )

    assert request.await_count == 2


@pytest.mark.asyncio
async def test_groq_does_not_retry_invalid_api_key(monkeypatch) -> None:
    provider = _provider(retries=2)
    request = AsyncMock(
        side_effect=_GroqRequestError("unauthorized", status_code=401)
    )
    monkeypatch.setattr(provider, "_post_json", request)

    with pytest.raises(RuntimeError, match="unauthorized"):
        await provider.generate(
            system_prompt="system",
            user_prompt="user",
        )

    assert request.await_count == 1


def test_groq_records_rate_limit_headers_from_successful_response(monkeypatch) -> None:
    provider = _provider()

    class FakeResponse:
        headers = {
            "x-ratelimit-limit-requests": "1000",
            "x-ratelimit-limit-tokens": "8000",
            "x-ratelimit-remaining-requests": "987",
            "x-ratelimit-remaining-tokens": "6543",
            "x-ratelimit-reset-requests": "23h59m",
            "x-ratelimit-reset-tokens": "7.66s",
        }

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self) -> bytes:
            return b'{"choices": []}'

    monkeypatch.setattr(
        "app.llm.groq_provider.urlopen",
        lambda request, timeout: FakeResponse(),
    )

    provider._post_json_sync({"model": "openai/gpt-oss-120b"})

    rate_limits = provider.rate_limits
    assert rate_limits is not None
    assert rate_limits.limit_requests == 1000
    assert rate_limits.limit_tokens == 8000
    assert rate_limits.remaining_requests == 987
    assert rate_limits.remaining_tokens == 6543
    assert rate_limits.reset_requests == "23h59m"
    assert rate_limits.reset_tokens == "7.66s"


def test_groq_records_rate_limit_headers_from_429_response(monkeypatch) -> None:
    provider = _provider(retries=0)
    error = HTTPError(
        url="https://api.groq.com/openai/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs={
            "Retry-After": "2",
            "x-ratelimit-limit-requests": "1000",
            "x-ratelimit-limit-tokens": "8000",
            "x-ratelimit-remaining-requests": "0",
            "x-ratelimit-remaining-tokens": "120",
            "x-ratelimit-reset-requests": "12h",
            "x-ratelimit-reset-tokens": "3.2s",
        },
        fp=BytesIO(b'{"error":{"message":"rate limited"}}'),
    )

    def raise_rate_limit(request, timeout):
        raise error

    monkeypatch.setattr("app.llm.groq_provider.urlopen", raise_rate_limit)

    with pytest.raises(_GroqRequestError):
        provider._post_json_sync({"model": "openai/gpt-oss-120b"})

    rate_limits = provider.rate_limits
    assert rate_limits is not None
    assert rate_limits.remaining_requests == 0
    assert rate_limits.remaining_tokens == 120
    assert rate_limits.reset_requests == "12h"
    assert rate_limits.reset_tokens == "3.2s"
