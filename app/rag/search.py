from app.rag.embeddings.base import EmbeddingProvider
from app.rag.retrieval_quality import apply_relative_score_floor, group_hits_by_page
from app.rag.vector_store import QdrantVectorStore, SearchHit


async def semantic_search(
    query: str,
    *,
    embeddings: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    limit: int = 5,
    category: str | None = None,
    audience: str | None = None,
    min_score: float | None = None,
    candidate_multiplier: int = 4,
    score_margin: float = 0.22,
    merge_same_page: bool = True,
    max_group_chars: int = 5000,
) -> list[SearchHit]:
    query_vector = await embeddings.embed_query(query)

    candidate_limit = max(limit, limit * max(candidate_multiplier, 1))
    hits = await vector_store.search(
        query_vector,
        limit=candidate_limit,
        category=category,
        audience=audience,
        min_score=min_score,
    )

    if merge_same_page:
        hits = group_hits_by_page(hits, max_group_chars=max_group_chars)

    hits = apply_relative_score_floor(hits, score_margin=score_margin)
    return hits[:limit]
