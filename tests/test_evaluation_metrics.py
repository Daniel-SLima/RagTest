import pytest

from app.evaluation.metrics import (
    evaluate_case_sources,
    evaluate_explicit_case_sources,
    first_expected_rank,
    source_ndcg_at_k,
    source_recall_at_k,
)


def test_first_expected_rank_preserves_legacy_page_level_semantics() -> None:
    assert first_expected_rank(["other", "expected"], ["expected"]) == 2


def test_source_recall_counts_each_expected_source_once() -> None:
    sources = ["a.pdf", "a.pdf", "b.pdf", "other.pdf"]

    assert source_recall_at_k(sources, ["a.pdf", "b.pdf"], 4) == 1.0


def test_source_recall_penalizes_missing_expected_sources() -> None:
    sources = ["a.pdf", "a.pdf", "other.pdf"]

    assert source_recall_at_k(sources, ["a.pdf", "b.pdf"], 3) == 0.5


def test_source_ndcg_is_one_for_ideal_unique_source_ranking() -> None:
    assert source_ndcg_at_k(["a.pdf", "b.pdf"], ["a.pdf", "b.pdf"], 2) == 1.0


def test_source_ndcg_penalizes_duplicate_pages_before_second_relevant_source() -> None:
    ndcg = source_ndcg_at_k(
        ["a.pdf", "a.pdf", "b.pdf"],
        ["a.pdf", "b.pdf"],
        3,
    )

    assert ndcg == pytest.approx(0.9197207891)


def test_case_metrics_keep_legacy_and_source_metrics_together() -> None:
    metrics = evaluate_case_sources(
        ["other.pdf", "expected.pdf", "expected.pdf"],
        ["expected.pdf"],
        3,
    )

    assert metrics.hit is True
    assert metrics.reciprocal_rank == 0.5
    assert metrics.source_recall == 1.0
    assert metrics.source_ndcg == pytest.approx(1 / 1.5849625007)
    assert metrics.unique_sources == 2



def test_explicit_acceptable_sources_use_or_semantics() -> None:
    metrics = evaluate_explicit_case_sources(
        ["b.pdf"],
        ["a.pdf", "b.pdf"],
        [],
        5,
    )

    assert metrics.passed is True
    assert metrics.acceptable_hit is True
    assert metrics.required_recall is None


def test_explicit_required_sources_use_and_coverage_semantics() -> None:
    partial = evaluate_explicit_case_sources(
        ["a.pdf"],
        [],
        ["a.pdf", "b.pdf"],
        5,
    )
    complete = evaluate_explicit_case_sources(
        ["a.pdf", "b.pdf"],
        [],
        ["a.pdf", "b.pdf"],
        5,
    )

    assert partial.passed is False
    assert partial.required_recall == 0.5
    assert complete.passed is True
    assert complete.required_recall == 1.0


def test_explicit_combined_case_requires_both_conditions() -> None:
    missing_required = evaluate_explicit_case_sources(
        ["overview.pdf"],
        ["overview.pdf"],
        ["primary.pdf"],
        5,
    )

    assert missing_required.acceptable_hit is True
    assert missing_required.required_recall == 0.0
    assert missing_required.passed is False
