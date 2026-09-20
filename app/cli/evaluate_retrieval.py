import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.evaluation import EVALUATION_DATASET_VERSION, select_retrieval_cases
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.retrieval_profiles import RetrievalProfile, selected_profiles
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RagTest retrieval quality.")
    parser.add_argument("--cases", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--mode",
        choices=("dense", "dense-rerank", "hybrid", "all"),
        default="all",
        help="Retrieval strategy to evaluate. Default: all.",
    )
    parser.add_argument(
        "--suite",
        choices=("dev", "holdout", "all"),
        default="dev",
        help=(
            "Packaged evaluation suite. 'dev' preserves the historical seven cases; "
            "'holdout' contains frozen unseen queries; 'all' combines both."
        ),
    )
    return parser.parse_args()


def _load_cases(
    cases_path: Path | None,
    suite: str,
) -> tuple[list[dict[str, Any]], str]:
    if cases_path is not None:
        return json.loads(cases_path.read_text(encoding="utf-8")), "external JSON"

    return select_retrieval_cases(suite), f"packaged {suite}"


def _first_expected_rank(sources: list[str], expected_sources: list[str]) -> int | None:
    expected = set(expected_sources)
    for rank, source in enumerate(sources, start=1):
        if source in expected:
            return rank
    return None


async def _evaluate_profile(
    *,
    profile: RetrievalProfile,
    cases: list[dict[str, Any]],
    limit: int,
    embeddings,
    sparse_embeddings,
    store: QdrantVectorStore,
    settings,
) -> tuple[float, float]:
    hits_count = 0
    reciprocal_rank_sum = 0.0

    print()
    print(f"=== mode={profile.name} ===")

    for index, case in enumerate(cases, start=1):
        case_id = str(case.get("id", index))
        query = str(case["query"])
        expected_sources = [str(item) for item in case["expected_sources"]]

        hits = await semantic_search(
            query,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings if profile.use_sparse else None,
            vector_store=store,
            limit=limit,
            category=str(case["category"]) if case.get("category") else None,
            audience=str(case["audience"]) if case.get("audience") else None,
            candidate_multiplier=profile.candidate_multiplier,
            score_margin=profile.score_margin,
            merge_same_page=settings.retrieval_merge_same_page,
            max_group_chars=settings.retrieval_max_group_chars,
            source_lexical_weight=profile.source_lexical_weight,
            content_lexical_weight=profile.content_lexical_weight,
            hybrid_dense_weight=profile.dense_weight,
            hybrid_sparse_weight=profile.sparse_weight,
        )

        sources = [hit.source for hit in hits]
        rank = _first_expected_rank(sources, expected_sources)
        passed = rank is not None

        if passed:
            hits_count += 1
            reciprocal_rank_sum += 1.0 / rank

        print(
            f"[{'PASS' if passed else 'FAIL'}] {index}. [{case_id}] {query} "
            f"| first_expected_rank={rank or '-'}"
        )
        for result_rank, hit in enumerate(hits, start=1):
            page = f":{hit.page}" if hit.page is not None else ""
            effective = hit.rank_score if hit.rank_score is not None else hit.score
            print(
                f"    {result_rank}. {hit.source}{page} "
                f"retrieval={hit.score:.4f} rank={effective:.4f}"
            )

    total = len(cases)
    hit_rate = hits_count / total if total else 0.0
    mrr = reciprocal_rank_sum / total if total else 0.0

    print()
    print(f"HitRate@{limit}: {hit_rate:.3f} ({hits_count}/{total})")
    print(f"MRR@{limit}: {mrr:.3f}")
    return hit_rate, mrr


async def run(
    cases_path: Path | None,
    limit: int,
    mode: str,
    suite: str,
) -> None:
    cases, source_label = _load_cases(cases_path, suite)
    profiles = selected_profiles(mode)
    settings = get_settings()
    qdrant = QdrantService(settings)
    embeddings = create_embedding_provider(settings)
    sparse_embeddings = (
        create_sparse_embedding_provider(settings)
        if any(profile.use_sparse for profile in profiles)
        else None
    )
    store = QdrantVectorStore(qdrant.client, settings.qdrant_collection)

    try:
        print("RagTest retrieval benchmark")
        print(
            f"Dataset: {EVALUATION_DATASET_VERSION} | "
            f"Cases: {len(cases)} | k={limit} | source={source_label}"
        )

        results: list[tuple[str, float, float]] = []
        for profile in profiles:
            hit_rate, mrr = await _evaluate_profile(
                profile=profile,
                cases=cases,
                limit=limit,
                embeddings=embeddings,
                sparse_embeddings=sparse_embeddings,
                store=store,
                settings=settings,
            )
            results.append((profile.name, hit_rate, mrr))

        if len(results) > 1:
            print()
            print("=== summary ===")
            print("MODE            HITRATE      MRR")
            for name, hit_rate, mrr in results:
                print(f"{name:<15} {hit_rate:>7.3f}  {mrr:>7.3f}")
    finally:
        await qdrant.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args.cases, args.limit, args.mode, args.suite))


if __name__ == "__main__":
    main()
