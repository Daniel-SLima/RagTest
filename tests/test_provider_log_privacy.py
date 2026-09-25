import logging
from io import BytesIO
from unittest.mock import AsyncMock
from urllib.error import HTTPError, URLError

import pytest

from app.llm.base import LLMServiceUnavailableError
from app.llm.groq_provider import GroqProvider, _GroqRequestError
from app.llm.ollama_provider import OllamaProvider, _OllamaRequestError
from app.rag.decomposition import decompose_question


def _groq_provider(*, retries: int = 0) -> GroqProvider:
    return GroqProvider(
        api_key="test-key",
        model_name="openai/gpt-oss-120b",
        service_retry_attempts=retries,
        service_retry_base_delay_seconds=0,
    )


def _ollama_provider(*, retries: int = 0) -> OllamaProvider:
    return OllamaProvider(
        base_url="http://host.docker.internal:11434",
        model_name="qwen3:8b",
        service_retry_attempts=retries,
        service_retry_base_delay_seconds=0,
    )


@pytest.mark.asyncio
async def test_groq_http_body_is_not_logged(caplog, monkeypatch) -> None:
    error = HTTPError(
        url="https://provider.invalid/chat",
        code=503,
        msg="Service unavailable",
        hdrs={},
        fp=BytesIO(b"PROMPT_SECRET EXCERPT_SECRET ANSWER_SECRET"),
    )
    monkeypatch.setattr("app.llm.groq_provider.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(error))

    with caplog.at_level(logging.WARNING):
        with pytest.raises(LLMServiceUnavailableError):
            await _groq_provider().generate(system_prompt="p", user_prompt="q")

    assert "PROMPT_SECRET" not in caplog.text
    assert "EXCERPT_SECRET" not in caplog.text
    assert "ANSWER_SECRET" not in caplog.text


@pytest.mark.asyncio
async def test_ollama_http_body_is_not_logged(caplog, monkeypatch) -> None:
    error = HTTPError(
        url="http://provider.invalid/api/chat",
        code=503,
        msg="Service unavailable",
        hdrs={},
        fp=BytesIO(b"PROMPT_SECRET EXCERPT_SECRET ANSWER_SECRET"),
    )
    monkeypatch.setattr("app.llm.ollama_provider.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(error))

    with caplog.at_level(logging.WARNING):
        with pytest.raises(LLMServiceUnavailableError):
            await _ollama_provider().generate(system_prompt="p", user_prompt="q")

    assert "PROMPT_SECRET" not in caplog.text
    assert "EXCERPT_SECRET" not in caplog.text
    assert "ANSWER_SECRET" not in caplog.text


@pytest.mark.asyncio
async def test_provider_url_error_does_not_expose_sensitive_url() -> None:
    groq_error = URLError("https://PROMPT_SECRET:ANSWER_SECRET@private.invalid")
    ollama_error = URLError("http://private.invalid/EXCERPT_SECRET")

    for module_name, error, provider in (
        ("app.llm.groq_provider", groq_error, _groq_provider()),
        ("app.llm.ollama_provider", ollama_error, _ollama_provider()),
    ):
        target = f"{module_name}.urlopen"
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(target, lambda *args, _error=error, **kwargs: (_ for _ in ()).throw(_error))
            with pytest.raises((LLMServiceUnavailableError, _GroqRequestError, _OllamaRequestError)) as raised:
                await provider.generate(system_prompt="p", user_prompt="q")

        assert "PROMPT_SECRET" not in str(raised.value)
        assert "EXCERPT_SECRET" not in str(raised.value)
        assert "ANSWER_SECRET" not in str(raised.value)


@pytest.mark.asyncio
async def test_http_200_error_field_does_not_expose_provider_body() -> None:
    groq = _groq_provider()
    ollama = _ollama_provider()
    groq_request = AsyncMock(return_value={"error": {"message": "PROMPT_SECRET"}})
    ollama_request = AsyncMock(return_value={"error": "EXCERPT_SECRET"})

    groq._post_json = groq_request
    ollama._post_json = ollama_request

    with pytest.raises(RuntimeError) as groq_raised:
        await groq.generate(system_prompt="p", user_prompt="q")
    with pytest.raises(RuntimeError) as ollama_raised:
        await ollama.generate(system_prompt="p", user_prompt="q")

    assert "PROMPT_SECRET" not in str(groq_raised.value)
    assert "EXCERPT_SECRET" not in str(ollama_raised.value)


@pytest.mark.asyncio
async def test_retry_log_uses_status_metadata_without_exception_text(caplog, monkeypatch) -> None:
    provider = _groq_provider(retries=1)
    request = AsyncMock(
        side_effect=[
            _GroqRequestError("PROMPT_SECRET", status_code=503),
            _GroqRequestError("EXCERPT_SECRET", status_code=503),
        ]
    )
    monkeypatch.setattr(provider, "_post_json", request)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(LLMServiceUnavailableError):
            await provider.generate(system_prompt="p", user_prompt="q")

    assert "PROMPT_SECRET" not in caplog.text
    assert "EXCERPT_SECRET" not in caplog.text
    assert "Groq" in caplog.text
    assert "openai/gpt-oss-120b" in caplog.text
    assert "503" in caplog.text
    assert "1/1" in caplog.text


@pytest.mark.asyncio
async def test_ollama_retry_log_uses_status_metadata_without_exception_text(caplog, monkeypatch) -> None:
    provider = _ollama_provider(retries=1)
    request = AsyncMock(
        side_effect=[
            _OllamaRequestError("PROMPT_SECRET", status_code=503),
            _OllamaRequestError("EXCERPT_SECRET", status_code=503),
        ]
    )
    monkeypatch.setattr(provider, "_post_json", request)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(LLMServiceUnavailableError):
            await provider.generate(system_prompt="p", user_prompt="q")

    assert "PROMPT_SECRET" not in caplog.text
    assert "EXCERPT_SECRET" not in caplog.text
    assert "Ollama" in caplog.text
    assert "qwen3:8b" in caplog.text
    assert "503" in caplog.text
    assert "1/1" in caplog.text


@pytest.mark.asyncio
async def test_decomposition_fallback_omits_traceback_and_exception_text(caplog) -> None:
    class FailingPlanner:
        model_name = "fake"

        async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
            raise RuntimeError("PROMPT_SECRET EXCERPT_SECRET")

    with caplog.at_level(logging.WARNING):
        result = await decompose_question(
            "Quais são os direitos e deveres?",
            llm=FailingPlanner(),
        )

    assert result.status == "fallback-error"
    records = [record for record in caplog.records if record.name == "app.rag.decomposition"]
    assert records
    assert all(record.exc_info is None for record in records)
    assert "PROMPT_SECRET" not in caplog.text
    assert "EXCERPT_SECRET" not in caplog.text
