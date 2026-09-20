import asyncio

from app.core.config import get_settings
from app.rag.chunking import split_documents
from app.rag.loaders import discover_source_files, load_source_documents
from app.rag.sync import build_ingestion_sync_plan
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


async def run() -> None:
    settings = get_settings()
    source_dir = settings.source_dir.resolve()

    source_files = discover_source_files(source_dir)
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

        print("RagTest ingestion sync plan")
        print(f"Source files       : {len(discovered_sources)}")
        print(f"Files loaded       : {report.files_loaded}/{report.files_scanned}")
        print(f"Current chunks     : {plan.current_chunks}")
        print(f"Indexed points     : {plan.indexed_points}")
        print(f"Current sources    : {plan.current_sources}")
        print(f"Indexed sources    : {plan.indexed_sources}")
        print(f"Missing points     : {plan.missing_points}")
        print(f"Stale points       : {plan.stale_points}")
        print(f"Orphan sources     : {len(plan.orphan_sources)}")
        print(f"In sync            : {'yes' if plan.in_sync else 'no'}")

        if report.errors:
            print()
            print("Document load warnings:")
            for error in report.errors:
                print(f"- {error.source}: {error.message}")

        if plan.orphan_sources:
            print()
            print("Orphan sources:")
            for source in plan.orphan_sources:
                print(f"- {source}")

        if plan.source_deltas:
            print()
            print("Sources with differences:")
            for delta in plan.source_deltas:
                print(
                    f"- {delta.source}: current={delta.current_chunks} "
                    f"indexed={delta.indexed_points} "
                    f"missing={delta.missing_points} stale={delta.stale_points}"
                )

        print()
        print("Read-only plan: no Qdrant points were changed.")
    finally:
        await qdrant.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
