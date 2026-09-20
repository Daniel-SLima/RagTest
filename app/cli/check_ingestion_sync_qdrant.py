import asyncio

from langchain_core.documents import Document

from app.core.config import get_settings
from app.rag.embeddings.base import SparseVectorData
from app.rag.sync import build_ingestion_sync_plan, select_missing_chunks
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService

_TEMP_COLLECTION = "ragtest_ingestion_sync_selfcheck"


def _chunk(source: str, text: str) -> Document:
    return Document(
        page_content=text,
        metadata={
            "source": source,
            "filename": source,
            "category": "selfcheck",
            "file_type": "txt",
            "page": 1,
            "start_index": 0,
        },
    )


def _dense(index: int) -> list[float]:
    vector = [0.0, 0.0, 0.0, 0.0]
    vector[index] = 1.0
    return vector


def _sparse(index: int) -> SparseVectorData:
    return SparseVectorData(indices=[index], values=[1.0])


async def run() -> None:
    settings = get_settings()
    if settings.qdrant_collection == _TEMP_COLLECTION:
        raise RuntimeError("Self-check collection must differ from the application collection.")

    qdrant = QdrantService(settings)
    try:
        if not await qdrant.is_ready():
            raise RuntimeError("Qdrant is unavailable.")

        store = QdrantVectorStore(qdrant.client, _TEMP_COLLECTION)
        await store.ensure_collection(4, recreate=True)

        old_changed = _chunk("changed.pdf", "old text")
        removed = _chunk("removed.pdf", "removed text")
        await store.upsert(
            [old_changed, removed],
            [_dense(0), _dense(1)],
            [_sparse(0), _sparse(1)],
        )

        current_changed = _chunk("changed.pdf", "new text")
        added = _chunk("added.pdf", "added text")
        current_chunks = [current_changed, added]
        discovered_sources = {"changed.pdf", "added.pdf"}

        before = build_ingestion_sync_plan(
            current_chunks,
            await store.list_indexed_points(),
            discovered_sources=discovered_sources,
        )
        missing_chunks = select_missing_chunks(
            current_chunks,
            before.missing_point_ids,
        )

        await store.upsert(
            missing_chunks,
            [_dense(2), _dense(3)],
            [_sparse(2), _sparse(3)],
        )
        await store.delete_points(list(before.stale_point_ids))

        after_points = await store.list_indexed_points()
        after = build_ingestion_sync_plan(
            current_chunks,
            after_points,
            discovered_sources=discovered_sources,
        )

        checks = [
            ("initial plan detects 2 missing", before.missing_points == 2),
            ("initial plan detects 2 stale", before.stale_points == 2),
            ("removed source is orphan", before.orphan_sources == ("removed.pdf",)),
            ("final collection has 2 points", len(after_points) == 2),
            ("final plan has no missing points", after.missing_points == 0),
            ("final plan has no stale points", after.stale_points == 0),
            ("final plan has no orphan sources", after.orphan_sources == ()),
            ("final plan is in sync", after.in_sync),
        ]

        print("RagTest Qdrant ingestion sync integration self-check")
        failed = 0
        for name, passed in checks:
            print(f"[{'PASS' if passed else 'FAIL'}] {name}")
            if not passed:
                failed += 1

        if failed:
            raise SystemExit(f"{failed} Qdrant ingestion sync self-check(s) failed")

        print("All Qdrant ingestion sync integration self-checks passed.")
        print("Main application collection was not touched.")
    finally:
        try:
            if await qdrant.client.collection_exists(_TEMP_COLLECTION):
                await qdrant.client.delete_collection(_TEMP_COLLECTION)
        finally:
            await qdrant.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
