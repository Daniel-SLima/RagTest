import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.evaluation import EVALUATION_DATASET_VERSION, select_retrieval_cases
from app.evaluation.labels import (
    evaluation_label_mode,
    parse_source_judgments,
)
from app.evaluation.metrics import (
    evaluate_case_sources,
    evaluate_explicit_case_sources,
    first_expected_rank,
)
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


@dataclass(frozen=True, slots=True)
class ExplicitAggregateMetrics:
    pass_rate: float
    mrr: float
    acceptable_hit_rate: float | None
    required_recall: float | None
    required_ndcg: float | None


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


async def _search_case(
    *,
    case: dict[str, Any],
    profile: RetrievalProfile,
    limit: int,
    embeddings,
    sparse_embeddings,
    store: QdrantVectorStore,
    settings,
):
    return await semantic_search(
        str(case["query"]),
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


def _print_hits(hits) -> None:
    for result_rank, hit in enumerate(hits, start=1):
        page = f":{hit.page}" if hit.page is not None else ""
        effective = hit.rank_score if hit.rank_score is not None else hit.score
        print(
            f"    {result_rank}. {hit.source}{page} "
            f"retrieval={hit.score:.4f} rank={effective:.4f}"
        )


async def _evaluate_profile_legacy(
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
        judgments = parse_source_judgments(case)
        expected_sources = list(judgments.legacy_expected_sources)

        hits = await _search_case(
            case=case,
            profile=profile,
            limit=limit,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings,
            store=store,
            settings=settings,
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
        _print_hits(hits)

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


async def _evaluate_profile_explicit(
    *,
    profile: RetrievalProfile,
    cases: list[dict[str, Any]],
    limit: int,
    embeddings,
    sparse_embeddings,
    store: QdrantVectorStore,
    settings,
) -> ExplicitAggregateMetrics:
    passed_count = 0
    reciprocal_rank_sum = 0.0
    acceptable_hits = 0
    acceptable_cases = 0
    required_recall_sum = 0.0
    required_ndcg_sum = 0.0
    required_cases = 0

    print()
    print(f"=== mode={profile.name} ===")

    for index, case in enumerate(cases, start=1):
        case_id = str(case.get("id", index))
        query = str(case["query"])
        judgments = parse_source_judgments(case)

        hits = await _search_case(
            case=case,
            profile=profile,
            limit=limit,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings,
            store=store,
            settings=settings,
        )
        sources = [hit.source for hit in hits]
        case_metrics = evaluate_explicit_case_sources(
            sources,
            list(judgments.acceptable_sources),
            list(judgments.required_sources),
            limit,
        )

        if case_metrics.passed:
            passed_count += 1
        reciprocal_rank_sum += case_metrics.reciprocal_rank

        acceptable_text = "-"
        if case_metrics.acceptable_hit is not None:
            acceptable_cases += 1
            if case_metrics.acceptable_hit:
                acceptable_hits += 1
            acceptable_text = "yes" if case_metrics.acceptable_hit else "no"

        required_recall_text = "-"
        required_ndcg_text = "-"
        if case_metrics.required_recall is not None:
            required_cases += 1
            required_recall_sum += case_metrics.required_recall
            required_ndcg_sum += case_metrics.required_ndcg or 0.0
            required_recall_text = f"{case_metrics.required_recall:.3f}"
            required_ndcg_text = f"{(case_metrics.required_ndcg or 0.0):.3f}"

        print(
            f"[{'PASS' if case_metrics.passed else 'FAIL'}] "
            f"{index}. [{case_id}] {query} "
            f"| acceptable_hit={acceptable_text} "
            f"| required_recall={required_recall_text} "
            f"| required_ndcg={required_ndcg_text} "
            f"| unique_sources={case_metrics.unique_sources}"
        )
        _print_hits(hits)

    total = len(cases)
    metrics = ExplicitAggregateMetrics(
        pass_rate=(passed_count / total) if total else 0.0,
        mrr=(reciprocal_rank_sum / total) if total else 0.0,
        acceptable_hit_rate=(
            acceptable_hits / acceptable_cases
            if acceptable_cases
            else None
        ),
        required_recall=(
            required_recall_sum / required_cases
            if required_cases
            else None
        ),
        required_ndcg=(
            required_ndcg_sum / required_cases
            if required_cases
            else None
        ),
    )

    print()
    print(f"PassRate@{limit}: {metrics.pass_rate:.3f} ({passed_count}/{total})")
    print(f"MRR@{limit}: {metrics.mrr:.3f}")
    if metrics.acceptable_hit_rate is not None:
        print(
            f"AcceptableHitRate@{limit}: "
            f"{metrics.acceptable_hit_rate:.3f}"
        )
    if metrics.required_recall is not None:
        print(f"RequiredRecall@{limit}: {metrics.required_recall:.3f}")
        print(f"RequiredNDCG@{limit}: {metrics.required_ndcg:.3f}")
    return metrics


def _format_optional(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "-"


async def run(
    cases_path: Path | None,
    limit: int,
    mode: str,
    suite: str,
) -> None:
    cases, source_label = _load_cases(cases_path, suite)
    label_mode = evaluation_label_mode(cases)
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
        print(f"Label semantics: {label_mode}")
        if label_mode == "legacy-ambiguous":
            print(
                "Metrics: historical HitRate/MRR + source-level Recall/NDCG. "
                "Multi-source expected_sources remains legacy/ambiguous."
            )
        else:
            print(
                "Metrics: PassRate/MRR + AcceptableHitRate for OR alternatives "
                "+ RequiredRecall/RequiredNDCG for AND-required sources."
            )

        results: list[tuple[str, AggregateMetrics | ExplicitAggregateMetrics]] = []
        for profile in profiles:
            if label_mode == "legacy-ambiguous":
                metrics = await _evaluate_profile_legacy(
                    profile=profile,
                    cases=cases,
                    limit=limit,
                    embeddings=embeddings,
                    sparse_embeddings=sparse_embeddings,
                    store=store,
                    settings=settings,
                )
            else:
                metrics = await _evaluate_profile_explicit(
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
            if label_mode == "legacy-ambiguous":
                print("MODE            HITRATE      MRR  SRC_RECALL  SRC_NDCG")
                for name, result in results:
                    assert isinstance(result, AggregateMetrics)
                    print(
                        f"{name:<15} "
                        f"{result.hit_rate:>7.3f}  "
                        f"{result.mrr:>7.3f}  "
                        f"{result.source_recall:>10.3f}  "
                        f"{result.source_ndcg:>8.3f}"
                    )
            else:
                print("MODE            PASSRATE      MRR  ACCEPT_HIT  REQ_RECALL  REQ_NDCG")
                for name, result in results:
                    assert isinstance(result, ExplicitAggregateMetrics)
                    print(
                        f"{name:<15} "
                        f"{result.pass_rate:>8.3f}  "
                        f"{result.mrr:>7.3f}  "
                        f"{_format_optional(result.acceptable_hit_rate):>10}  "
                        f"{_format_optional(result.required_recall):>10}  "
                        f"{_format_optional(result.required_ndcg):>8}"
                    )
    finally:
        await qdrant.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args.cases, args.limit, args.mode, args.suite))


if __name__ == "__main__":
    main()
