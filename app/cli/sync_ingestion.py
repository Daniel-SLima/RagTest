import argparse
import asyncio

from app.core.config import get_settings
from app.rag.chunking import split_documents
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.ingestion import ingest_chunks
from app.rag.loaders import discover_source_files, load_source_documents
from app.rag.sync import build_ingestion_sync_plan, select_missing_chunks
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize the current RagTest corpus with the existing Qdrant collection."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply missing upserts and stale deletions. Without this flag, no writes occur.",
    )
    return parser.parse_args()


async def run(*, apply: bool) -> None:
    settings = get_settings()
    source_dir = settings.source_dir.resolve()

    source_files = discover_source_files(source_dir)
    if not source_files:
        raise RuntimeError(
            "No source files were discovered. Refusing to synchronize an empty corpus."
        )

    discovered_sources = {
        path.relative_to(source_dir).as_posix()
        for path in source_files
    }

    report = load_source_documents(
        source_dir,
        pdf_ocr_enabled=settings.pdf_ocr_enabled,
        pdf_ocr_language=settings.pdf_ocr_language,
        pdf_ocr_dpi=settings.pdf_ocr_dpi,
        pdf_ocr_timeout_seconds=settings.pdf_ocr_timeout_seconds,
    )
    chunks = split_documents(
        report.documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    if report.errors and apply:
        details = "; ".join(
            f"{error.source}: {error.message}"
            for error in report.errors
        )
        raise RuntimeError(
            "Document loading produced warnings/errors. "
            "Refusing to mutate Qdrant until all sources load successfully. "
            f"Details: {details}"
        )

    qdrant = QdrantService(settings)
    try:
        if not await qdrant.is_ready():
            raise RuntimeError("Qdrant is unavailable.")

        vector_store = QdrantVectorStore(
            qdrant.client,
            settings.qdrant_collection,
        )
        indexed_points = await vector_store.list_indexed_points()
        plan = build_ingestion_sync_plan(
            chunks,
            indexed_points,
            discovered_sources=discovered_sources,
        )

        print("RagTest ingestion sync")
        print(f"Mode               : {'apply' if apply else 'dry-run'}")
        print(f"Source files       : {len(discovered_sources)}")
        print(f"Files loaded       : {report.files_loaded}/{report.files_scanned}")
        print(f"Current chunks     : {plan.current_chunks}")
        print(f"Indexed points     : {plan.indexed_points}")
        print(f"Missing points     : {plan.missing_points}")
        print(f"Stale points       : {plan.stale_points}")
        print(f"Orphan sources     : {len(plan.orphan_sources)}")
        print(f"In sync before     : {'yes' if plan.in_sync else 'no'}")

        if report.errors:
            print()
            print("Document load warnings:")
            for error in report.errors:
                print(f"- {error.source}: {error.message}")

        if not apply:
            print()
            print("Dry-run only: no Qdrant points were changed.")
            return

        if plan.in_sync:
            print()
            print("No changes required. Qdrant was not modified.")
            return

        missing_chunks = select_missing_chunks(
            chunks,
            plan.missing_point_ids,
        )

        inserted = 0
        if missing_chunks:
            embeddings = create_embedding_provider(settings)
            sparse_embeddings = create_sparse_embedding_provider(settings)
            stats = await ingest_chunks(
                missing_chunks,
                embeddings=embeddings,
                sparse_embeddings=sparse_embeddings,
                vector_store=vector_store,
                upsert_batch_size=settings.upsert_batch_size,
                recreate=False,
            )
            inserted = stats.chunks_indexed

        # Delete only after every required replacement/new chunk has been upserted.
        deleted = await vector_store.delete_points(
            list(plan.stale_point_ids)
        )

        indexed_after = await vector_store.list_indexed_points()
        verification = build_ingestion_sync_plan(
            chunks,
            indexed_after,
            discovered_sources=discovered_sources,
        )

        print()
        print(f"Inserted points    : {inserted}")
        print(f"Deleted points     : {deleted}")
        print(f"Indexed after      : {verification.indexed_points}")
        print(f"Missing after      : {verification.missing_points}")
        print(f"Stale after        : {verification.stale_points}")
        print(f"Orphans after      : {len(verification.orphan_sources)}")
        print(f"In sync after      : {'yes' if verification.in_sync else 'no'}")

        if not verification.in_sync:
            raise RuntimeError(
                "Qdrant synchronization finished with remaining differences. "
                "Inspect the plan before retrying."
            )
    finally:
        await qdrant.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(apply=args.apply))


if __name__ == "__main__":
    main()
