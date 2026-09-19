from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from qdrant_client import AsyncQdrantClient, models


@dataclass(slots=True)
class SearchHit:
    id: str
    score: float
    content: str
    source: str
    category: str | None
    audience: str | None
    page: int | None
    metadata: dict[str, Any]


def deterministic_point_id(document: Document) -> str:
    metadata = document.metadata
    content_hash = sha256(document.page_content.encode("utf-8")).hexdigest()
    identity = "|".join(
        [
            str(metadata.get("source", "")),
            str(metadata.get("page", "")),
            str(metadata.get("start_index", "")),
            content_hash,
        ]
    )
    return str(uuid5(NAMESPACE_URL, f"ragtest:{identity}"))


class QdrantVectorStore:
    def __init__(self, client: AsyncQdrantClient, collection_name: str) -> None:
        self._client = client
        self.collection_name = collection_name

    async def ensure_collection(self, vector_size: int, *, recreate: bool = False) -> bool:
        exists = await self._client.collection_exists(self.collection_name)

        if exists and recreate:
            await self._client.delete_collection(self.collection_name)
            exists = False

        if exists:
            info = await self._client.get_collection(self.collection_name)
            vectors_config = info.config.params.vectors
            if isinstance(vectors_config, models.VectorParams):
                if vectors_config.size != vector_size:
                    raise RuntimeError(
                        "Existing Qdrant collection has a different vector dimension. "
                        "Re-run ingestion with --recreate after changing embedding models."
                    )
            return False

        await self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

        for field_name in ("category", "audience", "source", "file_type"):
            await self._client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
                wait=True,
            )

        return True

    async def upsert(
        self,
        documents: list[Document],
        vectors: list[list[float]],
    ) -> int:
        if len(documents) != len(vectors):
            raise ValueError("documents and vectors must have the same length")

        points: list[models.PointStruct] = []
        for document, vector in zip(documents, vectors, strict=True):
            payload = {
                "text": document.page_content,
                **document.metadata,
            }
            points.append(
                models.PointStruct(
                    id=deterministic_point_id(document),
                    vector=vector,
                    payload=payload,
                )
            )

        if points:
            await self._client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )

        return len(points)

    async def search(
        self,
        query_vector: list[float],
        *,
        limit: int = 5,
        category: str | None = None,
        audience: str | None = None,
        min_score: float | None = None,
    ) -> list[SearchHit]:
        if not await self._client.collection_exists(self.collection_name):
            raise RuntimeError(
                "Qdrant collection does not exist yet. Run ragtest-ingest first."
            )

        conditions: list[models.FieldCondition] = []
        if category:
            conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=category),
                )
            )
        if audience:
            conditions.append(
                models.FieldCondition(
                    key="audience",
                    match=models.MatchValue(value=audience),
                )
            )

        query_filter = models.Filter(must=conditions) if conditions else None

        response = await self._client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            score_threshold=min_score,
        )

        hits: list[SearchHit] = []
        for point in response.points:
            payload = dict(point.payload or {})
            page = payload.get("page")
            hits.append(
                SearchHit(
                    id=str(point.id),
                    score=float(point.score),
                    content=str(payload.pop("text", "")),
                    source=str(payload.get("source", "")),
                    category=(
                        str(payload["category"])
                        if payload.get("category") is not None
                        else None
                    ),
                    audience=(
                        str(payload["audience"])
                        if payload.get("audience") is not None
                        else None
                    ),
                    page=int(page) if isinstance(page, int) else None,
                    metadata=payload,
                )
            )

        return hits
