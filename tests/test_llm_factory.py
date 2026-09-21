import pytest
from app.llm.groq_provider import GroqProvider

from app.core.config import Settings
from app.llm.factory import create_llm_provider
from app.llm.gemini_provider import GeminiProvider
from app.llm.ollama_provider import OllamaProvider


def test_factory_creates_ollama_without_gemini_key() -> None:
    settings = Settings(
        llm_provider="ollama",
        gemini_api_key=None,
        ollama_model="qwen3:8b",
        ollama_context_window=8192,
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, OllamaProvider)
    assert provider.model_name == "qwen3:8b"


def test_factory_keeps_gemini_provider() -> None:
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="test-key",
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, GeminiProvider)


def test_factory_creates_groq_provider() -> None:
    settings = Settings(
        llm_provider="groq",
        gemini_api_key=None,
        groq_api_key="test-groq-key",
        groq_model="openai/gpt-oss-120b",
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, GroqProvider)
    assert provider.model_name == "openai/gpt-oss-120b"


def test_factory_rejects_groq_without_key() -> None:
    settings = Settings(
        llm_provider="groq",
        groq_api_key=None,
    )

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        create_llm_provider(settings)


def test_factory_rejects_unknown_provider() -> None:
    settings = Settings(
        llm_provider="unknown",
        gemini_api_key="test-key",
    )

    with pytest.raises(RuntimeError, match="Supported providers: gemini, groq, ollama"):
        create_llm_provider(settings)
