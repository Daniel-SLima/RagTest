from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider != "gemini":
        raise RuntimeError(
            f"Unsupported LLM provider: {settings.llm_provider}. "
            "Supported providers: gemini"
        )

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
