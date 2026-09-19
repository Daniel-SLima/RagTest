from app.cli.evaluate_retrieval import _load_cases
from app.evaluation import DEFAULT_RETRIEVAL_CASES


def test_packaged_retrieval_cases_are_available_without_external_file() -> None:
    cases = _load_cases(None)

    assert cases == DEFAULT_RETRIEVAL_CASES
    assert len(cases) >= 1
    assert all("query" in case for case in cases)
    assert all("expected_sources" in case for case in cases)
