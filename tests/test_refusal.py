import pytest

from app.rag.chat import answer_with_rag
from app.rag.refusal import NO_CONTEXT_MARKER, is_refusal
from app.rag.vector_store import SearchHit


@pytest.mark.parametrize(
    "answer",
    [
        NO_CONTEXT_MARKER,
        f"{NO_CONTEXT_MARKER}.",
        "Os documentos recuperados não contêm nenhuma informação sobre o resultado de jogos do "
        "Bahia. Portanto, não é possível responder à pergunta com base nas fontes disponíveis[1].",
        "Os documentos recuperados não são suficientes para responder a essa pergunta.",
    ],
)
def test_detects_refusals(answer: str) -> None:
    assert is_refusal(answer)


@pytest.mark.parametrize(
    "answer",
    [
        "O preventivo é indicado dos 25 aos 64 anos [1].",
        "Procure a UBS [1].\n\nOs documentos não detalham o horário de funcionamento [2].\n\n"
        "- Leve o Cartão SUS [1].\n- Leve documento com foto [1].",
    ],
)
def test_keeps_real_answers(answer: str) -> None:
    assert not is_refusal(answer)


class OneHitStore:
    async def search(self, *args: object, **kwargs: object) -> list[SearchHit]:
        return [
            SearchHit(
                id="1", score=0.4, content="Caderneta da gestante", source="gestacao/c.pdf",
                category="gestacao", audience=None, page=21, metadata={},
            )
        ]


class Embeddings:
    async def embed_query(self, text: str) -> list[float]:
        return [1.0]


class RefusingLLM:
    model_name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        return (
            "Os documentos recuperados não contêm nenhuma informação sobre jogos do Bahia. "
            "Portanto, não é possível responder à pergunta com base nas fontes disponíveis[1]."
        )


@pytest.mark.asyncio
async def test_refusal_becomes_out_of_scope_without_fake_citation() -> None:
    llm = RefusingLLM()

    result = await answer_with_rag(
        "quem ganhou o jogo do bahia ontem?",
        embeddings=Embeddings(),
        vector_store=OneHitStore(),
        llm=llm,
        auto_decompose=False,
    )

    assert result.out_of_scope
    assert result.grounded is False
    assert result.citation_ids == []
    assert "UBS" in result.answer
    assert llm.calls == 1


def test_system_prompt_asks_for_marker() -> None:
    from app.rag.prompting import SYSTEM_PROMPT

    assert NO_CONTEXT_MARKER in SYSTEM_PROMPT
