import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_settings
from app.core.config import Settings
from app.main import app


@pytest.fixture
def client():
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_list_services_returns_catalog_summary(client: TestClient) -> None:
    body = client.get("/v1/services").json()

    assert body["catalog_version"]
    ids = [service["id"] for service in body["services"]]
    assert {"preventivo", "mamografia", "prenatal", "urgencia_obstetrica"} <= set(ids)
    preventivo = next(service for service in body["services"] if service["id"] == "preventivo")
    assert preventivo["name"].startswith("Exame preventivo")
    assert preventivo["link"] == {"label": "Ver unidades de saúde", "url": "seucuida://unidades"}


def test_get_service_returns_details(client: TestClient) -> None:
    body = client.get("/v1/services/mamografia").json()

    assert body["id"] == "mamografia"
    assert body["how_to_schedule"]
    assert body["reminders"][0]["days"] == 730
    assert body["sources"][0]["title"]


def test_get_unknown_service_returns_404(client: TestClient) -> None:
    response = client.get("/v1/services/nao-existe")

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found."
