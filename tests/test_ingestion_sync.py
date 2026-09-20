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


def test_sync_plan_reports_clean_collection() -> None:
    a = _chunk("a.pdf", "alpha")
    b = _chunk("b.pdf", "beta")

    plan = build_ingestion_sync_plan(
        [a, b],
        [
            IndexedPointRef(id=deterministic_point_id(a), source="a.pdf"),
            IndexedPointRef(id=deterministic_point_id(b), source="b.pdf"),
        ],
        discovered_sources={"a.pdf", "b.pdf"},
    )

    assert plan.in_sync is True
    assert plan.missing_points == 0
    assert plan.stale_points == 0
    assert plan.orphan_sources == ()


def test_sync_plan_detects_changed_chunk() -> None:
    current = _chunk("a.pdf", "new text")
    old = _chunk("a.pdf", "old text")

    plan = build_ingestion_sync_plan(
        [current],
        [IndexedPointRef(id=deterministic_point_id(old), source="a.pdf")],
        discovered_sources={"a.pdf"},
    )

    assert plan.in_sync is False
    assert plan.missing_points == 1
    assert plan.stale_points == 1
    assert plan.source_deltas[0].source == "a.pdf"


def test_sync_plan_detects_removed_source() -> None:
    old = _chunk("removed.pdf", "old")

    plan = build_ingestion_sync_plan(
        [],
        [IndexedPointRef(id=deterministic_point_id(old), source="removed.pdf")],
        discovered_sources=set(),
    )

    assert plan.missing_points == 0
    assert plan.stale_points == 1
    assert plan.orphan_sources == ("removed.pdf",)



def test_select_missing_chunks_maps_ids_back_to_current_documents() -> None:
    a = _chunk("a.pdf", "alpha")
    b = _chunk("b.pdf", "beta")

    selected = select_missing_chunks(
        [a, b],
        (deterministic_point_id(b),),
    )

    assert selected == [b]


def test_select_missing_chunks_rejects_unknown_ids() -> None:
    a = _chunk("a.pdf", "alpha")

    try:
        select_missing_chunks([a], ("unknown-id",))
    except RuntimeError as exc:
        assert "could not be mapped" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for unresolved point id")
