from types import SimpleNamespace

from app.evaluation.gate import check_quality_gate


def _metrics(pass_rate: float, mrr: float) -> SimpleNamespace:
    return SimpleNamespace(pass_rate=pass_rate, mrr=mrr)


def test_gate_passes_when_all_modes_meet_minimums() -> None:
    assert check_quality_gate([("hybrid", _metrics(0.96, 0.86))], min_pass_rate=0.9, min_mrr=0.8) == []


def test_gate_reports_each_violation() -> None:
    failures = check_quality_gate(
        [("hybrid", _metrics(0.85, 0.70))], min_pass_rate=0.9, min_mrr=0.8
    )

    assert failures == [
        "hybrid: PassRate 0.850 < 0.900",
        "hybrid: MRR 0.700 < 0.800",
    ]


def test_gate_supports_legacy_hit_rate_and_optional_thresholds() -> None:
    legacy = SimpleNamespace(hit_rate=0.5, mrr=0.4)

    assert check_quality_gate([("dense", legacy)], min_pass_rate=0.6, min_mrr=None) == [
        "dense: PassRate 0.500 < 0.600"
    ]
    assert check_quality_gate([("dense", legacy)], min_pass_rate=None, min_mrr=None) == []
