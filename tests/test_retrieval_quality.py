from app.rag.retrieval_quality import apply_relative_score_floor, group_hits_by_page, metadata_aware_rerank
from app.rag.vector_store import SearchHit


def _hit(*, id: str, score: float, source: str, page: int | None, text: str, start_index: int = 0) -> SearchHit:
    return SearchHit(
        id=id,
        score=score,
        content=text,
        source=source,
        category="vacinacao",
        audience="idoso",
        page=page,
        metadata={"start_index": start_index},
    )


def test_group_hits_by_page_merges_overlapping_chunks() -> None:
    overlap = " trecho compartilhado entre os chunks "
    first = _hit(id="a", score=0.80, source="idoso.pdf", page=1, text="inicio" + overlap)
    second = _hit(id="b", score=0.75, source="idoso.pdf", page=1, text=overlap + "fim", start_index=10)

    grouped = group_hits_by_page([first, second])

    assert len(grouped) == 1
    assert grouped[0].chunk_count == 2
    assert grouped[0].score == 0.80


def test_metadata_rerank_can_promote_exact_subject_in_filename() -> None:
    generic = _hit(
        id="generic",
        score=0.62,
        source="medicamentos/relacao_nacional_medicamentos.pdf",
        page=1,
        text="Informações gerais sobre assistência à saúde.",
    )
    expected = _hit(
        id="expected",
        score=0.50,
        source="direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf",
        page=1,
        text="Carta de direitos e deveres da pessoa usuária da saúde.",
    )

    reranked = metadata_aware_rerank(
        "Quais são os direitos e deveres da pessoa usuária da saúde?",
        [generic, expected],
        source_weight=0.25,
        content_weight=0.05,
    )

    assert reranked[0].id == "expected"
    assert reranked[0].rank_score is not None


def test_relative_score_floor_uses_rank_score_when_available() -> None:
    first = _hit(id="a", score=0.55, source="a.pdf", page=1, text="a")
    second = _hit(id="b", score=0.60, source="b.pdf", page=1, text="b")
    third = _hit(id="c", score=0.50, source="c.pdf", page=1, text="c")
    first.rank_score = 0.80
    second.rank_score = 0.63
    third.rank_score = 0.52

    filtered = apply_relative_score_floor([first, second, third], score_margin=0.22)

    assert [hit.id for hit in filtered] == ["a", "b"]
