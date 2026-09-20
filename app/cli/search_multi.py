import argparse
import asyncio

from app.core.config import get_settings
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.multi_query import multi_query_search, select_fusion_queries
from app.rag.retrieval_profiles import PROFILES, get_profile
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a controlled multi-query retrieval experiment in RagTest."
    )
    parser.add_argument("query", help="Original natural-language query.")
    parser.add_argument(
        "--subquery",
        action="append",
        default=[],
        help="Manual decomposition query. Repeat the option for each subquery.",
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--per-query-limit", type=int, default=5)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument(
        "--include-original",
        action="store_true",
        help=(
            "Include the original compound question as an RRF voter even when "
            "subqueries are provided. Default: fuse only the explicit subqueries."
        ),
    )
    parser.add_argument("--category", default=None)
    parser.add_argument("--audience", default=None)
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument(
        "--mode",
        choices=tuple(PROFILES),
        default=None,
        help="Override the configured retrieval mode.",
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

        fusion_queries = select_fusion_queries(
            args.query,
            args.subquery,
            include_original=args.include_original,
        )

        queries, query_results, fused = await multi_query_search(
            fusion_queries,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings,
            vector_store=vector_store,
            limit=args.limit,
            per_query_limit=args.per_query_limit,
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
            rrf_k=args.rrf_k,
        )

        print(f"Mode: {profile.name}")
        print(f'Original query: "{args.query}"')
        print(
            "Fusion policy: "
            + ("original + subqueries" if args.include_original else "subqueries only")
        )
        print(f"Queries: {len(queries)}")
        for index, query in enumerate(queries, start=1):
            print(f'Q{index}: "{query}"')

        print()
        print("Per-query ranks:")
        for query_index, hits in enumerate(query_results, start=1):
            pages = ", ".join(
                (
                    f"{hit.source}:{hit.page}"
                    if hit.page is not None
                    else f"{hit.source}:{hit.id}"
                )
                for hit in hits
            )
            print(f"Q{query_index}: {pages or '-'}")

        print()
        print(f"Fused results: {len(fused)}")
        for index, item in enumerate(fused, start=1):
            hit = item.hit
            page = f" | page {hit.page}" if hit.page is not None else ""
            matched = ",".join(f"Q{query_index}" for query_index in item.matched_query_indexes)
            excerpt = " ".join(hit.content.split())
            if len(excerpt) > 320:
                excerpt = excerpt[:317] + "..."

            print()
            print(
                f"#{index} fusion={item.fusion_score:.6f} "
                f"matched={matched} best_rank={item.best_rank}"
            )
            print(f"{hit.source}{page} | audience={hit.audience or '-'}")
            print(excerpt)
    finally:
        await qdrant.close()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
