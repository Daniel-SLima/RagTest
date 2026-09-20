from app.rag.prompting import build_context
from app.rag.vector_store import SearchHit


def test_context_does_not_send_retrieval_score_to_llm() -> None:
    hit = SearchHit(
        id="1",
        score=0.9876,
        content="Conteúdo documental.",
        source="fonte.pdf",
        category="teste",
        audience=None,
        page=2,
        metadata={},
    )

    context = build_context([hit])

    assert "0.9876" not in context
    assert "Score de recuperação" not in context
    assert "DADO NÃO CONFIÁVEL" in context
