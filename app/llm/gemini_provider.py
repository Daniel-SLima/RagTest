import asyncio
import logging

from google import genai
from google.genai import errors, types

from app.llm.base import LLMServiceUnavailableError

logger = logging.getLogger(__name__)

_TRANSIENT_API_STATUS_CODES = {429, 500, 502, 503, 504}


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        temperature: float = 0.1,
        max_output_tokens: int = 2400,
        service_retry_attempts: int = 2,
        service_retry_base_delay_seconds: float = 1.0,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._service_retry_attempts = service_retry_attempts
        self._service_retry_base_delay_seconds = service_retry_base_delay_seconds

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

    async def _generate_with_service_retry(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int,
    ):
        for retry_index in range(self._service_retry_attempts + 1):
            try:
                return await self._generate_once(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_output_tokens=max_output_tokens,
                )
            except errors.APIError as exc:
                is_transient = exc.code in _TRANSIENT_API_STATUS_CODES
                retries_exhausted = retry_index >= self._service_retry_attempts

                if not is_transient:
                    raise

                if retries_exhausted:
                    raise LLMServiceUnavailableError(
                        "Gemini permaneceu temporariamente indisponível após "
                        f"{self._service_retry_attempts} tentativa(s) adicional(is). "
                        "Tente novamente mais tarde."
                    ) from exc

                delay = self._service_retry_base_delay_seconds * (2**retry_index)
                logger.warning(
                    "Gemini transient API error %s; retrying in %.1fs (%s/%s).",
                    exc.code,
                    delay,
                    retry_index + 1,
                    self._service_retry_attempts,
                )
                if delay > 0:
                    await asyncio.sleep(delay)

        raise AssertionError("unreachable service retry state")

    @staticmethod
    def _finish_reason(response) -> types.FinishReason | None:
        if not response.candidates:
            return None
        return response.candidates[0].finish_reason

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        response = await self._generate_with_service_retry(
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
            response = await self._generate_with_service_retry(
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
