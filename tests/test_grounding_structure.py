from app.rag.grounding import prune_uncited_claim_blocks, validate_citation_coverage

REAL_ANSWER = """**Como agendar a mamografia**

1. **Procure a Unidade Básica de Saúde (UBS) ou a Unidade de Saúde da Família (USF) mais próxima da sua residência**.
   - Verifique na recepção se há vaga para mamografia [1].
   - A UBS não realiza o exame, mas consulta no sistema a vaga e a unidade [1][3].
2. **Leve os documentos necessários** [3]:
   - Cartão Nacional de Saúde (Cartão SUS);
   - Documento de identificação com foto;
3. A mamografia de rastreamento é recomendada a cada 2 anos dos 50 aos 74 anos [4]."""


def test_structured_answer_from_real_failure_is_fully_grounded() -> None:
    coverage = validate_citation_coverage(REAL_ANSWER, 5)

    assert coverage.valid, coverage.uncited_blocks
    assert coverage.total_claim_blocks == 3


def test_bold_only_line_is_a_heading() -> None:
    coverage = validate_citation_coverage("**Documentos necessários**\n\nLeve o Cartão SUS [1].", 1)

    assert coverage.valid


def test_parent_step_is_not_exempt_when_children_are_uncited() -> None:
    answer = (
        "1. Procure a unidade básica de saúde mais próxima de casa.\n"
        "   - Verifique na recepção se existe vaga disponível hoje.\n"
        "2. A mamografia é feita em serviço de imagem de referência [1]."
    )

    coverage = validate_citation_coverage(answer, 1)

    assert not coverage.valid
    assert coverage.uncited_claim_blocks == 2


def test_long_items_do_not_inherit_the_intro_citation() -> None:
    answer = (
        "Leve os documentos abaixo [1]:\n"
        "- Cartão SUS;\n"
        "- A mamografia deve ser repetida a cada dois anos entre os cinquenta e setenta e quatro anos."
    )

    coverage = validate_citation_coverage(answer, 1)

    assert not coverage.valid
    assert coverage.uncited_blocks == (
        "- A mamografia deve ser repetida a cada dois anos entre os cinquenta e setenta e quatro anos.",
    )


def test_uncited_intro_does_not_grant_inheritance() -> None:
    answer = "Leve os documentos abaixo:\n- Cartão Nacional de Saúde (Cartão SUS);\n- Documento com foto;"

    coverage = validate_citation_coverage(answer, 1)

    assert not coverage.valid


def test_prune_keeps_structural_lines() -> None:
    pruned = prune_uncited_claim_blocks(REAL_ANSWER, 5)

    assert "Cartão Nacional de Saúde" in pruned
    assert "**Como agendar a mamografia**" in pruned
