from pathlib import Path
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
from app.catalog.services import load_service_catalog
from app.core.config import Settings
from app.main import app
from app.rag.actions import build_actions
from app.rag.chat import ChatResult
from app.rag.vector_store import SearchHit
from app.safety.triage import triage_message

CATALOG = load_service_catalog(Path("data/source/servicos/catalogo_servicos.json"))


def _hit(service_id: str | None, source: str = "servicos/catalogo_servicos.json") -> SearchHit:
    metadata = {"service_id": service_id} if service_id else {}
    return SearchHit(
        id=f"p-{service_id}",
        score=0.8,
        content="conteúdo",
        source=source,
        category="servicos",
        audience="mulher",
        page=None,
        metadata=metadata,
    )


def _result(hits: list[SearchHit], citation_ids: list[int], grounded: bool = True) -> ChatResult:
    return ChatResult(
        answer="Resposta [1].",
        sources=hits,
        model="fake",
        grounded=grounded,
        citation_ids=citation_ids,
    )


def test_cited_service_produces_link_and_reminders() -> None:
    result = _result([_hit("preventivo"), _hit(None, "chatscm/chatscm.docx")], [1])

    actions = build_actions(result, CATALOG)

    assert [action.type for action in actions] == [
        "open_link",
        "schedule_reminder",
        "schedule_reminder",
        "schedule_reminder",
    ]
    assert actions[0].url == "seucuida://unidades"
    assert {action.suggested_in_days for action in actions[1:]} == {365, 1095, 1825}
    assert all(action.service_id == "preventivo" for action in actions)


def test_uncited_service_produces_no_actions() -> None:
    result = _result([_hit(None, "chatscm/chatscm.docx"), _hit("mamografia")], [1])

    assert build_actions(result, CATALOG) == []


def test_ungrounded_answer_produces_no_actions() -> None:
    result = _result([_hit("preventivo")], [], grounded=False)

    assert build_actions(result, CATALOG) == []


def test_triaged_result_produces_only_emergency_call() -> None:
    result = ChatResult(
        answer="x",
        sources=[],
        model="triagem-deterministica",
        grounded=False,
        citation_ids=[],
        safety=triage_message("estou grávida e sangrando"),
    )

    actions = build_actions(result, CATALOG)

    assert [(action.type, action.url) for action in actions] == [("call_emergency", "tel:192")]


def test_missing_catalog_still_allows_emergency_but_no_service_actions() -> None:
    result = _result([_hit("preventivo")], [1])

    assert build_actions(result, None) == []


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


def test_chat_endpoint_exposes_actions_and_safety(client) -> None:
    test_client, monkeypatch = client
    monkeypatch.setattr(
        "app.api.routes.chat.answer_with_rag",
        AsyncMock(return_value=_result([_hit("mamografia")], [1])),
    )

    body = test_client.post("/v1/chat", json={"message": "como agendo a mamografia"}).json()

    assert body["safety"] == {"triaged": False, "rule_id": None, "out_of_scope": False}
    assert body["actions"][0] == {
        "type": "open_link",
        "label": "Ver unidades de saúde",
        "url": "seucuida://unidades",
        "service_id": "mamografia",
        "suggested_in_days": None,
        "due_date": None,
        "requires_host_app": True,
        "note": "Este atalho abre a tela correspondente no app Se Cuida Mulher.",
    }
    assert body["actions"][1]["type"] == "schedule_reminder"
    assert body["actions"][1]["suggested_in_days"] == 730
    assert body["actions"][1]["due_date"] is not None


def test_chat_endpoint_marks_triaged_answers(client) -> None:
    test_client, monkeypatch = client
    triage = triage_message("estou grávida e sangrando")
    monkeypatch.setattr(
        "app.api.routes.chat.answer_with_rag",
        AsyncMock(
            return_value=ChatResult(
                answer=triage.answer,
                sources=[],
                model="triagem-deterministica",
                grounded=False,
                citation_ids=[],
                safety=triage,
            )
        ),
    )

    body = test_client.post("/v1/chat", json={"message": "estou grávida e sangrando"}).json()

    assert body["safety"] == {"triaged": True, "rule_id": "sangramento", "out_of_scope": False}
    assert body["actions"] == [
        {
            "type": "call_emergency",
            "label": "Ligar para o SAMU (192)",
            "url": "tel:192",
            "service_id": None,
            "suggested_in_days": None,
            "due_date": None,
            "requires_host_app": False,
            "note": None,
        }
    ]
