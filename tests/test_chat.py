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


class UnicodeCitationFakeLLM:
    model_name = "unicode-citation-fake-llm"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        return "A fonte informa vacinação anual contra influenza【1】."


class RepairingFakeLLM:
    model_name = "repairing-fake-llm"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return "Resposta com citação inexistente [9]."
        assert "VALIDAÇÃO AUTOMÁTICA DE CITAÇÕES" in user_prompt
        assert "Resposta com citação inexistente [9]." in user_prompt
        return "Resposta reparada e verificável [1]."


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
    assert result.grounded is True
    assert result.citation_ids == [1]
    assert result.citation_retry_count == 0
    assert len(result.sources) == 1
    assert result.sources[0].audience == "idoso"


@pytest.mark.asyncio
async def test_answer_with_rag_retries_invalid_citations_once() -> None:
    llm = RepairingFakeLLM()

    result = await answer_with_rag(
        "Quais vacinas?",
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        llm=llm,
        audience="idoso",
    )

    assert llm.calls == 2
    assert result.grounded is True
    assert result.citation_ids == [1]
    assert result.citation_retry_count == 1



class CoverageRepairingFakeLLM:
    model_name = "coverage-repairing-fake-llm"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return (
                "A fonte informa vacinação anual contra influenza [1].\n"
                "Outra afirmação informativa ficou sem referência."
            )
        assert "VALIDAÇÃO AUTOMÁTICA DE CITAÇÕES" in user_prompt
        assert "Outra afirmação informativa ficou sem referência." in user_prompt
        assert "BLOCOS SEM CITAÇÃO VÁLIDA" in user_prompt
        assert "Cada parágrafo ou item informativo" in user_prompt
        return (
            "A fonte informa vacinação anual contra influenza [1].\n"
            "A segunda afirmação também está atribuída à fonte [1]."
        )


class HighCoverageSingleUncitedFakeLLM:
    model_name = "high-coverage-single-uncited-fake-llm"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        return (
            "Item um sustentado pela fonte [1].\n"
            "Item dois sustentado pela fonte [1].\n"
            "Item três sustentado pela fonte [1].\n"
            "Item quatro sustentado pela fonte [1].\n"
            "Item cinco sustentado pela fonte [1].\n"
            "Item seis sustentado pela fonte [1].\n"
            "Item sete sustentado pela fonte [1].\n"
            "Item oito sustentado pela fonte [1].\n"
            "Conclusão adicional sem referência."
        )


class PersistentlyUncitedConclusionFakeLLM:
    model_name = "persistently-uncited-conclusion-fake-llm"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return (
                "Primeira resposta com citação inexistente [9]."
            )
        return (
            "Item um sustentado pela fonte [1].\n"
            "Item dois sustentado pela fonte [1].\n"
            "Item três sustentado pela fonte [1].\n"
            "Item quatro sustentado pela fonte [1].\n"
            "Item cinco sustentado pela fonte [1].\n"
            "Item seis sustentado pela fonte [1].\n"
            "Item sete sustentado pela fonte [1].\n"
            "Item oito sustentado pela fonte [1].\n"
            "Esta conclusão adicional continua sem referência."
        )


class LowCoverageAfterRepairFakeLLM:
    model_name = "low-coverage-after-repair-fake-llm"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return "Resposta inicial com citação inexistente [9]."
        return (
            "Único item sustentado pela fonte [1].\n"
            "Afirmação dois continua sem referência.\n"
            "Afirmação três continua sem referência.\n"
            "Afirmação quatro continua sem referência."
        )


class UnrepairableCoverageFakeLLM:
    model_name = "unrepairable-coverage-fake-llm"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        return "Resposta permanece com citação fora do intervalo [9]."


@pytest.mark.asyncio
async def test_answer_with_rag_retries_incomplete_citation_coverage_once() -> None:
    llm = CoverageRepairingFakeLLM()

    result = await answer_with_rag(
        "Quais vacinas?",
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        llm=llm,
        audience="idoso",
    )

    assert llm.calls == 2
    assert result.grounded is True
    assert result.citation_ids == [1]
    assert result.citation_retry_count == 1
    assert len(result.citation_validation_attempts) == 2
    first_attempt, second_attempt = result.citation_validation_attempts
    assert first_attempt.valid is False
    assert first_attempt.coverage == 0.5
    assert second_attempt.valid is True
    assert second_attempt.coverage == 1.0
    assert "segunda afirmação" in result.answer.lower()


