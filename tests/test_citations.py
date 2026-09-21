from app.rag.citations import (
    extract_citation_ids,
    normalize_citation_markup,
    validate_citations,
)


def test_extract_citation_ids_deduplicates_and_sorts() -> None:
    assert extract_citation_ids("Texto [2] e [1], novamente [2].") == (1, 2)


def test_validate_citations_accepts_available_sources() -> None:
    result = validate_citations("Texto [1] e [2].", 2)

    assert result.valid is True
    assert result.citation_ids == (1, 2)
    assert result.invalid_ids == ()


def test_validate_citations_rejects_missing_citation() -> None:
    result = validate_citations("Texto sem fonte.", 2)

    assert result.valid is False
    assert result.reason == "answer does not contain a verifiable source citation"


def test_validate_citations_rejects_out_of_range_id() -> None:
    result = validate_citations("Texto [3].", 2)

    assert result.valid is False
    assert result.invalid_ids == (3,)


def test_normalize_citation_markup_converts_unicode_brackets() -> None:
    assert normalize_citation_markup("Direito A【1】 e Direito B【2】.") == (
        "Direito A[1] e Direito B[2]."
    )


def test_validate_citations_accepts_unicode_bracket_variant() -> None:
    result = validate_citations("Direito sustentado pela fonte【1】.", 1)

    assert result.valid is True
    assert result.citation_ids == (1,)
