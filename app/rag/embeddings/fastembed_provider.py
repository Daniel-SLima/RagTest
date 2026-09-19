import asyncio
from pathlib import Path

from fastembed import TextEmbedding


class FastEmbedProvider:
    def __init__(
        self,
        *,
        model_name: str,
        cache_dir: Path,
        batch_size: int = 32,
    ) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir
        self._batch_size = batch_size
        self._model: TextEmbedding | None = None
        self._dimension: int | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_model(self) -> TextEmbedding:
        if self._model is None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._model = TextEmbedding(
                model_name=self._model_name,
                cache_dir=str(self._cache_dir),
            )
        return self._model

    def _embed_documents_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        vectors = model.passage_embed(texts, batch_size=self._batch_size)
        return [vector.tolist() for vector in vectors]

    def _embed_query_sync(self, text: str) -> list[float]:
        model = self._get_model()
        vector = next(iter(model.query_embed(text)))
        return vector.tolist()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_documents_sync, texts)

    async def embed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_query_sync, text)

    async def dimension(self) -> int:
        if self._dimension is None:
            probe = await self.embed_documents(["dimension probe"])
            self._dimension = len(probe[0])
        return self._dimension
