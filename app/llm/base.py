from typing import Protocol


class LLMProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str: ...
