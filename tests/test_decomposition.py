import pytest

from app.rag.decomposition import (
    decompose_question,
    parse_subqueries,
    should_attempt_decomposition,
)


class FakePlanner:
    model_name = "fake"

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        return self.response


def test_parse_subqueries_deduplicates_and_removes_original() -> None:
    original = "Quais são os direitos e deveres?"
    raw = (
        '{"subqueries":["Quais são os direitos?",'
        '"Quais são os deveres?",'
        '"Quais são os direitos?",'
        '"Quais são os direitos e deveres?"]}'
    )

    assert parse_subqueries(raw, original) == (
        "Quais são os direitos?",
        "Quais são os deveres?",
    )


def test_simple_question_does_not_trigger_heuristic() -> None:
    assert not should_attempt_decomposition(
        "Quais vacinas são recomendadas para idosos?"
    )


@pytest.mark.asyncio
async def test_compound_question_uses_two_subqueries() -> None:
    planner = FakePlanner(
        '{"subqueries":["Quais são os direitos da pessoa usuária?",'
        '"Quais são os deveres da pessoa usuária?"]}'
    )

    result = await decompose_question(
        "Quais são os direitos e deveres da pessoa usuária?",
        llm=planner,
    )

    assert result.used is True
    assert len(result.subqueries) == 2
    assert planner.calls == 1


@pytest.mark.asyncio
async def test_malformed_output_falls_back() -> None:
    planner = FakePlanner("texto inválido")

    result = await decompose_question(
        "Quais são os direitos e deveres da pessoa usuária?",
        llm=planner,
    )

    assert result.used is False
    assert result.status == "single-query"
