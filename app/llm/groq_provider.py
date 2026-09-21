import asyncio
import json
import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.llm.base import LLMServiceUnavailableError

logger = logging.getLogger(__name__)

_TRANSIENT_HTTP_STATUS_CODES = {429, 498, 500, 502, 503, 504}
_MAX_RETRY_AFTER_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class GroqRateLimits:
    limit_requests: int | None
    limit_tokens: int | None
    remaining_requests: int | None
    remaining_tokens: int | None
    reset_requests: str | None
    reset_tokens: str | None


@dataclass(frozen=True, slots=True)
class GroqGenerationMetrics:
    total_seconds: float | None
    load_seconds: float | None
    prompt_tokens: int | None
    prompt_seconds: float | None
    output_tokens: int | None
    output_seconds: float | None
    done_reason: str | None

    @property
    def output_tokens_per_second(self) -> float | None:
        if not self.output_tokens or not self.output_seconds or self.output_seconds <= 0:
            return None
        return self.output_tokens / self.output_seconds


@dataclass(frozen=True, slots=True)
class _GroqRequestError(Exception):
    message: str
    status_code: int | None = None
    retry_after_seconds: float | None = None

    def __str__(self) -> str:
        return self.message


class GroqProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        base_url: str = "https://api.groq.com/openai/v1",
        temperature: float = 0.1,
        max_output_tokens: int = 2400,
        reasoning_effort: str = "low",
        request_timeout_seconds: float = 120.0,
        service_retry_attempts: int = 2,
        service_retry_base_delay_seconds: float = 1.0,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._reasoning_effort = reasoning_effort
        self._request_timeout_seconds = request_timeout_seconds
        self._service_retry_attempts = service_retry_attempts
        self._service_retry_base_delay_seconds = service_retry_base_delay_seconds
        self._generation_metrics: list[GroqGenerationMetrics] = []
        self._rate_limits: GroqRateLimits | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def generation_metrics(self) -> tuple[GroqGenerationMetrics, ...]:
        return tuple(self._generation_metrics)

    @property
    def rate_limits(self) -> GroqRateLimits | None:
        return self._rate_limits

    @staticmethod
    def _header_int(headers: Mapping[str, str], name: str) -> int | None:
        value = headers.get(name)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _record_rate_limits(self, headers: Mapping[str, str]) -> None:
        normalized = {key.lower(): value for key, value in headers.items()}
        self._rate_limits = GroqRateLimits(
            limit_requests=self._header_int(normalized, "x-ratelimit-limit-requests"),
            limit_tokens=self._header_int(normalized, "x-ratelimit-limit-tokens"),
            remaining_requests=self._header_int(
                normalized,
                "x-ratelimit-remaining-requests",
            ),
            remaining_tokens=self._header_int(
                normalized,
                "x-ratelimit-remaining-tokens",
            ),
            reset_requests=normalized.get("x-ratelimit-reset-requests"),
            reset_tokens=normalized.get("x-ratelimit-reset-tokens"),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; RagTest/0.5.20)",
        }

    def _payload(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        return {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "temperature": self._temperature,
            "max_completion_tokens": self._max_output_tokens,
            "reasoning_effort": self._reasoning_effort,
            "include_reasoning": False,
            "citation_options": "disabled",
        }

    @staticmethod
    def _retry_after_seconds(exc: HTTPError) -> float | None:
        value = exc.headers.get("Retry-After") if exc.headers is not None else None
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            return None

    def _post_json_sync(self, payload: dict[str, object]) -> dict[str, object]:
        request = Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )

        try:
            with urlopen(request, timeout=self._request_timeout_seconds) as response:
                self._record_rate_limits(response.headers)
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.headers is not None:
                self._record_rate_limits(exc.headers)
            try:
                detail = exc.read().decode("utf-8").strip()
            except Exception:  # noqa: BLE001 - best-effort extraction of provider error body.
                detail = ""
            message = f"Groq HTTP {exc.code}"
            if detail:
                message += f": {detail}"
            raise _GroqRequestError(
                message,
                status_code=exc.code,
                retry_after_seconds=self._retry_after_seconds(exc),
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise _GroqRequestError(f"Não foi possível acessar a Groq: {exc}") from exc

        try:
            body = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Groq retornou JSON inválido.") from exc

        if not isinstance(body, dict):
            raise RuntimeError("Groq retornou uma resposta inesperada.")
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
            except _GroqRequestError as exc:
                is_transient = (
                    exc.status_code is None
                    or exc.status_code in _TRANSIENT_HTTP_STATUS_CODES
                )
                retries_exhausted = retry_index >= self._service_retry_attempts

                if not is_transient:
                    raise RuntimeError(str(exc)) from exc

                if retries_exhausted:
                    raise LLMServiceUnavailableError(
                        "Groq permaneceu indisponível após "
                        f"{self._service_retry_attempts} tentativa(s) adicional(is). "
                        "Verifique os limites da conta e tente novamente mais tarde."
                    ) from exc

                delay = self._service_retry_base_delay_seconds * (2**retry_index)
                if exc.retry_after_seconds is not None:
                    delay = max(
                        delay,
                        min(exc.retry_after_seconds, _MAX_RETRY_AFTER_SECONDS),
                    )
                logger.warning(
                    "Groq transient error; retrying in %.1fs (%s/%s): %s",
                    delay,
                    retry_index + 1,
                    self._service_retry_attempts,
                    exc,
                )
                if delay > 0:
                    await asyncio.sleep(delay)

        raise AssertionError("unreachable Groq retry state")

    @staticmethod
    def _number(body: dict[str, object], key: str) -> float | None:
        value = body.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _record_generation_metrics(
        self,
        *,
        body: dict[str, object],
        elapsed_seconds: float,
        finish_reason: str | None,
    ) -> None:
        usage = body.get("usage")
        usage_dict = usage if isinstance(usage, dict) else {}
        prompt_tokens = usage_dict.get("prompt_tokens")
        output_tokens = usage_dict.get("completion_tokens")

        self._generation_metrics.append(
            GroqGenerationMetrics(
                total_seconds=self._number(usage_dict, "total_time") or elapsed_seconds,
                load_seconds=None,
                prompt_tokens=prompt_tokens if isinstance(prompt_tokens, int) else None,
                prompt_seconds=self._number(usage_dict, "prompt_time"),
                output_tokens=output_tokens if isinstance(output_tokens, int) else None,
                output_seconds=self._number(usage_dict, "completion_time"),
                done_reason=finish_reason,
            )
        )

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        started = time.perf_counter()
        body = await self._generate_with_service_retry(
            self._payload(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        )
        elapsed_seconds = time.perf_counter() - started

        provider_error = body.get("error")
        if provider_error:
            raise RuntimeError(f"Groq retornou erro: {provider_error}")

        choices = body.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise RuntimeError("Groq não retornou choices no formato esperado.")

        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Groq não retornou o campo message esperado.")

        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("Groq não retornou conteúdo textual.")

        finish_reason = choice.get("finish_reason")
        finish_reason_text = finish_reason if isinstance(finish_reason, str) else None
        self._record_generation_metrics(
            body=body,
            elapsed_seconds=elapsed_seconds,
            finish_reason=finish_reason_text,
        )
        return content.strip()
