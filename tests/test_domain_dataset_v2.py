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
