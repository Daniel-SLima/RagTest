from app.evaluation import (
    DEV_RETRIEVAL_CASES,
    EVALUATION_DATASET_VERSION,
    HOLDOUT_RETRIEVAL_CASES,
    select_retrieval_cases,
    source_label_summary,
)


def test_evaluation_suites_have_stable_sizes() -> None:
    assert len(DEV_RETRIEVAL_CASES) == 7
    assert len(HOLDOUT_RETRIEVAL_CASES) == 15
    assert len(select_retrieval_cases("all")) == 22


def test_dev_and_holdout_queries_are_disjoint() -> None:
    dev_queries = {str(case["query"]) for case in DEV_RETRIEVAL_CASES}
    holdout_queries = {str(case["query"]) for case in HOLDOUT_RETRIEVAL_CASES}

    assert dev_queries.isdisjoint(holdout_queries)


def test_every_case_has_id_query_and_expected_sources() -> None:
    for case in select_retrieval_cases("all"):
        assert case["id"]
        assert case["query"]
        assert case["expected_sources"]


def test_dataset_version_is_frozen_identifier() -> None:
    assert EVALUATION_DATASET_VERSION == "2026-09-20-v1"



def test_frozen_v1_label_audit_is_stable() -> None:
    summary = source_label_summary(select_retrieval_cases("all"))

    assert summary["total_cases"] == 22
    assert summary["legacy_cases"] == 22
    assert summary["legacy_multi_source_cases"] == 5
    assert summary["explicit_cases"] == 0
