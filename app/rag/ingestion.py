from dataclasses import dataclass

from langchain_core.documents import Document

from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.vector_store import QdrantVectorStore


@dataclass(slots=True)
class IngestionStats:
    chunks_indexed: int
    vector_size: int
    collection_created: bool


def build_sparse_index_text(document: Document) -> str:
    metadata = document.metadata
    header_parts = [
        str(metadata.get("source", "")),
        str(metadata.get("filename", "")),
        str(metadata.get("category", "")),
        str(metadata.get("audience", "")),
    ]
    header = " ".join(part for part in header_parts if part)
    if not header:
        return document.page_content

    return f"{header}\n{document.page_content}"


async def ingest_chunks(
    chunks: list[Document],
    *,
    embeddings: EmbeddingProvider,
    sparse_embeddings: SparseEmbeddingProvider,
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
        dense_texts = [document.page_content for document in batch]
        sparse_texts = [build_sparse_index_text(document) for document in batch]

        dense_vectors = await embeddings.embed_documents(dense_texts)
        sparse_vectors = await sparse_embeddings.embed_documents(sparse_texts)
        indexed += await vector_store.upsert(
            batch,
            dense_vectors,
            sparse_vectors,
        )

    return IngestionStats(
        chunks_indexed=indexed,
        vector_size=vector_size,
        collection_created=collection_created,
    )
