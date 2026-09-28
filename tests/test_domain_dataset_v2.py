import json
from pathlib import Path

from app.evaluation.labels import parse_source_judgments

DATASETS = Path("app/evaluation/datasets")
SOURCE_DIR = Path("data/source")


def _load(name: str) -> list[dict[str, object]]:
    return json.loads((DATASETS / name).read_text(encoding="utf-8"))


def test_domain_v2_split_sizes() -> None:
    assert len(_load("dominio-v2-dev.json")) == 15
    assert len(_load("dominio-v2-holdout.json")) == 25
    assert len(_load("dominio-v2-fora-escopo.json")) >= 3


def test_domain_v2_ids_and_queries_are_unique_across_splits() -> None:
    cases = _load("dominio-v2-dev.json") + _load("dominio-v2-holdout.json")
    ids = [case["id"] for case in cases]
    queries = [str(case["query"]).lower() for case in cases]

    assert len(ids) == len(set(ids))
    assert len(queries) == len(set(queries))


def test_domain_v2_uses_explicit_labels_pointing_to_existing_sources() -> None:
    for case in _load("dominio-v2-dev.json") + _load("dominio-v2-holdout.json"):
        judgments = parse_source_judgments(case)
        assert judgments.has_explicit_semantics, case["id"]
        for source in (*judgments.acceptable_sources, *judgments.required_sources):
            assert (SOURCE_DIR / source).is_file(), f"{case['id']}: {source}"


def test_domain_v2_covers_core_topics() -> None:
    topics = {
        case["topic"]
        for case in _load("dominio-v2-dev.json") + _load("dominio-v2-holdout.json")
    }

    assert {"rastreamento", "agendamento", "gestacao", "urgencia"} <= topics


def test_out_of_scope_cases_have_no_sources() -> None:
    for case in _load("dominio-v2-fora-escopo.json"):
        assert "acceptable_sources" not in case
        assert "required_sources" not in case
        assert case["expected_behavior"] == "recusar"


def test_packaged_datasets_load_by_name() -> None:
    from app.cli.evaluate_retrieval import _load_cases

    cases, label = _load_cases(None, "dev", "dominio-v2-holdout")

    assert len(cases) == 25
    assert label == "packaged dataset dominio-v2-holdout"


def test_blank_min_score_env_is_none(monkeypatch) -> None:
    from app.core.config import Settings

    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "")

    assert Settings(_env_file=None).retrieval_min_score is None


def test_holdout_v3_is_fresh_and_valid() -> None:
    v3 = _load("dominio-v3-holdout.json")
    previous = _load("dominio-v2-dev.json") + _load("dominio-v2-holdout.json")

    assert len(v3) == 25
    assert {case["query"].lower() for case in v3}.isdisjoint(
        {case["query"].lower() for case in previous}
    )
    for case in v3:
        judgments = parse_source_judgments(case)
        for source in judgments.acceptable_sources:
            assert (SOURCE_DIR / source).is_file(), f"{case['id']}: {source}"
