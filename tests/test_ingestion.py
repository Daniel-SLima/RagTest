from langchain_core.documents import Document
import pytest

from app.rag.ingestion import ingest_chunks


class FakeEmbeddings:
    model_name = "fake"

    async def dimension(self) -> int:
        return 3

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 0.0, 1.0] for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [float(len(text)), 0.0, 1.0]


class FakeVectorStore:
    def __init__(self) -> None:
        self.batches: list[int] = []

    async def ensure_collection(self, vector_size: int, *, recreate: bool = False) -> bool:
        assert vector_size == 3
        assert recreate is False
        return True

    async def upsert(
        self,
        documents: list[Document],
        vectors: list[list[float]],
    ) -> int:
        assert len(documents) == len(vectors)
        self.batches.append(len(documents))
        return len(documents)


@pytest.mark.asyncio
async def test_ingestion_batches_chunks_and_counts_points() -> None:
    chunks = [Document(page_content=f"chunk {index}") for index in range(5)]
    store = FakeVectorStore()

    stats = await ingest_chunks(
        chunks,
        embeddings=FakeEmbeddings(),
        vector_store=store,
        upsert_batch_size=2,
    )

    assert store.batches == [2, 2, 1]
    assert stats.chunks_indexed == 5
    assert stats.vector_size == 3
    assert stats.collection_created is True
