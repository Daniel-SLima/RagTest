import logging

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        temperature: float = 0.1,
        max_output_tokens: int = 2400,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    @property
    def model_name(self) -> str:
        return self._model_name

    async def _generate_once(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int,
    ):
        client = genai.Client(api_key=self._api_key)
        async with client.aio as aclient:
            return await aclient.models.generate_content(
                model=self._model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self._temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )

    @staticmethod
    def _finish_reason(response) -> types.FinishReason | None:
        if not response.candidates:
            return None
        return response.candidates[0].finish_reason

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        response = await self._generate_once(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=self._max_output_tokens,
        )

        if self._finish_reason(response) == types.FinishReason.MAX_TOKENS:
            retry_tokens = min(max(self._max_output_tokens * 2, 3200), 4096)
            logger.warning(
                "Gemini response reached max tokens; retrying once with %s tokens.",
                retry_tokens,
            )
            response = await self._generate_once(
                system_prompt=system_prompt,
                user_prompt=(
                    user_prompt
                    + "\n\nImportante: entregue uma resposta completa nesta tentativa, "
                    "sem terminar após uma frase introdutória."
                ),
                max_output_tokens=retry_tokens,
            )

        text = response.text or ""
        return text.strip()
