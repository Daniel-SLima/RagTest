from dataclasses import dataclass

from langchain_core.documents import Document

from app.rag.embeddings.base import EmbeddingProvider
from app.rag.vector_store import QdrantVectorStore


@dataclass(slots=True)
class IngestionStats:
    chunks_indexed: int
    vector_size: int
    collection_created: bool


async def ingest_chunks(
    chunks: list[Document],
    *,
    embeddings: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    upsert_batch_size: int,
    recreate: bool = False,
) -> IngestionStats:
    if upsert_batch_size <= 0:
        raise ValueError("upsert_batch_size must be greater than zero")
    if not chunks:
        raise ValueError("No chunks were provided for ingestion")

    vector_size = await embeddings.dimension()
    collection_created = await vector_store.ensure_collection(
        vector_size,
        recreate=recreate,
    )

    indexed = 0
    for start in range(0, len(chunks), upsert_batch_size):
        batch = chunks[start : start + upsert_batch_size]
        vectors = await embeddings.embed_documents(
            [document.page_content for document in batch]
        )
        indexed += await vector_store.upsert(batch, vectors)

    return IngestionStats(
        chunks_indexed=indexed,
        vector_size=vector_size,
        collection_created=collection_created,
    )
