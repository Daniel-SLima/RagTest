from app.rag.prompting import build_citation_repair_prompt, build_context
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


def test_citation_repair_prompt_reuses_previous_answer_and_failure_reason() -> None:
    hit = SearchHit(
        id="1",
        score=0.8,
        content="A pessoa usuária tem direito ao atendimento adequado.",
        source="direitos.pdf",
        category="direitos_saude",
        audience=None,
        page=1,
        metadata={},
    )

    prompt = build_citation_repair_prompt(
        "Quais são os direitos?",
        [hit],
        previous_answer="## Direitos\nAtendimento adequado.",
        validation_reason="one or more informative answer blocks have no valid citation",
    )

    assert "## Direitos\nAtendimento adequado." in prompt
    assert "one or more informative answer blocks have no valid citation" in prompt
    assert "Revise a resposta anterior" in prompt
