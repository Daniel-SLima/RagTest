from dataclasses import dataclass
from typing import Any, Literal

LabelMode = Literal["legacy-ambiguous", "explicit"]


@dataclass(frozen=True, slots=True)
class SourceJudgments:
    mode: LabelMode
    legacy_expected_sources: tuple[str, ...] = ()
    acceptable_sources: tuple[str, ...] = ()
    required_sources: tuple[str, ...] = ()

    @property
    def has_explicit_semantics(self) -> bool:
        return self.mode == "explicit"


def _string_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of source strings")
    items = tuple(str(item).strip() for item in value if str(item).strip())
    if len(items) != len(value):
        raise ValueError(f"{field} cannot contain blank source values")
    if len(set(items)) != len(items):
        raise ValueError(f"{field} cannot contain duplicate source values")
    return items


def parse_source_judgments(case: dict[str, Any]) -> SourceJudgments:
    legacy = _string_tuple(case.get("expected_sources"), field="expected_sources")
    acceptable = _string_tuple(
        case.get("acceptable_sources"),
        field="acceptable_sources",
    )
    required = _string_tuple(case.get("required_sources"), field="required_sources")

    if legacy and (acceptable or required):
        raise ValueError(
            "A case cannot mix legacy expected_sources with explicit "
            "acceptable_sources/required_sources."
        )

    if legacy:
        return SourceJudgments(
            mode="legacy-ambiguous",
            legacy_expected_sources=legacy,
        )

    if not acceptable and not required:
        raise ValueError(
            "A case must define expected_sources (legacy) or at least one "
            "explicit source judgment."
        )

    return SourceJudgments(
        mode="explicit",
        acceptable_sources=acceptable,
        required_sources=required,
    )


def source_label_summary(cases: list[dict[str, Any]]) -> dict[str, int]:
    legacy_cases = 0
    explicit_cases = 0
    legacy_multi_source_cases = 0
    explicit_with_acceptable = 0
    explicit_with_required = 0

    for case in cases:
        judgments = parse_source_judgments(case)
        if judgments.mode == "legacy-ambiguous":
            legacy_cases += 1
            if len(judgments.legacy_expected_sources) > 1:
                legacy_multi_source_cases += 1
            continue

        explicit_cases += 1
        if judgments.acceptable_sources:
            explicit_with_acceptable += 1
        if judgments.required_sources:
            explicit_with_required += 1

    return {
        "total_cases": len(cases),
        "legacy_cases": legacy_cases,
        "legacy_multi_source_cases": legacy_multi_source_cases,
        "explicit_cases": explicit_cases,
        "explicit_with_acceptable": explicit_with_acceptable,
        "explicit_with_required": explicit_with_required,
    }
