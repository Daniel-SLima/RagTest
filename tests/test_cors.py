from fastapi.testclient import TestClient

from app.main import app


def test_cors_allows_expo_web_localhost() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/v1/chat",
            headers={
                "Origin": "http://localhost:8081",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_cors_does_not_allow_unknown_origin() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/v1/chat",
            headers={
                "Origin": "https://example.invalid",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_delete_for_sessions() -> None:
    from uuid import uuid4

    with TestClient(app) as client:
        response = client.options(
            f"/v1/sessions/{uuid4()}",
            headers={
                "Origin": "http://localhost:8081",
                "Access-Control-Request-Method": "DELETE",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"
    assert "DELETE" in response.headers["access-control-allow-methods"]
