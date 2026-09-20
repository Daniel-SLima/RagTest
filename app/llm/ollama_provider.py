import asyncio
import json
import logging
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.llm.base import LLMServiceUnavailableError

logger = logging.getLogger(__name__)

_TRANSIENT_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True, slots=True)
class _OllamaRequestError(Exception):
    message: str
    status_code: int | None = None

    def __str__(self) -> str:
        return self.message


class OllamaProvider:
    def __init__(
        self,
        *,
        base_url: str,
        model_name: str,
        temperature: float = 0.1,
        max_output_tokens: int = 2400,
        context_window: int = 8192,
        think: bool = False,
        request_timeout_seconds: float = 180.0,
        service_retry_attempts: int = 2,
        service_retry_base_delay_seconds: float = 1.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._context_window = context_window
        self._think = think
        self._request_timeout_seconds = request_timeout_seconds
        self._service_retry_attempts = service_retry_attempts
        self._service_retry_base_delay_seconds = service_retry_base_delay_seconds

    @property
    def model_name(self) -> str:
        return self._model_name

    def _payload(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        return {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "think": self._think,
            "options": {
                "temperature": self._temperature,
                "num_ctx": self._context_window,
                "num_predict": self._max_output_tokens,
            },
        }

    def _post_json_sync(self, payload: dict[str, object]) -> dict[str, object]:
        request = Request(
            f"{self._base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self._request_timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8").strip()
            except Exception:  # noqa: BLE001 - best-effort extraction of provider error body.
                detail = ""
            message = f"Ollama HTTP {exc.code}"
            if detail:
                message += f": {detail}"
            raise _OllamaRequestError(message, status_code=exc.code) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise _OllamaRequestError(f"Não foi possível acessar o Ollama: {exc}") from exc

        try:
            body = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama retornou JSON inválido.") from exc

        if not isinstance(body, dict):
            raise RuntimeError("Ollama retornou uma resposta inesperada.")
        return body

    async def _post_json(self, payload: dict[str, object]) -> dict[str, object]:
        return await asyncio.to_thread(self._post_json_sync, payload)

    async def _generate_with_service_retry(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        for retry_index in range(self._service_retry_attempts + 1):
            try:
                return await self._post_json(payload)
            except _OllamaRequestError as exc:
                is_transient = (
                    exc.status_code is None
                    or exc.status_code in _TRANSIENT_HTTP_STATUS_CODES
                )
                retries_exhausted = retry_index >= self._service_retry_attempts

                if not is_transient:
                    raise RuntimeError(str(exc)) from exc

                if retries_exhausted:
                    raise LLMServiceUnavailableError(
                        "Ollama permaneceu indisponível após "
                        f"{self._service_retry_attempts} tentativa(s) adicional(is). "
                        "Confirme se o Ollama está em execução e tente novamente."
                    ) from exc

                delay = self._service_retry_base_delay_seconds * (2**retry_index)
                logger.warning(
                    "Ollama transient error; retrying in %.1fs (%s/%s): %s",
                    delay,
                    retry_index + 1,
                    self._service_retry_attempts,
                    exc,
                )
                if delay > 0:
                    await asyncio.sleep(delay)

        raise AssertionError("unreachable Ollama retry state")

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        body = await self._generate_with_service_retry(
            self._payload(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        )

        provider_error = body.get("error")
        if provider_error:
            raise RuntimeError(f"Ollama retornou erro: {provider_error}")

        message = body.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Ollama não retornou o campo message esperado.")

        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("Ollama não retornou conteúdo textual.")

        text = content.strip()
        if not self._think and "</think>" in text.lower():
            raise RuntimeError(
                "Ollama retornou conteúdo de reasoning apesar de think=false. "
                "Use um modelo que respeite a desativação de thinking."
            )
        return text
