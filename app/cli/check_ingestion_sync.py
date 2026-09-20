from langchain_core.documents import Document

from app.rag.sync import build_ingestion_sync_plan, select_missing_chunks
from app.rag.vector_store import IndexedPointRef, deterministic_point_id


def _chunk(source: str, text: str, start_index: int = 0) -> Document:
    return Document(
        page_content=text,
        metadata={
            "source": source,
            "page": 1,
            "start_index": start_index,
        },
    )


def main() -> None:
    old = _chunk("changed.pdf", "old")
    new = _chunk("changed.pdf", "new")
    added = _chunk("added.pdf", "added")
    removed = _chunk("removed.pdf", "removed")

    indexed = [
        IndexedPointRef(
            id=deterministic_point_id(old),
            source="changed.pdf",
        ),
        IndexedPointRef(
            id=deterministic_point_id(removed),
            source="removed.pdf",
        ),
    ]

    plan = build_ingestion_sync_plan(
        [new, added],
        indexed,
        discovered_sources={"changed.pdf", "added.pdf"},
    )
    selected = select_missing_chunks(
        [new, added],
        plan.missing_point_ids,
    )

    checks = [
        ("changed/new chunks are missing", plan.missing_points == 2),
        ("old and removed chunks are stale", plan.stale_points == 2),
        ("removed source is orphan", plan.orphan_sources == ("removed.pdf",)),
        ("missing chunks map back exactly", len(selected) == 2),
        (
            "selected ids equal planned missing ids",
            {deterministic_point_id(chunk) for chunk in selected}
            == set(plan.missing_point_ids),
        ),
    ]

    print("RagTest ingestion sync self-check")
    failed = 0
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        if not passed:
            failed += 1

    if failed:
        raise SystemExit(f"{failed} ingestion sync self-check(s) failed")

    print("All ingestion sync self-checks passed.")


if __name__ == "__main__":
    main()
