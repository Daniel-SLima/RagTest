import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.evaluation import DEFAULT_RETRIEVAL_CASES
from app.rag.embeddings.factory import create_embedding_provider
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RagTest retrieval quality.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=None,
        help=(
            "Optional external JSON file with evaluation cases. "
            "If omitted, uses the cases packaged with RagTest."
        ),
    )
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


def _load_cases(cases_path: Path | None) -> list[dict[str, Any]]:
    if cases_path is None:
        return [dict(case) for case in DEFAULT_RETRIEVAL_CASES]

    return json.loads(cases_path.read_text(encoding="utf-8"))


def _first_expected_rank(sources: list[str], expected_sources: list[str]) -> int | None:
    expected = set(expected_sources)
    for rank, source in enumerate(sources, start=1):
        if source in expected:
            return rank
    return None


async def run(cases_path: Path | None, limit: int) -> None:
    cases = _load_cases(cases_path)
    settings = get_settings()
    qdrant = QdrantService(settings)
    embeddings = create_embedding_provider(settings)
    store = QdrantVectorStore(qdrant.client, settings.qdrant_collection)

    hits_count = 0
    reciprocal_rank_sum = 0.0

    try:
        print("RagTest retrieval evaluation")
        print(
            f"Cases: {len(cases)} | k={limit} | "
            f"source={'external JSON' if cases_path else 'packaged defaults'}"
        )
        print()

        for index, case in enumerate(cases, start=1):
            query = str(case["query"])
            expected_sources = [str(item) for item in case["expected_sources"]]

            hits = await semantic_search(
                query,
                embeddings=embeddings,
                vector_store=store,
                limit=limit,
                category=(
                    str(case["category"])
                    if case.get("category") is not None
                    else None
                ),
                audience=(
                    str(case["audience"])
                    if case.get("audience") is not None
                    else None
                ),
                candidate_multiplier=settings.retrieval_candidate_multiplier,
                score_margin=settings.retrieval_score_margin,
                merge_same_page=settings.retrieval_merge_same_page,
                max_group_chars=settings.retrieval_max_group_chars,
            )

            sources = [hit.source for hit in hits]
            rank = _first_expected_rank(sources, expected_sources)
            passed = rank is not None

            if passed:
                hits_count += 1
                reciprocal_rank_sum += 1.0 / rank

            print(
                f"[{'PASS' if passed else 'FAIL'}] {index}. {query} "
                f"| first_expected_rank={rank or '-'}"
            )
            for result_rank, hit in enumerate(hits, start=1):
                page = f":{hit.page}" if hit.page is not None else ""
                print(
                    f"    {result_rank}. {hit.source}{page} "
                    f"score={hit.score:.4f}"
                )

        total = len(cases)
        hit_rate = hits_count / total if total else 0.0
        mrr = reciprocal_rank_sum / total if total else 0.0

        print()
        print(f"HitRate@{limit}: {hit_rate:.3f} ({hits_count}/{total})")
        print(f"MRR@{limit}: {mrr:.3f}")
    finally:
        await qdrant.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args.cases, args.limit))


if __name__ == "__main__":
    main()
