from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.hybrid.fusion import reciprocal_rank_fusion

from app.rag.embeddings.base import SparseVectorData


@dataclass(frozen=True, slots=True)
class IndexedPointRef:
    id: str
    source: str


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
    chunk_count: int = 1
    rank_score: float | None = None
    dense_score: float | None = None
    sparse_score: float | None = None


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
            sparse_config = info.config.params.sparse_vectors or {}

            compatible_dense = (
                isinstance(vectors_config, dict)
                and isinstance(vectors_config.get("dense"), models.VectorParams)
                and vectors_config["dense"].size == vector_size
            )
            compatible_sparse = "sparse" in sparse_config

            if not compatible_dense or not compatible_sparse:
                raise RuntimeError(
                    "Existing Qdrant collection uses the previous dense-only schema. "
                    "Run ragtest-ingest --recreate to enable hybrid retrieval."
                )
            return False

        await self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
            },
        )

        for field_name in ("category", "audience", "source", "file_type"):
            await self._client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
                wait=True,
            )

        return True

    async def list_indexed_points(
        self,
        *,
        page_size: int = 256,
    ) -> list[IndexedPointRef]:
        if page_size <= 0:
            raise ValueError("page_size must be greater than zero")
        if not await self._client.collection_exists(self.collection_name):
            raise RuntimeError(
                "Qdrant collection does not exist yet. Run ragtest-ingest first."
            )

        points: list[IndexedPointRef] = []
        offset: Any = None

        while True:
            records, next_offset = await self._client.scroll(
                collection_name=self.collection_name,
                limit=page_size,
                offset=offset,
                with_payload=["source"],
                with_vectors=False,
            )
            for record in records:
                payload = dict(record.payload or {})
                source = str(payload.get("source", "")).strip()
                if not source:
                    raise RuntimeError(
                        f"Indexed point {record.id} does not contain source metadata."
                    )
                points.append(
                    IndexedPointRef(
                        id=str(record.id),
                        source=source,
                    )
                )

            if next_offset is None:
                break
            offset = next_offset

        return points

    async def delete_points(self, point_ids: list[str]) -> int:
        if not point_ids:
            return 0

        await self._client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=point_ids),
            wait=True,
        )
        return len(point_ids)

    async def upsert(
        self,
        documents: list[Document],
        dense_vectors: list[list[float]],
        sparse_vectors: list[SparseVectorData],
    ) -> int:
        if len(documents) != len(dense_vectors) or len(documents) != len(sparse_vectors):
            raise ValueError("documents, dense_vectors and sparse_vectors must match")

        points: list[models.PointStruct] = []
        for document, dense_vector, sparse_vector in zip(
            documents,
            dense_vectors,
            sparse_vectors,
            strict=True,
        ):
            payload = {"text": document.page_content, **document.metadata}
            points.append(
                models.PointStruct(
                    id=deterministic_point_id(document),
                    vector={
                        "dense": dense_vector,
                        "sparse": models.SparseVector(
                            indices=sparse_vector.indices,
                            values=sparse_vector.values,
                        ),
                    },
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

    def _filter(
        self,
        *,
        category: str | None,
        audience: str | None,
    ) -> models.Filter | None:
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
        return models.Filter(must=conditions) if conditions else None

    async def search(
        self,
        query_vector: list[float],
        *,
        sparse_query_vector: SparseVectorData | None = None,
        limit: int = 5,
        category: str | None = None,
        audience: str | None = None,
        min_score: float | None = None,
        dense_weight: float = 1.0,
        sparse_weight: float = 1.2,
    ) -> list[SearchHit]:
        if not await self._client.collection_exists(self.collection_name):
            raise RuntimeError(
                "Qdrant collection does not exist yet. Run ragtest-ingest first."
            )

        query_filter = self._filter(category=category, audience=audience)

        dense_response = await self._client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            using="dense",
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            score_threshold=min_score,
        )

        dense_scores = {
            str(point.id): float(point.score)
            for point in dense_response.points
        }

        if sparse_query_vector is None:
            points = dense_response.points
            sparse_scores: dict[str, float] = {}
        else:
            sparse_response = await self._client.query_points(
                collection_name=self.collection_name,
                query=models.SparseVector(
                    indices=sparse_query_vector.indices,
                    values=sparse_query_vector.values,
                ),
                using="sparse",
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            sparse_scores = {
                str(point.id): float(point.score)
                for point in sparse_response.points
            }
            points = reciprocal_rank_fusion(
                [dense_response.points, sparse_response.points],
                limit=limit,
                weights=[dense_weight, sparse_weight],
            )

        hits: list[SearchHit] = []
        for point in points:
            payload = dict(point.payload or {})
            page = payload.get("page")
            point_id = str(point.id)
            hits.append(
                SearchHit(
                    id=point_id,
                    score=float(point.score),
                    dense_score=dense_scores.get(point_id),
                    sparse_score=sparse_scores.get(point_id),
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
