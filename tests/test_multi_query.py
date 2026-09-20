from app.rag.multi_query import reciprocal_rank_fuse_hits, select_fusion_queries
from app.rag.vector_store import SearchHit


def _hit(source: str, page: int, score: float = 0.5) -> SearchHit:
    return SearchHit(
        id=f"{source}-{page}",
        score=score,
        content="texto",
        source=source,
        category=None,
        audience=None,
        page=page,
        metadata={},
    )


def test_rrf_promotes_result_seen_in_multiple_queries() -> None:
    shared_a = _hit("shared.pdf", 3, 0.6)
    shared_b = _hit("shared.pdf", 3, 0.9)

    fused = reciprocal_rank_fuse_hits(
        [
            [_hit("a.pdf", 1), shared_a],
            [shared_b, _hit("b.pdf", 1)],
        ],
        limit=4,
    )

    assert fused[0].hit.source == "shared.pdf"
    assert fused[0].matched_query_indexes == (1, 2)
    assert fused[0].best_rank == 1


def test_rrf_deduplicates_same_source_and_page() -> None:
    fused = reciprocal_rank_fuse_hits(
        [
            [_hit("same.pdf", 5)],
            [_hit("same.pdf", 5)],
        ],
        limit=5,
    )

    assert len(fused) == 1


def test_rrf_respects_limit() -> None:
    fused = reciprocal_rank_fuse_hits(
        [
            [_hit("a.pdf", 1), _hit("b.pdf", 1)],
            [_hit("c.pdf", 1), _hit("d.pdf", 1)],
        ],
        limit=2,
    )

    assert len(fused) == 2



def test_explicit_subqueries_are_fused_without_original_by_default() -> None:
    assert select_fusion_queries(
        "direitos e deveres",
        ["direitos", "deveres"],
    ) == ["direitos", "deveres"]


def test_original_can_be_included_for_diagnostics() -> None:
    assert select_fusion_queries(
        "direitos e deveres",
        ["direitos", "deveres"],
        include_original=True,
    ) == ["direitos e deveres", "direitos", "deveres"]
