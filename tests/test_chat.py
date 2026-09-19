import pytest

from app.rag.chat import answer_with_rag
from app.rag.vector_store import SearchHit


class FakeEmbeddings:
    model_name = "fake-embeddings"

    async def dimension(self) -> int:
        return 3

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


class FakeStore:
    async def search(self, query_vector: list[float], **kwargs: object) -> list[SearchHit]:
        return [
            SearchHit(
                id="1",
                score=0.8,
                content="Vacinação anual contra influenza.",
                source="vacinacao/idoso.pdf",
                category="vacinacao",
                audience="idoso",
                page=1,
                metadata={},
            )
        ]


class FakeLLM:
    model_name = "fake-llm"

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        assert "[1]" in user_prompt
        return "A fonte informa vacinação anual contra influenza [1]."


@pytest.mark.asyncio
async def test_answer_with_rag_returns_grounded_answer_and_sources() -> None:
    result = await answer_with_rag(
        "Quais vacinas?",
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        llm=FakeLLM(),
        audience="idoso",
    )

    assert result.model == "fake-llm"
    assert result.answer.endswith("[1].")
    assert len(result.sources) == 1
    assert result.sources[0].audience == "idoso"
