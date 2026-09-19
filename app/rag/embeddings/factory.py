from app.core.config import Settings
from app.rag.embeddings.base import EmbeddingProvider
from app.rag.embeddings.fastembed_provider import FastEmbedProvider


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
