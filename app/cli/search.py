import argparse
import asyncio

from app.core.config import get_settings
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.retrieval_profiles import PROFILES, get_profile
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run document retrieval in RagTest.")
    parser.add_argument("query", help="Natural-language search query.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--category", default=None)
    parser.add_argument("--audience", default=None)
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument(
        "--mode",
        choices=tuple(PROFILES),
        default=None,
        help="Override the configured retrieval mode for this search.",
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

        hits = await semantic_search(
            args.query,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings,
            vector_store=vector_store,
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

        print(f'Mode: {profile.name}')
        print(f'Query: "{args.query}"')
        print(f"Results: {len(hits)}")
        for index, hit in enumerate(hits, start=1):
            page = f" | page {hit.page}" if hit.page is not None else ""
            excerpt = " ".join(hit.content.split())
            if len(excerpt) > 320:
                excerpt = excerpt[:317] + "..."
            rank_score = hit.rank_score if hit.rank_score is not None else hit.score
            dense = f"{hit.dense_score:.4f}" if hit.dense_score is not None else "-"
            sparse = f"{hit.sparse_score:.4f}" if hit.sparse_score is not None else "-"
            print()
            print(
                f"#{index} retrieval={hit.score:.4f} rank={rank_score:.4f} "
                f"dense={dense} sparse={sparse} grouped_chunks={hit.chunk_count}"
            )
            print(f"{hit.source}{page} | audience={hit.audience or '-'}")
            print(excerpt)
    finally:
        await qdrant.close()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
