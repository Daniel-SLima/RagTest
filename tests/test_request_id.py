from time import monotonic
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.main import app
from app.observability.middleware import RequestContextMiddleware


def test_backend_generates_request_id_on_success() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    UUID(response.headers["X-Request-ID"])


def test_backend_generates_request_id_and_ignores_client_header() -> None:
    client_request_id = "00000000-0000-0000-0000-000000000099"

    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"X-Request-ID": client_request_id},
        )

    request_id = UUID(response.headers["X-Request-ID"])
    assert request_id != UUID(client_request_id)


def test_request_id_exists_on_validation_error() -> None:
    with TestClient(app) as client:
        response = client.post("/v1/chat", json={"message": "x"})

    UUID(response.headers["X-Request-ID"])
    assert response.status_code == 422


def test_request_context_keeps_id_and_monotonic_start_time_in_state() -> None:
    context_app = FastAPI()
    context_app.add_middleware(RequestContextMiddleware)

    @context_app.get("/context")
    async def context(request: Request) -> dict[str, str | bool]:
        request_id = request.state.request_id
        started_at = request.state.request_started_at
        return {
            "request_id_is_uuid": isinstance(request_id, UUID),
            "started_at_is_monotonic_float": isinstance(started_at, float)
            and started_at <= monotonic(),
        }

    with TestClient(context_app) as client:
        response = client.get("/context")

    assert response.json() == {
        "request_id_is_uuid": True,
        "started_at_is_monotonic_float": True,
    }
