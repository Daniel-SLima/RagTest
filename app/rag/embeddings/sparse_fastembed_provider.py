import asyncio
from pathlib import Path

from fastembed import SparseTextEmbedding

from app.rag.embeddings.base import SparseVectorData


class FastEmbedSparseProvider:
    def __init__(
        self,
        *,
        model_name: str,
        cache_dir: Path,
        language: str = "portuguese",
        batch_size: int = 32,
    ) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir
        self._language = language
        self._batch_size = batch_size
        self._model: SparseTextEmbedding | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_model(self) -> SparseTextEmbedding:
        if self._model is None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._model = SparseTextEmbedding(
                model_name=self._model_name,
                cache_dir=str(self._cache_dir),
                language=self._language,
            )
        return self._model

    @staticmethod
    def _convert(vector) -> SparseVectorData:
        return SparseVectorData(
            indices=[int(value) for value in vector.indices],
            values=[float(value) for value in vector.values],
        )

    def _embed_documents_sync(self, texts: list[str]) -> list[SparseVectorData]:
        vectors = self._get_model().embed(texts, batch_size=self._batch_size)
        return [self._convert(vector) for vector in vectors]

    def _embed_query_sync(self, text: str) -> SparseVectorData:
        vector = next(iter(self._get_model().query_embed(text)))
        return self._convert(vector)

    async def embed_documents(self, texts: list[str]) -> list[SparseVectorData]:
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_documents_sync, texts)

    async def embed_query(self, text: str) -> SparseVectorData:
        return await asyncio.to_thread(self._embed_query_sync, text)
