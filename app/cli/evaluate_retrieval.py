import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.evaluation import EVALUATION_DATASET_VERSION, select_retrieval_cases
from app.evaluation.metrics import evaluate_case_sources, first_expected_rank
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.retrieval_profiles import RetrievalProfile, selected_profiles
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


@dataclass(frozen=True, slots=True)
class AggregateMetrics:
    hit_rate: float
    mrr: float
    source_recall: float
    source_ndcg: float


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


async def _evaluate_profile(
    *,
    profile: RetrievalProfile,
    cases: list[dict[str, Any]],
    limit: int,
    embeddings,
    sparse_embeddings,
    store: QdrantVectorStore,
    settings,
) -> AggregateMetrics:
    hits_count = 0
    reciprocal_rank_sum = 0.0
    source_recall_sum = 0.0
    source_ndcg_sum = 0.0

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
        rank = first_expected_rank(sources, expected_sources)
        case_metrics = evaluate_case_sources(sources, expected_sources, limit)

        if case_metrics.hit:
            hits_count += 1

        reciprocal_rank_sum += case_metrics.reciprocal_rank
        source_recall_sum += case_metrics.source_recall
        source_ndcg_sum += case_metrics.source_ndcg

        print(
            f"[{'PASS' if case_metrics.hit else 'FAIL'}] {index}. [{case_id}] {query} "
            f"| first_expected_rank={rank or '-'} "
            f"| source_recall={case_metrics.source_recall:.3f} "
            f"| source_ndcg={case_metrics.source_ndcg:.3f} "
            f"| unique_sources={case_metrics.unique_sources}"
        )
        for result_rank, hit in enumerate(hits, start=1):
            page = f":{hit.page}" if hit.page is not None else ""
            effective = hit.rank_score if hit.rank_score is not None else hit.score
            print(
                f"    {result_rank}. {hit.source}{page} "
                f"retrieval={hit.score:.4f} rank={effective:.4f}"
            )

    total = len(cases)
    metrics = AggregateMetrics(
        hit_rate=(hits_count / total) if total else 0.0,
        mrr=(reciprocal_rank_sum / total) if total else 0.0,
        source_recall=(source_recall_sum / total) if total else 0.0,
        source_ndcg=(source_ndcg_sum / total) if total else 0.0,
    )

    print()
    print(f"HitRate@{limit}: {metrics.hit_rate:.3f} ({hits_count}/{total})")
    print(f"MRR@{limit}: {metrics.mrr:.3f}")
    print(f"SourceRecall@{limit}: {metrics.source_recall:.3f}")
    print(f"SourceNDCG@{limit}: {metrics.source_ndcg:.3f}")
    return metrics


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
        print(
            "Metrics: legacy HitRate/MRR + source-level Recall/NDCG "
            "(duplicate source pages count once as relevant)."
        )

        results: list[tuple[str, AggregateMetrics]] = []
        for profile in profiles:
            metrics = await _evaluate_profile(
                profile=profile,
                cases=cases,
                limit=limit,
                embeddings=embeddings,
                sparse_embeddings=sparse_embeddings,
                store=store,
                settings=settings,
            )
            results.append((profile.name, metrics))

        if len(results) > 1:
            print()
            print("=== summary ===")
            print("MODE            HITRATE      MRR  SRC_RECALL  SRC_NDCG")
            for name, metrics in results:
                print(
                    f"{name:<15} "
                    f"{metrics.hit_rate:>7.3f}  "
                    f"{metrics.mrr:>7.3f}  "
                    f"{metrics.source_recall:>10.3f}  "
                    f"{metrics.source_ndcg:>8.3f}"
                )
    finally:
        await qdrant.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args.cases, args.limit, args.mode, args.suite))


if __name__ == "__main__":
    main()
