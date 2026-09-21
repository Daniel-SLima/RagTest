from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.groq_provider import GroqProvider
from app.llm.ollama_provider import OllamaProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError(
                "Gemini is not configured. Define GEMINI_API_KEY in the local .env file."
            )

        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_output_tokens,
            service_retry_attempts=settings.llm_service_retry_attempts,
            service_retry_base_delay_seconds=settings.llm_service_retry_base_delay_seconds,
        )

    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError(
                "Groq is not configured. Define GROQ_API_KEY in the local .env file."
            )

        return GroqProvider(
            api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            base_url=settings.groq_base_url,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_output_tokens,
            reasoning_effort=settings.groq_reasoning_effort,
            request_timeout_seconds=settings.groq_request_timeout_seconds,
            service_retry_attempts=settings.llm_service_retry_attempts,
            service_retry_base_delay_seconds=settings.llm_service_retry_base_delay_seconds,
        )

    if settings.llm_provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model_name=settings.ollama_model,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_output_tokens,
            context_window=settings.ollama_context_window,
            think=settings.ollama_think,
            request_timeout_seconds=settings.ollama_request_timeout_seconds,
            service_retry_attempts=settings.llm_service_retry_attempts,
            service_retry_base_delay_seconds=settings.llm_service_retry_base_delay_seconds,
        )

    raise RuntimeError(
        f"Unsupported LLM provider: {settings.llm_provider}. "
        "Supported providers: gemini, groq, ollama"
    )
