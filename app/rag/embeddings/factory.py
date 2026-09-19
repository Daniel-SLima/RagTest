from app.core.config import Settings
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.embeddings.fastembed_provider import FastEmbedProvider
from app.rag.embeddings.sparse_fastembed_provider import FastEmbedSparseProvider


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider != "fastembed":
        raise ValueError(
            f"Unsupported embedding provider: {settings.embedding_provider}. "
            "Supported providers: fastembed"
        )

    return FastEmbedProvider(
        model_name=settings.embedding_model,
        cache_dir=settings.embedding_cache_dir,
        batch_size=settings.embedding_batch_size,
    )


def create_sparse_embedding_provider(settings: Settings) -> SparseEmbeddingProvider:
    if settings.sparse_embedding_provider != "fastembed_bm25":
        raise ValueError(
            f"Unsupported sparse embedding provider: {settings.sparse_embedding_provider}. "
            "Supported providers: fastembed_bm25"
        )

    return FastEmbedSparseProvider(
        model_name=settings.sparse_embedding_model,
        cache_dir=settings.embedding_cache_dir,
        language=settings.sparse_embedding_language,
        batch_size=settings.embedding_batch_size,
    )
