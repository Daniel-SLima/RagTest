from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from google.genai import errors

from app.llm.base import LLMServiceUnavailableError
from app.llm.gemini_provider import GeminiProvider


def _provider(*, retries: int = 2) -> GeminiProvider:
    return GeminiProvider(
        api_key="test-key",
        model_name="test-model",
        service_retry_attempts=retries,
        service_retry_base_delay_seconds=0,
    )


def _response(text: str = "ok"):
    return SimpleNamespace(candidates=[], text=text)


@pytest.mark.asyncio
async def test_gemini_retries_transient_503_and_recovers(monkeypatch) -> None:
    provider = _provider(retries=2)
    request = AsyncMock(
        side_effect=[
            errors.ServerError(
                503,
                {"error": {"message": "high demand"}},
                None,
            ),
            _response("resposta recuperada"),
        ]
    )
    monkeypatch.setattr(provider, "_generate_once", request)

    answer = await provider.generate(
        system_prompt="system",
        user_prompt="user",
    )

    assert answer == "resposta recuperada"
    assert request.await_count == 2


@pytest.mark.asyncio
async def test_gemini_raises_domain_error_after_transient_retries(monkeypatch) -> None:
    provider = _provider(retries=2)
    request = AsyncMock(
        side_effect=[
            errors.ServerError(503, {"error": {"message": "busy 1"}}, None),
            errors.ServerError(503, {"error": {"message": "busy 2"}}, None),
            errors.ServerError(503, {"error": {"message": "busy 3"}}, None),
        ]
    )
    monkeypatch.setattr(provider, "_generate_once", request)

    with pytest.raises(LLMServiceUnavailableError, match="temporariamente indisponível"):
        await provider.generate(
            system_prompt="system",
            user_prompt="user",
        )

    assert request.await_count == 3


@pytest.mark.asyncio
async def test_gemini_does_not_retry_non_transient_client_error(monkeypatch) -> None:
    provider = _provider(retries=2)
    request = AsyncMock(
        side_effect=errors.ClientError(
            400,
            {"error": {"message": "bad request"}},
            None,
        )
    )
    monkeypatch.setattr(provider, "_generate_once", request)

    with pytest.raises(errors.ClientError):
        await provider.generate(
            system_prompt="system",
            user_prompt="user",
        )

    assert request.await_count == 1
