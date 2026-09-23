from __future__ import annotations

from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True, slots=True)
class DiagnosticsTimings:
    retrieval_ms: float
    generation_ms: float
    total_ms: float

    def as_dict(self) -> dict[str, float]:
        return {
            "retrieval_ms": self.retrieval_ms,
            "generation_ms": self.generation_ms,
            "total_ms": self.total_ms,
        }


class DiagnosticsCollector:
    """Opt-in monotonic timing collector for the demo pipeline."""

    def __init__(self) -> None:
        self._started_at: float | None = None
        self._retrieval_at: float | None = None
        self._generation_at: float | None = None
        self._finished_at: float | None = None
        self._timings: dict[str, float] | None = None

    def start(self) -> None:
        self._started_at = monotonic()

    def mark_retrieval(self) -> None:
        self._retrieval_at = monotonic()

    def mark_generation(self) -> None:
        self._generation_at = monotonic()

    def finish(self) -> dict[str, float]:
        if self._timings is not None:
            return dict(self._timings)
        self._finished_at = monotonic()
        started = self._started_at or self._finished_at
        retrieval = self._retrieval_at or self._finished_at
        generation = self._generation_at or self._finished_at
        self._timings = DiagnosticsTimings(
            retrieval_ms=max(0.0, (retrieval - started) * 1000),
            generation_ms=max(0.0, (self._finished_at - generation) * 1000),
            total_ms=max(0.0, (self._finished_at - started) * 1000),
        ).as_dict()
        return dict(self._timings)
