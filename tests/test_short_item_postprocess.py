import pytest

from app.rag.chat import _can_postprocess_safely, answer_with_rag
from app.rag.citations import normalize_citation_markup
from app.rag.grounding import validate_citation_coverage
from app.rag.vector_store import SearchHit

ANSWER = """Para agendar o preventivo, procure a UBS mais próxima e verifique a data na recepção [1].

Documentos necessários:
- Cartão Nacional de Saúde (Cartão SUS)
- Documento de identificação com foto [1]

O resultado fica pronto entre 20 e 30 dias [3]."""


def test_short_uncited_list_item_with_cited_siblings_can_be_pruned() -> None:
    validation = validate_citation_coverage(ANSWER, 3)

    assert validation.uncited_blocks == ("- Cartão Nacional de Saúde (Cartão SUS)",)
    assert _can_postprocess_safely(validation)


def test_long_uncited_block_still_blocks_postprocess_when_coverage_is_low() -> None:
    answer = (
        "Procure a UBS [1].\n\n"
        "A mamografia deve ser feita todo ano a partir dos trinta anos em qualquer unidade."
    )

    assert not _can_postprocess_safely(validate_citation_coverage(answer, 1))


def test_more_than_two_short_items_are_not_pruned() -> None:
    answer = "Leve:\n- Cartão SUS\n- RG\n- CPF\n- Documento com foto [1]\n\nProcure a UBS [1]."

    assert not _can_postprocess_safely(validate_citation_coverage(answer, 1))


def test_normalizes_any_numbered_lenticular_citation() -> None:
    assert normalize_citation_markup("Texto【1:0†source】 e【2†L3】.") == "Texto[1] e[2]."


class Store:
    async def search(self, *args: object, **kwargs: object) -> list[SearchHit]:
        return [
            SearchHit(
                id=str(i), score=0.5, content="c", source=f"s{i}.pdf", category=None,
                audience=None, page=1, metadata={},
            )
            for i in range(1, 4)
        ]


class Embeddings:
    async def embed_query(self, text: str) -> list[float]:
        return [1.0]


class LLM:
    model_name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        return ANSWER


@pytest.mark.asyncio
async def test_pipeline_prunes_short_item_without_repair_and_keeps_rejected_text() -> None:
    llm = LLM()

    result = await answer_with_rag(
        "onde eu marco o preventivo", embeddings=Embeddings(), vector_store=Store(),
        llm=llm, auto_decompose=False,
    )

    assert result.grounded
    assert llm.calls == 1
    assert "Cartão Nacional de Saúde" not in result.answer
    assert result.citation_validation_attempts[0].answer == ANSWER
