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
from app.evaluation.scope import suggest_min_score
from app.main import app
from app.rag.chat import ChatResult, answer_with_rag


def test_suggest_min_score_uses_midpoint_when_sets_are_separable() -> None:
    suggestion = suggest_min_score(in_scope=[0.62, 0.55, 0.71], out_of_scope=[0.31, 0.40])

    assert suggestion.separable
    assert suggestion.threshold == pytest.approx(0.475)


def test_suggest_min_score_reports_overlap() -> None:
    suggestion = suggest_min_score(in_scope=[0.50, 0.70], out_of_scope=[0.55, 0.20])

    assert not suggestion.separable
    assert suggestion.threshold is None
    assert suggestion.overlap_in_scope == 1


class EmptyStore:
    async def search(self, *args: object, **kwargs: object) -> list:
        return []


class FakeEmbeddings:
    async def embed_query(self, text: str) -> list[float]:
        return [1.0]


class NoLLM:
    model_name = "fake"

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise AssertionError("LLM must not be called without hits")


@pytest.mark.asyncio
async def test_answer_without_hits_is_flagged_out_of_scope() -> None:
    result = await answer_with_rag(
        "quem ganhou o jogo do bahia ontem?",
        embeddings=FakeEmbeddings(),
        vector_store=EmptyStore(),
        llm=NoLLM(),
        auto_decompose=False,
    )

    assert result.out_of_scope
    assert "UBS" in result.answer


def test_route_applies_configured_min_score_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(_env_file=None, retrieval_auto_decompose=False, retrieval_min_score=0.42)
    answer = AsyncMock(
        return_value=ChatResult(
            answer="x", sources=[], model="fake", grounded=False, citation_ids=[], out_of_scope=True
        )
    )
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
    monkeypatch.setattr("app.api.routes.chat.answer_with_rag", answer)
    try:
        with TestClient(app) as client:
            body = client.post("/v1/chat", json={"message": "qual a previsão do tempo?"}).json()
            client.post("/v1/chat", json={"message": "outra pergunta", "min_score": 0.1})
    finally:
        app.dependency_overrides.clear()

    assert answer.await_args_list[0].kwargs["min_score"] == 0.42
    assert answer.await_args_list[1].kwargs["min_score"] == 0.1
    assert body["safety"]["out_of_scope"] is True
