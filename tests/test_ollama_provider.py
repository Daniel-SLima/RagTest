from unittest.mock import AsyncMock

import pytest

from app.llm.base import LLMServiceUnavailableError
from app.llm.ollama_provider import OllamaProvider, _OllamaRequestError


def _provider(*, retries: int = 2, think: bool = False) -> OllamaProvider:
    return OllamaProvider(
        base_url="http://host.docker.internal:11434",
        model_name="qwen3:8b",
        context_window=8192,
        think=think,
        service_retry_attempts=retries,
        service_retry_base_delay_seconds=0,
    )


def test_ollama_payload_keeps_system_user_and_runtime_options() -> None:
    provider = _provider()

    payload = provider._payload(
        system_prompt="system",
        user_prompt="user",
    )

    assert payload["model"] == "qwen3:8b"
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"},
    ]
    assert payload["options"]["num_ctx"] == 8192


@pytest.mark.asyncio
async def test_ollama_returns_message_content(monkeypatch) -> None:
    provider = _provider()
    request = AsyncMock(
        return_value={
            "message": {
                "role": "assistant",
                "content": "Resposta local [1].",
            }
        }
    )
    monkeypatch.setattr(provider, "_post_json", request)

    answer = await provider.generate(
        system_prompt="system",
        user_prompt="user",
    )

    assert answer == "Resposta local [1]."
    assert request.await_count == 1


@pytest.mark.asyncio
async def test_ollama_records_generation_metrics(monkeypatch) -> None:
    provider = _provider()
    request = AsyncMock(
        return_value={
            "message": {
                "role": "assistant",
                "content": "Resposta local [1].",
            },
            "done_reason": "stop",
            "total_duration": 2_000_000_000,
            "load_duration": 100_000_000,
            "prompt_eval_count": 120,
            "prompt_eval_duration": 500_000_000,
            "eval_count": 50,
            "eval_duration": 1_250_000_000,
        }
    )
    monkeypatch.setattr(provider, "_post_json", request)

    await provider.generate(
        system_prompt="system",
        user_prompt="user",
    )

    assert len(provider.generation_metrics) == 1
    metrics = provider.generation_metrics[0]
    assert metrics.total_seconds == pytest.approx(2.0)
    assert metrics.load_seconds == pytest.approx(0.1)
    assert metrics.prompt_tokens == 120
    assert metrics.prompt_seconds == pytest.approx(0.5)
    assert metrics.output_tokens == 50
    assert metrics.output_seconds == pytest.approx(1.25)
    assert metrics.output_tokens_per_second == pytest.approx(40.0)
    assert metrics.done_reason == "stop"


@pytest.mark.asyncio
async def test_ollama_retries_transient_failure_and_recovers(monkeypatch) -> None:
    provider = _provider(retries=2)
    request = AsyncMock(
        side_effect=[
            _OllamaRequestError("connection refused"),
            {
                "message": {
                    "role": "assistant",
                    "content": "recuperou",
                }
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
async def test_ollama_raises_domain_error_after_transient_retries(monkeypatch) -> None:
    provider = _provider(retries=1)
    request = AsyncMock(
        side_effect=[
            _OllamaRequestError("connection refused"),
            _OllamaRequestError("connection refused"),
        ]
    )
    monkeypatch.setattr(provider, "_post_json", request)

    with pytest.raises(LLMServiceUnavailableError, match="Ollama permaneceu indisponível"):
        await provider.generate(
            system_prompt="system",
            user_prompt="user",
        )

    assert request.await_count == 2


@pytest.mark.asyncio
async def test_ollama_does_not_retry_non_transient_http_error(monkeypatch) -> None:
    provider = _provider(retries=2)
    request = AsyncMock(side_effect=_OllamaRequestError("model not found", status_code=404))
    monkeypatch.setattr(provider, "_post_json", request)

    with pytest.raises(RuntimeError, match="model not found"):
        await provider.generate(
            system_prompt="system",
            user_prompt="user",
        )

    assert request.await_count == 1


@pytest.mark.asyncio
async def test_ollama_rejects_thinking_leak_when_disabled(monkeypatch) -> None:
    provider = _provider(think=False)
    request = AsyncMock(
        return_value={
            "message": {
                "role": "assistant",
                "content": "raciocínio interno</think>\n\nResposta final.",
            }
        }
    )
    monkeypatch.setattr(provider, "_post_json", request)

    with pytest.raises(RuntimeError, match="reasoning"):
        await provider.generate(
            system_prompt="system",
            user_prompt="user",
        )
