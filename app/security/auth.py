import hmac
import math
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
WINDOW_SECONDS = 60.0
UNAUTHORIZED_DETAIL = "Invalid or missing API key."
RATE_LIMITED_DETAIL = "Too many requests."


def parse_api_keys(raw: str | None) -> dict[str, str]:
    keys: dict[str, str] = {}
    if not raw:
        return keys
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        client, separator, key = item.partition(":")
        if not separator or not client.strip() or not key.strip():
            raise ValueError("API_KEYS deve seguir o formato cliente:chave,cliente2:chave2")
        keys[key.strip()] = client.strip()
    return keys


@dataclass(frozen=True, slots=True)
class RateDecision:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, client_id: str, *, limit: int) -> RateDecision:
        if limit <= 0:
            return RateDecision(True)
        now = self._clock()
        with self._lock:
            hits = self._hits[client_id]
            while hits and now - hits[0] >= WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= limit:
                retry = max(1, math.ceil(hits[0] + WINDOW_SECONDS - now))
                return RateDecision(False, retry)
            hits.append(now)
            return RateDecision(True)


_DEFAULT_LIMITER = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _DEFAULT_LIMITER


def _client_host(request: Request) -> str:
    return f"ip:{request.client.host}" if request.client else "ip:unknown"


async def require_api_client(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    api_key: Annotated[str | None, Depends(API_KEY_HEADER)] = None,
) -> str:
    keys = parse_api_keys(settings.api_keys)
    if not keys:
        client_id = _client_host(request)
    else:
        client_id = next(
            (
                client
                for key, client in keys.items()
                if api_key is not None and hmac.compare_digest(key, api_key)
            ),
            None,
        )
        if client_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=UNAUTHORIZED_DETAIL,
                headers={"WWW-Authenticate": "ApiKey"},
            )
    request.state.client_id = client_id
    return client_id


async def enforce_chat_rate_limit(
    client_id: Annotated[str, Depends(require_api_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    decision = limiter.check(client_id, limit=settings.rate_limit_per_minute)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=RATE_LIMITED_DETAIL,
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


def ensure_production_security(settings: Settings) -> None:
    if settings.environment == "production" and not parse_api_keys(settings.api_keys):
        raise RuntimeError("API_KEYS é obrigatório quando ENVIRONMENT=production.")
