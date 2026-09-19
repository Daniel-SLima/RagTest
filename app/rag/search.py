from app.rag.embeddings.base import EmbeddingProvider
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
) -> list[SearchHit]:
    query_vector = await embeddings.embed_query(query)
    return await vector_store.search(
        query_vector,
        limit=limit,
        category=category,
        audience=audience,
        min_score=min_score,
    )
