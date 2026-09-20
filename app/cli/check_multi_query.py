from app.rag.multi_query import reciprocal_rank_fuse_hits, select_fusion_queries
from app.rag.vector_store import SearchHit


def _hit(name: str, page: int, score: float) -> SearchHit:
    return SearchHit(
        id=f"{name}-{page}",
        score=score,
        content=f"Conteúdo {name} página {page}",
        source=f"{name}.pdf",
        category="teste",
        audience=None,
        page=page,
        metadata={},
    )


def main() -> None:
    a = _hit("a", 1, 0.9)
    b = _hit("b", 1, 0.8)
    shared_q1 = _hit("shared", 3, 0.7)
    shared_q2 = _hit("shared", 3, 0.95)
    d = _hit("d", 1, 0.85)

    fused = reciprocal_rank_fuse_hits(
        [
            [a, shared_q1, b],
            [shared_q2, d],
        ],
        limit=4,
    )

    checks = [
        (
            "explicit subqueries exclude original query by default",
            select_fusion_queries(
                "direitos e deveres",
                ["direitos", "deveres"],
            ) == ["direitos", "deveres"],
        ),
        (
            "original query can be included explicitly",
            select_fusion_queries(
                "direitos e deveres",
                ["direitos", "deveres"],
                include_original=True,
            ) == ["direitos e deveres", "direitos", "deveres"],
        ),
        ("shared result promoted across queries", fused[0].hit.source == "shared.pdf"),
        ("shared page deduplicated", sum(x.hit.source == "shared.pdf" for x in fused) == 1),
        ("matched query ids preserved", fused[0].matched_query_indexes == (1, 2)),
        ("best rank preserved", fused[0].best_rank == 1),
        ("limit respected", len(fused) == 4),
    ]

    print("RagTest multi-query self-check")
    failed = 0
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        if not passed:
            failed += 1

    if failed:
        raise SystemExit(f"{failed} multi-query self-check(s) failed")

    print("All multi-query self-checks passed.")


if __name__ == "__main__":
    main()
