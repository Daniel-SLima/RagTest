"""Request-scoped correlation and timing context for the HTTP application."""

from time import monotonic
from uuid import uuid4

from fastapi import Request
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def _elapsed_milliseconds(started_at: float) -> int:
    return max(0, round((monotonic() - started_at) * 1000))


class RequestContextMiddleware:
    """Install backend-owned request metadata without reading the request body."""

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

        async def send_with_context(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["X-Request-ID"] = str(request_id)
            elif message["type"] == "http.response.body" and not message.get("more_body", False):
                request.state.request_duration_ms = _elapsed_milliseconds(started_at)
            await send(message)

        await self.app(scope, receive, send_with_context)
