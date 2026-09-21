import argparse
import asyncio

from app.core.config import get_settings
from app.llm.base import LLMServiceUnavailableError
from app.llm.factory import create_llm_provider
from app.rag.chat import answer_with_rag
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.retrieval_profiles import PROFILES, get_profile
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def _format_seconds(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}s"


def _format_rate(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f} tok/s"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask a grounded question to RagTest.")
    parser.add_argument("message", help="Question to send to the RAG chat.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--category", default=None)
    parser.add_argument("--audience", default=None)
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument(
        "--no-decompose",
        action="store_true",
        help="Disable automatic multi-intent decomposition for this request.",
    )
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
            auto_decompose=settings.retrieval_auto_decompose and not args.no_decompose,
            max_subqueries=settings.retrieval_max_subqueries,
        )

        print()
        print(f"Retrieval mode: {profile.name}")
        print(f"Decomposition status: {result.decomposition_status}")
        print(f"Multi-query used: {'yes' if result.multi_query_used else 'no'}")
        print(f"Retrieval queries: {result.retrieval_queries or [args.message]}")
        print(f"Grounded: {'yes' if result.grounded else 'no'}")
        print(f"Citation ids: {result.citation_ids or '-'}")
        print(f"Citation retries: {result.citation_retry_count}")
        if result.citation_validation_attempts:
            print("Citation validation attempts:")
            for index, attempt in enumerate(result.citation_validation_attempts, start=1):
                print(
                    f"  [{index}] stage={attempt.stage} "
                    f"valid={'yes' if attempt.valid else 'no'} "
                    f"syntax={'yes' if attempt.syntax_valid else 'no'} "
                    f"coverage={attempt.coverage:.3f} "
                    f"blocks={attempt.cited_claim_blocks}/{attempt.total_claim_blocks} "
                    f"reason={attempt.reason or '-'}"
                )

        generation_metrics = getattr(llm, "generation_metrics", ())
        if generation_metrics:
            print("LLM generation metrics:")
            for index, metric in enumerate(generation_metrics, start=1):
                print(
                    f"  [{index}] total={_format_seconds(metric.total_seconds)} "
                    f"load={_format_seconds(metric.load_seconds)} "
                    f"prompt_tokens={metric.prompt_tokens or '-'} "
                    f"prompt={_format_seconds(metric.prompt_seconds)} "
                    f"output_tokens={metric.output_tokens or '-'} "
                    f"output={_format_seconds(metric.output_seconds)} "
                    f"rate={_format_rate(metric.output_tokens_per_second)} "
                    f"done_reason={metric.done_reason or '-'}"
                )

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
    try:
        asyncio.run(run(parse_args()))
    except LLMServiceUnavailableError as exc:
        raise SystemExit(f"LLM temporariamente indisponível: {exc}") from None


if __name__ == "__main__":
    main()
