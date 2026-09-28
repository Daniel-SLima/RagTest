from collections.abc import Sequence
from typing import Any


def _pass_rate(metrics: Any) -> float:
    value = getattr(metrics, "pass_rate", None)
    return float(value if value is not None else metrics.hit_rate)


def check_quality_gate(
    results: Sequence[tuple[str, Any]],
    *,
    min_pass_rate: float | None,
    min_mrr: float | None,
) -> list[str]:
    failures: list[str] = []
    for name, metrics in results:
        pass_rate = _pass_rate(metrics)
        if min_pass_rate is not None and pass_rate < min_pass_rate:
            failures.append(f"{name}: PassRate {pass_rate:.3f} < {min_pass_rate:.3f}")
        if min_mrr is not None and metrics.mrr < min_mrr:
            failures.append(f"{name}: MRR {metrics.mrr:.3f} < {min_mrr:.3f}")
    return failures
