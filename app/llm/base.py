from typing import Protocol


class LLMProviderRequestError(RuntimeError):
    """Safe provider failure with status metadata and no raw provider detail."""

    def __init__(self, *, provider: str, status_code: int | None = None) -> None:
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"{provider} request failed.")


class LLMServiceUnavailableError(Exception):
    """Raised when the configured LLM service remains temporarily unavailable."""


class LLMProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str: ...
