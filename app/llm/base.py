from typing import Protocol


class LLMServiceUnavailableError(Exception):
    """Raised when the configured LLM service remains temporarily unavailable."""


class LLMProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str: ...
