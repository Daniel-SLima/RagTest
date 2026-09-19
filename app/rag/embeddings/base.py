from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class SparseVectorData:
    indices: list[int]
    values: list[float]


class EmbeddingProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    async def dimension(self) -> int: ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


class SparseEmbeddingProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    async def embed_documents(self, texts: list[str]) -> list[SparseVectorData]: ...

    async def embed_query(self, text: str) -> SparseVectorData: ...
