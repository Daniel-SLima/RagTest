from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MinScoreSuggestion:
    separable: bool
    threshold: float | None
    min_in_scope: float
    max_out_of_scope: float
    overlap_in_scope: int


def suggest_min_score(*, in_scope: list[float], out_of_scope: list[float]) -> MinScoreSuggestion:
    if not in_scope or not out_of_scope:
        raise ValueError("in_scope and out_of_scope must not be empty")
    lowest_in = min(in_scope)
    highest_out = max(out_of_scope)
    separable = highest_out < lowest_in
    return MinScoreSuggestion(
        separable=separable,
        threshold=round((lowest_in + highest_out) / 2, 4) if separable else None,
        min_in_scope=lowest_in,
        max_out_of_scope=highest_out,
        overlap_in_scope=sum(1 for score in in_scope if score <= highest_out),
    )
