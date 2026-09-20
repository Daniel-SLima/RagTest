from dataclasses import dataclass

from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore, SearchHit


@dataclass(frozen=True, slots=True)
class MultiQueryHit:
    hit: SearchHit
    fusion_score: float
    matched_query_indexes: tuple[int, ...]
    best_rank: int


def _hit_key(hit: SearchHit) -> tuple[str, int | str]:
    if hit.page is not None:
        return hit.source, hit.page
    return hit.source, hit.id


def reciprocal_rank_fuse_hits(
    query_results: list[list[SearchHit]],
    *,
    limit: int = 5,
    rrf_k: int = 60,
) -> list[MultiQueryHit]:
    if limit <= 0:
        return []
    if rrf_k < 0:
        raise ValueError("rrf_k must be >= 0")

    scores: dict[tuple[str, int | str], float] = {}
    matched_queries: dict[tuple[str, int | str], set[int]] = {}
    best_ranks: dict[tuple[str, int | str], int] = {}
    representatives: dict[tuple[str, int | str], SearchHit] = {}

    for query_index, hits in enumerate(query_results, start=1):
        seen_in_query: set[tuple[str, int | str]] = set()

        for rank, hit in enumerate(hits, start=1):
            key = _hit_key(hit)
            if key in seen_in_query:
                continue
            seen_in_query.add(key)

            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
            matched_queries.setdefault(key, set()).add(query_index)

            previous_rank = best_ranks.get(key)
            if previous_rank is None or rank < previous_rank:
                best_ranks[key] = rank
                representatives[key] = hit
            elif rank == previous_rank:
                current = representatives[key]
                current_score = (
                    current.rank_score if current.rank_score is not None else current.score
                )
                candidate_score = hit.rank_score if hit.rank_score is not None else hit.score
                if candidate_score > current_score:
                    representatives[key] = hit

    ordered_keys = sorted(
        scores,
        key=lambda key: (
            -scores[key],
            best_ranks[key],
            representatives[key].source,
            representatives[key].page if representatives[key].page is not None else -1,
        ),
    )

    return [
        MultiQueryHit(
            hit=representatives[key],
            fusion_score=scores[key],
            matched_query_indexes=tuple(sorted(matched_queries[key])),
            best_rank=best_ranks[key],
        )
        for key in ordered_keys[:limit]
    ]


async def multi_query_search(
    queries: list[str],
    *,
    embeddings: EmbeddingProvider,
    sparse_embeddings: SparseEmbeddingProvider | None = None,
    vector_store: QdrantVectorStore,
    limit: int = 5,
    per_query_limit: int = 5,
    category: str | None = None,
    audience: str | None = None,
    min_score: float | None = None,
    candidate_multiplier: int = 8,
    score_margin: float = 0.22,
    merge_same_page: bool = True,
    max_group_chars: int = 5000,
    source_lexical_weight: float = 0.25,
    content_lexical_weight: float = 0.05,
    hybrid_dense_weight: float = 1.0,
    hybrid_sparse_weight: float = 1.2,
    rrf_k: int = 60,
) -> tuple[list[str], list[list[SearchHit]], list[MultiQueryHit]]:
    normalized_queries: list[str] = []
    seen_queries: set[str] = set()

    for query in queries:
        cleaned = query.strip()
        if not cleaned:
            continue
        normalized = " ".join(cleaned.casefold().split())
        if normalized in seen_queries:
            continue
        seen_queries.add(normalized)
        normalized_queries.append(cleaned)

    if not normalized_queries:
        return [], [], []

    query_results: list[list[SearchHit]] = []
    for query in normalized_queries:
        hits = await semantic_search(
            query,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings,
            vector_store=vector_store,
            limit=per_query_limit,
            category=category,
            audience=audience,
            min_score=min_score,
            candidate_multiplier=candidate_multiplier,
            score_margin=score_margin,
            merge_same_page=merge_same_page,
            max_group_chars=max_group_chars,
            source_lexical_weight=source_lexical_weight,
            content_lexical_weight=content_lexical_weight,
            hybrid_dense_weight=hybrid_dense_weight,
            hybrid_sparse_weight=hybrid_sparse_weight,
        )
        query_results.append(hits)

    fused = reciprocal_rank_fuse_hits(
        query_results,
        limit=limit,
        rrf_k=rrf_k,
    )
    return normalized_queries, query_results, fused
