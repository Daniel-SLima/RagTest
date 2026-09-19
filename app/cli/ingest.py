import argparse
import asyncio

from app.core.config import get_settings
from app.rag.chunking import split_documents
from app.rag.embeddings.factory import create_embedding_provider
from app.rag.ingestion import ingest_chunks
from app.rag.loaders import load_source_documents
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index RagTest source documents in Qdrant.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the collection before indexing.",
    )
    return parser.parse_args()


async def run(recreate: bool) -> None:
    settings = get_settings()
    report = load_source_documents(settings.source_dir)

    if report.errors:
        print("Document load warnings:")
        for error in report.errors:
            print(f"- {error.source}: {error.message}")

    chunks = split_documents(
        report.documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    if not chunks:
        raise RuntimeError("No chunks were generated from the source documents.")

    qdrant = QdrantService(settings)
    try:
        if not await qdrant.is_ready():
            raise RuntimeError("Qdrant is unavailable.")

        embeddings = create_embedding_provider(settings)
        vector_store = QdrantVectorStore(
            qdrant.client,
            settings.qdrant_collection,
        )

        print("RagTest ingestion")
        print(f"Files loaded     : {report.files_loaded}/{report.files_scanned}")
        print(f"Chunks to index  : {len(chunks)}")
        print(f"Embedding model  : {embeddings.model_name}")
        print(f"Collection       : {settings.qdrant_collection}")
        print("First execution may download the embedding model...")

        stats = await ingest_chunks(
            chunks,
            embeddings=embeddings,
            vector_store=vector_store,
            upsert_batch_size=settings.upsert_batch_size,
            recreate=recreate,
        )

        print(f"Vector dimension : {stats.vector_size}")
        print(f"Chunks indexed   : {stats.chunks_indexed}")
        print(
            "Collection       : "
            + ("created/recreated" if stats.collection_created else "reused")
        )
        print("Ingestion complete.")
    finally:
        await qdrant.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(recreate=args.recreate))


if __name__ == "__main__":
    main()
