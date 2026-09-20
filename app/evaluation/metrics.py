from dataclasses import dataclass
from math import log2


@dataclass(frozen=True, slots=True)
class CaseMetrics:
    hit: bool
    reciprocal_rank: float
    source_recall: float
    source_ndcg: float
    unique_sources: int


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def first_expected_rank(
    sources: list[str],
    expected_sources: list[str],
) -> int | None:
    expected = set(expected_sources)
    for rank, source in enumerate(sources, start=1):
        if source in expected:
            return rank
    return None


def source_recall_at_k(
    sources: list[str],
    expected_sources: list[str],
    k: int,
) -> float:
    expected = set(expected_sources)
    if not expected:
        return 0.0

    retrieved = set(_dedupe_preserving_order(sources[:k]))
    return len(expected & retrieved) / len(expected)


def source_ndcg_at_k(
    sources: list[str],
    expected_sources: list[str],
    k: int,
) -> float:
    expected = set(expected_sources)
    if not expected or k <= 0:
        return 0.0

    seen: set[str] = set()
    dcg = 0.0
    for rank, source in enumerate(sources[:k], start=1):
        relevant = source in expected and source not in seen
        seen.add(source)
        if relevant:
            dcg += 1.0 / log2(rank + 1)

    ideal_relevant = min(len(expected), k)
    idcg = sum(1.0 / log2(rank + 1) for rank in range(1, ideal_relevant + 1))
    return dcg / idcg if idcg else 0.0


def evaluate_case_sources(
    sources: list[str],
    expected_sources: list[str],
    k: int,
) -> CaseMetrics:
    rank = first_expected_rank(sources, expected_sources)
    return CaseMetrics(
        hit=rank is not None,
        reciprocal_rank=(1.0 / rank) if rank is not None else 0.0,
        source_recall=source_recall_at_k(sources, expected_sources, k),
        source_ndcg=source_ndcg_at_k(sources, expected_sources, k),
        unique_sources=len(set(sources[:k])),
    )
