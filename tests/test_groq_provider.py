from unittest.mock import AsyncMock

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
