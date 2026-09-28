from datetime import date
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_conversation_service,
    get_embedding_provider,
    get_llm_provider,
    get_settings,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.core.config import Settings
from app.main import app
from app.presentation import build_display, local_today, source_location_label, source_title
from app.rag.actions import SuggestedAction, present_action
from app.rag.chat import ChatResult
from app.rag.vector_store import SearchHit
from app.safety.triage import triage_message


def _result(**overrides) -> ChatResult:
    base = dict(answer="x", sources=[], model="m", grounded=False, citation_ids=[])
    base.update(overrides)
    return ChatResult(**base)


def _hit() -> SearchHit:
    return SearchHit(
        id="1", score=0.5, content="c", source="chatscm/chatscm.docx",
        category="chatscm", audience=None, page=None, metadata={},
    )


@pytest.mark.parametrize(
    ("result", "status", "tone"),
    [
        (_result(safety=triage_message("estou grávida e sangrando")), "emergency", "danger"),
        (_result(out_of_scope=True), "out_of_scope", "neutral"),
        (_result(grounded=True, citation_ids=[1], sources=[_hit()]), "verified", "success"),
        (_result(sources=[_hit()]), "unverified", "warning"),
        (_result(), "no_sources", "warning"),
    ],
)
def test_build_display_maps_every_state(result: ChatResult, status: str, tone: str) -> None:
    display = build_display(result)

    assert display.status == status
    assert display.tone == tone
    assert display.title
    assert display.message


def test_source_labels() -> None:
    assert source_title("gestacao/caderneta_gestante_8ed_rev.pdf") == "caderneta_gestante_8ed_rev.pdf"
    assert source_title("servicos/catalogo_servicos.json") == "Catálogo de serviços do Se Cuida Mulher"
    assert source_location_label(3) == "Página 3"
    assert source_location_label(None) is None


def test_present_action_computes_due_date_and_host_app_flag() -> None:
    reminder = present_action(
        SuggestedAction(type="schedule_reminder", label="L", service_id="mamografia", suggested_in_days=730),
        today=date(2026, 9, 28),
    )
    link = present_action(
        SuggestedAction(type="open_link", label="Ver", url="seucuida://unidades"),
        today=date(2026, 9, 28),
    )
    call = present_action(
        SuggestedAction(type="call_emergency", label="192", url="tel:192"),
        today=date(2026, 9, 28),
    )

    assert reminder.due_date == date(2028, 9, 27)
    assert reminder.requires_host_app is False
    assert link.requires_host_app is True
    assert link.note
    assert call.requires_host_app is False
    assert call.due_date is None


def test_local_today_uses_configured_timezone() -> None:
    assert isinstance(local_today("America/Sao_Paulo"), date)
    assert isinstance(local_today("Invalid/Zone"), date)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    settings = Settings(_env_file=None, retrieval_auto_decompose=False)
    app.dependency_overrides.update(
        {
            get_embedding_provider: lambda: object(),
            get_sparse_embedding_provider: lambda: object(),
            get_vector_store: lambda: object(),
            get_llm_provider: lambda: object(),
            get_settings: lambda: settings,
            get_conversation_service: lambda: object(),
        }
    )
    try:
        with TestClient(app) as test_client:
            yield test_client, monkeypatch
    finally:
        app.dependency_overrides.clear()


def test_chat_response_carries_display_and_source_labels(client) -> None:
    test_client, monkeypatch = client
    monkeypatch.setattr(
        "app.api.routes.chat.answer_with_rag",
        AsyncMock(return_value=_result(grounded=True, citation_ids=[1], sources=[_hit()])),
    )

    body = test_client.post("/v1/chat", json={"message": "pergunta"}).json()

    assert body["display"]["status"] == "verified"
    assert body["display"]["title"] == "Citações verificadas"
    assert body["sources"][0]["title"] == "chatscm.docx"
    assert body["sources"][0]["location_label"] is None


def test_suggestions_endpoint_returns_catalog_questions(client) -> None:
    test_client, _ = client

    body = test_client.get("/v1/suggestions").json()

    texts = [item["text"] for item in body["suggestions"]]
    assert "Quando devo fazer o preventivo?" in texts
    assert all(item["text"] for item in body["suggestions"])
