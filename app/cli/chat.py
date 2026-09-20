import argparse
import asyncio

from app.core.config import get_settings
from app.llm.factory import create_llm_provider
from app.rag.chat import answer_with_rag
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.retrieval_profiles import PROFILES, get_profile
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask a grounded question to RagTest.")
    parser.add_argument("message", help="Question to send to the RAG chat.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--category", default=None)
    parser.add_argument("--audience", default=None)
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument(
        "--mode",
        choices=tuple(PROFILES),
        default=None,
        help="Override the configured retrieval mode for this chat request.",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    settings = get_settings()
    profile = get_profile(args.mode or settings.retrieval_mode)
    qdrant = QdrantService(settings)

    try:
        embeddings = create_embedding_provider(settings)
        sparse_embeddings = (
            create_sparse_embedding_provider(settings)
            if profile.use_sparse
            else None
        )
        vector_store = QdrantVectorStore(qdrant.client, settings.qdrant_collection)
        llm = create_llm_provider(settings)

        result = await answer_with_rag(
            args.message,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings,
            vector_store=vector_store,
            llm=llm,
            limit=args.limit,
            category=args.category,
            audience=args.audience,
            min_score=args.min_score,
            candidate_multiplier=profile.candidate_multiplier,
            score_margin=profile.score_margin,
            merge_same_page=settings.retrieval_merge_same_page,
            max_group_chars=settings.retrieval_max_group_chars,
            source_lexical_weight=profile.source_lexical_weight,
            content_lexical_weight=profile.content_lexical_weight,
            hybrid_dense_weight=profile.dense_weight,
            hybrid_sparse_weight=profile.sparse_weight,
        )

        print()
        print(f"Retrieval mode: {profile.name}")
        print("Answer:")
        print(result.answer)
        print()
        print(f"Model: {result.model}")
        print("Sources:")
        for index, hit in enumerate(result.sources, start=1):
            page = f", page {hit.page}" if hit.page is not None else ""
            print(
                f"[{index}] {hit.source}{page} "
                f"(retrieval={hit.score:.4f}, audience={hit.audience or '-'}, "
                f"grouped_chunks={hit.chunk_count})"
            )
    finally:
        await qdrant.close()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
