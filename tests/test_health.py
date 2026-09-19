from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_api_status() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "RagTest API"
    assert body["version"] == "0.1.0"


def test_ready_returns_200_when_qdrant_is_available() -> None:
    with TestClient(app) as client:
        app.state.qdrant.is_ready = AsyncMock(return_value=True)
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {"qdrant": "ok"},
    }


def test_ready_returns_503_when_qdrant_is_unavailable() -> None:
    with TestClient(app) as client:
        app.state.qdrant.is_ready = AsyncMock(return_value=False)
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Qdrant is unavailable"}
