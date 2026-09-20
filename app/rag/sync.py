from collections import defaultdict
from dataclasses import dataclass

from langchain_core.documents import Document

from app.rag.vector_store import IndexedPointRef, deterministic_point_id


@dataclass(frozen=True, slots=True)
class SourceSyncDelta:
    source: str
    current_chunks: int
    indexed_points: int
    missing_points: int
    stale_points: int


@dataclass(frozen=True, slots=True)
class IngestionSyncPlan:
    current_sources: int
    indexed_sources: int
    current_chunks: int
    indexed_points: int
    missing_point_ids: tuple[str, ...]
    stale_point_ids: tuple[str, ...]
    orphan_sources: tuple[str, ...]
    source_deltas: tuple[SourceSyncDelta, ...]

    @property
    def missing_points(self) -> int:
        return len(self.missing_point_ids)

    @property
    def stale_points(self) -> int:
        return len(self.stale_point_ids)

    @property
    def in_sync(self) -> bool:
        return self.missing_points == 0 and self.stale_points == 0


def build_ingestion_sync_plan(
    chunks: list[Document],
    indexed_points: list[IndexedPointRef],
    *,
    discovered_sources: set[str],
) -> IngestionSyncPlan:
    current_ids_by_source: dict[str, set[str]] = defaultdict(set)
    for chunk in chunks:
        source = str(chunk.metadata.get("source", "")).strip()
        if not source:
            raise ValueError("Every chunk must contain a non-empty source metadata field")
        current_ids_by_source[source].add(deterministic_point_id(chunk))

    indexed_ids_by_source: dict[str, set[str]] = defaultdict(set)
    for point in indexed_points:
        indexed_ids_by_source[point.source].add(point.id)

    missing_ids: set[str] = set()
    stale_ids: set[str] = set()
    source_deltas: list[SourceSyncDelta] = []

    all_sources = sorted(discovered_sources | set(indexed_ids_by_source))
    for source in all_sources:
        current_ids = current_ids_by_source.get(source, set())
        indexed_ids = indexed_ids_by_source.get(source, set())

        source_missing = current_ids - indexed_ids
        if source in discovered_sources:
            source_stale = indexed_ids - current_ids
        else:
            source_stale = indexed_ids

        missing_ids.update(source_missing)
        stale_ids.update(source_stale)

        if source_missing or source_stale:
            source_deltas.append(
                SourceSyncDelta(
                    source=source,
                    current_chunks=len(current_ids),
                    indexed_points=len(indexed_ids),
                    missing_points=len(source_missing),
                    stale_points=len(source_stale),
                )
            )

    orphan_sources = tuple(
        sorted(set(indexed_ids_by_source) - discovered_sources)
    )

    return IngestionSyncPlan(
        current_sources=len(discovered_sources),
        indexed_sources=len(indexed_ids_by_source),
        current_chunks=sum(len(ids) for ids in current_ids_by_source.values()),
        indexed_points=len(indexed_points),
        missing_point_ids=tuple(sorted(missing_ids)),
        stale_point_ids=tuple(sorted(stale_ids)),
        orphan_sources=orphan_sources,
        source_deltas=tuple(source_deltas),
    )
