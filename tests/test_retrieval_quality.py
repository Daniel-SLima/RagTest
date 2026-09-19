from app.rag.retrieval_quality import (
    apply_relative_score_floor,
    group_hits_by_page,
)
from app.rag.vector_store import SearchHit


def _hit(
    *,
    id: str,
    score: float,
    source: str,
    page: int | None,
    text: str,
    start_index: int = 0,
) -> SearchHit:
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
    first = _hit(
        id="a",
        score=0.80,
        source="idoso.pdf",
        page=1,
        text="inicio" + overlap,
        start_index=0,
    )
    second = _hit(
        id="b",
        score=0.75,
        source="idoso.pdf",
        page=1,
        text=overlap + "fim",
        start_index=10,
    )

    grouped = group_hits_by_page([first, second])

    assert len(grouped) == 1
    assert grouped[0].chunk_count == 2
    assert grouped[0].score == 0.80
    assert grouped[0].content.count(overlap.strip()) == 1
    assert grouped[0].metadata["grouped_chunks"] == 2


def test_chunks_without_page_are_not_grouped_by_source() -> None:
    first = _hit(id="a", score=0.8, source="arquivo.docx", page=None, text="um")
    second = _hit(id="b", score=0.7, source="arquivo.docx", page=None, text="dois")

    grouped = group_hits_by_page([first, second])

    assert len(grouped) == 2


def test_relative_score_floor_removes_distant_candidates() -> None:
    hits = [
        _hit(id="a", score=0.75, source="a.pdf", page=1, text="a"),
        _hit(id="b", score=0.60, source="b.pdf", page=1, text="b"),
        _hit(id="c", score=0.50, source="c.pdf", page=1, text="c"),
    ]

    filtered = apply_relative_score_floor(hits, score_margin=0.22)

    assert [hit.id for hit in filtered] == ["a", "b"]
