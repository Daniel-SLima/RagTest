from app.rag.grounding import prune_uncited_claim_blocks, validate_citation_coverage


def test_citation_coverage_accepts_every_informative_block_cited() -> None:
    result = validate_citation_coverage(
        "Vacinação anual contra influenza [1].\n"
        "A recomendação deve considerar a fonte recuperada [2].",
        2,
    )

    assert result.valid is True
    assert result.syntax_valid is True
    assert result.total_claim_blocks == 2
    assert result.cited_claim_blocks == 2
    assert result.uncited_claim_blocks == 0
    assert result.coverage == 1.0


def test_citation_coverage_detects_uncited_informative_block() -> None:
    result = validate_citation_coverage(
        "Vacinação anual contra influenza [1].\n"
        "Outra afirmação informativa sem referência.",
        1,
    )

    assert result.valid is False
    assert result.syntax_valid is True
    assert result.total_claim_blocks == 2
    assert result.cited_claim_blocks == 1
    assert result.uncited_claim_blocks == 1
    assert result.uncited_blocks == ("Outra afirmação informativa sem referência.",)
    assert result.coverage == 0.5


def test_citation_coverage_ignores_short_heading_blocks() -> None:
    result = validate_citation_coverage(
        "Vacinas recomendadas:\n"
        "- Influenza anual conforme o documento [1].",
        1,
    )

    assert result.valid is True
    assert result.total_claim_blocks == 1
    assert result.cited_claim_blocks == 1


def test_citation_coverage_ignores_long_list_intro_ending_with_colon() -> None:
    result = validate_citation_coverage(
        "Alguns dos direitos da pessoa usuária da saúde, conforme os trechos recuperados, são:\n"
        "1. Direito ao acolhimento imediato conforme a fonte [1].\n"
        "2. Direito a acompanhante conforme a fonte [2].",
        2,
    )

    assert result.valid is True
    assert result.total_claim_blocks == 2
    assert result.cited_claim_blocks == 2


def test_citation_coverage_ignores_markdown_heading_without_colon() -> None:
    result = validate_citation_coverage(
        "## Direitos da pessoa usuária\n"
        "- O direito descrito está sustentado pela fonte [1].",
        1,
    )

    assert result.valid is True
    assert result.total_claim_blocks == 1
    assert result.cited_claim_blocks == 1


def test_citation_coverage_rejects_out_of_range_citation() -> None:
    result = validate_citation_coverage(
        "Informação sustentada por uma fonte inexistente [2].",
        1,
    )

    assert result.valid is False
    assert result.syntax_valid is False
    assert result.coverage == 0.0


def test_citation_coverage_rejects_answer_without_claim_blocks() -> None:
    result = validate_citation_coverage("Resumo:", 1)

    assert result.valid is False
    assert result.total_claim_blocks == 0
    assert result.coverage == 0.0


def test_prune_uncited_claim_blocks_removes_only_unsupported_claims() -> None:
    answer = (
        "Alguns direitos são:\n\n"
        "1. Direito ao acolhimento [1].\n\n"
        "2. Direito a acompanhante [2].\n\n"
        "Esses direitos refletem garantias previstas para as pessoas usuárias."
    )

    pruned = prune_uncited_claim_blocks(answer, 2)

    assert "Alguns direitos são:" in pruned
    assert "1. Direito ao acolhimento [1]." in pruned
    assert "2. Direito a acompanhante [2]." in pruned
    assert "Esses direitos refletem" not in pruned

    validation = validate_citation_coverage(pruned, 2)
    assert validation.valid is True
    assert validation.coverage == 1.0