@pytest.mark.asyncio
async def test_answer_with_rag_falls_back_when_coverage_still_fails() -> None:
    llm = UnrepairableCoverageFakeLLM()

    result = await answer_with_rag(
        "Quais vacinas?",
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        llm=llm,
        audience="idoso",
    )

    assert llm.calls == 2
    assert result.grounded is False
    assert result.citation_ids == []
    assert result.citation_retry_count == 1
    assert len(result.citation_validation_attempts) == 2
    for attempt in result.citation_validation_attempts:
        assert attempt.valid is False
        assert attempt.syntax_valid is False
        assert attempt.coverage == 0.0
        assert attempt.reason == "answer contains citation ids outside the available source range"
    assert "Não foi possível gerar uma resposta" in result.answer


@pytest.mark.asyncio
async def test_answer_with_rag_normalizes_unicode_citations_before_validation() -> None:
    llm = UnicodeCitationFakeLLM()

    result = await answer_with_rag(
        "Quais vacinas?",
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        llm=llm,
        audience="idoso",
    )

    assert llm.calls == 1
    assert result.grounded is True
    assert result.citation_ids == [1]
    assert result.citation_retry_count == 0
    assert "【1】" not in result.answer
    assert result.answer.endswith("[1].")


@pytest.mark.asyncio
async def test_answer_with_rag_prunes_uncited_blocks_after_failed_repair() -> None:
    llm = PersistentlyUncitedConclusionFakeLLM()

    result = await answer_with_rag(
        "Quais vacinas?",
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        llm=llm,
        audience="idoso",
    )

    assert llm.calls == 2
    assert result.grounded is True
    assert result.citation_ids == [1]
    assert result.citation_retry_count == 1
    assert "conclusão adicional" not in result.answer
    assert len(result.citation_validation_attempts) == 3
    assert result.citation_validation_attempts[0].stage == "initial"
    assert result.citation_validation_attempts[1].stage == "repair"
    assert result.citation_validation_attempts[2].stage == "postprocess"
    assert result.citation_validation_attempts[2].valid is True
    assert result.citation_validation_attempts[2].coverage == 1.0


@pytest.mark.asyncio
async def test_answer_with_rag_prunes_high_coverage_single_uncited_before_repair() -> None:
    llm = HighCoverageSingleUncitedFakeLLM()

    result = await answer_with_rag(
        "Quais vacinas?",
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        llm=llm,
        audience="idoso",
    )

    assert llm.calls == 1
    assert result.grounded is True
    assert result.citation_ids == [1]
    assert result.citation_retry_count == 0
    assert "Conclusão adicional" not in result.answer
    assert len(result.citation_validation_attempts) == 2
    assert result.citation_validation_attempts[0].stage == "initial"
    assert result.citation_validation_attempts[0].coverage == pytest.approx(8 / 9)
    assert result.citation_validation_attempts[1].stage == "postprocess"
    assert result.citation_validation_attempts[1].valid is True
    assert result.citation_validation_attempts[1].coverage == 1.0


@pytest.mark.asyncio
async def test_answer_with_rag_does_not_prune_low_coverage_after_repair() -> None:
    llm = LowCoverageAfterRepairFakeLLM()

    result = await answer_with_rag(
        "Quais vacinas?",
        embeddings=FakeEmbeddings(),
        vector_store=FakeStore(),
        llm=llm,
        audience="idoso",
    )

    assert llm.calls == 2
    assert result.grounded is False
    assert result.citation_ids == []
    assert result.citation_retry_count == 1
    assert len(result.citation_validation_attempts) == 2
    assert result.citation_validation_attempts[0].stage == "initial"
    assert result.citation_validation_attempts[1].stage == "repair"
    assert result.citation_validation_attempts[1].coverage == pytest.approx(0.25)
    assert "Não foi possível gerar uma resposta" in result.answer
