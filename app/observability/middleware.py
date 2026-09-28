"""Request-scoped correlation, timing and safe chat failure fallback."""

import json
from datetime import UTC, datetime
from time import monotonic
from uuid import UUID, uuid4

from fastapi import Request
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.observability.audit import AuditEvent, AuditSink, safe_emit
from app.observability.errors import NormalizedError, normalize_exception, normalize_status


def _elapsed_milliseconds(started_at: float) -> int:
    return max(0, round((monotonic() - started_at) * 1000))


def _is_chat_request(scope: Scope) -> bool:
    return scope.get("method") == "POST" and scope.get("path") == "/v1/chat"


def _audit_sink(request: Request) -> AuditSink | None:
    return getattr(request.app.state, "audit_sink", None)


def _emit_chat_failure(
    request: Request,
    normalized: NormalizedError,
    started_at: float,
) -> None:
    if getattr(request.state, "audit_event_emitted", False):
        return

    request.state.audit_event_emitted = True
    sink = _audit_sink(request)
    if sink is None:
        return

    event = AuditEvent(
        event_id=uuid4(),
        timestamp=datetime.now(UTC),
        request_id=request.state.request_id,
        event_type="chat.failed",
        outcome="failure",
        operation="chat",
        duration_ms=_elapsed_milliseconds(started_at),
        status_code=normalized.status_code,
        error_code=normalized.error_code,
        error_type=normalized.error_type,
    )
    safe_emit(sink, event)


async def _send_safe_error(
    send: Send,
    request_id: UUID,
    status_code: int,
    detail: str,
    original_start: Message | None = None,
) -> None:
    body = json.dumps({"detail": detail}, separators=(",", ":")).encode("utf-8")
    original_headers = (original_start or {}).get("headers", [])
    headers = [
        (name, value)
        for name, value in original_headers
        if name.lower().startswith(b"access-control-")
        or name.lower() in (b"retry-after", b"www-authenticate")
    ]
    headers.extend(
        [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"x-request-id", str(request_id).encode("ascii")),
        ]
    )
    await send({"type": "http.response.start", "status": status_code, "headers": headers})
    await send({"type": "http.response.body", "body": body, "more_body": False})


class RequestContextMiddleware:
    """Install backend-owned request metadata and audit chat failures."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        request_id = uuid4()
        started_at = monotonic()
        request.state.request_id = request_id
        request.state.request_started_at = started_at
        request.state.audit_event_emitted = False
        response_status_code: int | None = None
        response_started = False
        deferred_response_start: Message | None = None

        async def send_with_context(message: Message) -> None:
            nonlocal deferred_response_start, response_started, response_status_code
            if message["type"] == "http.response.start":
                response_status_code = message["status"]
                if (
                    _is_chat_request(scope)
                    and response_status_code >= 400
                    and not request.state.audit_event_emitted
                ):
                    deferred_response_start = message
                    return
                response_started = True
                MutableHeaders(scope=message)["X-Request-ID"] = str(request_id)
            elif message["type"] == "http.response.body":
                if not message.get("more_body", False):
                    request.state.request_duration_ms = _elapsed_milliseconds(started_at)
                if deferred_response_start is not None:
                    return
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        except Exception as exc:  # noqa: BLE001 - chat errors receive a safe fallback
            if response_started:
                raise
            if not _is_chat_request(scope):
                request.state.request_duration_ms = _elapsed_milliseconds(started_at)
                await _send_safe_error(
                    send,
                    request_id,
                    500,
                    "Internal server error.",
                )
                return
            normalized = normalize_exception(exc)
            request.state.request_duration_ms = _elapsed_milliseconds(started_at)
            _emit_chat_failure(request, normalized, started_at)
            await _send_safe_error(
                send,
                request_id,
                normalized.status_code,
                normalized.public_detail,
                deferred_response_start,
            )
            return

        if (
            _is_chat_request(scope)
            and response_status_code is not None
            and response_status_code >= 400
            and not request.state.audit_event_emitted
        ):
            normalized = normalize_status(response_status_code)
            request.state.request_duration_ms = _elapsed_milliseconds(started_at)
            _emit_chat_failure(request, normalized, started_at)
            await _send_safe_error(
                send,
                request_id,
                normalized.status_code,
                normalized.public_detail,
                deferred_response_start,
            )
