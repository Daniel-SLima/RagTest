from app.evaluation.labels import evaluation_label_mode
from app.evaluation.metrics import evaluate_explicit_case_sources


def main() -> None:
    alternative_case = {
        "acceptable_sources": ["calendar.pdf", "guide.pdf"],
    }
    required_case = {
        "required_sources": ["rights.pdf", "duties.pdf"],
    }
    combined_case = {
        "acceptable_sources": ["overview.pdf"],
        "required_sources": ["primary.pdf"],
    }

    checks = []

    alternative = evaluate_explicit_case_sources(
        ["guide.pdf"],
        alternative_case["acceptable_sources"],
        [],
        5,
    )
    checks.append(
        ("OR alternative passes with one acceptable source", alternative.passed)
    )
    checks.append(
        (
            "OR alternative does not require every acceptable source",
            alternative.acceptable_hit is True,
        )
    )

    required_partial = evaluate_explicit_case_sources(
        ["rights.pdf"],
        [],
        required_case["required_sources"],
        5,
    )
    checks.append(
        (
            "AND required fails with incomplete coverage",
            required_partial.passed is False,
        )
    )
    checks.append(
        (
            "AND required exposes partial recall",
            required_partial.required_recall == 0.5,
        )
    )

    required_complete = evaluate_explicit_case_sources(
        ["duties.pdf", "rights.pdf"],
        [],
        required_case["required_sources"],
        5,
    )
    checks.append(
        (
            "AND required passes with complete coverage",
            required_complete.passed is True,
        )
    )

    combined = evaluate_explicit_case_sources(
        ["overview.pdf", "primary.pdf"],
        combined_case["acceptable_sources"],
        combined_case["required_sources"],
        5,
    )
    checks.append(
        (
            "combined case requires acceptable and required conditions",
            combined.passed is True,
        )
    )

    checks.append(
        (
            "explicit dataset mode is detected",
            evaluation_label_mode([alternative_case, required_case]) == "explicit",
        )
    )

    print("RagTest evaluation v2 semantics self-check")
    failed = 0
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        if not passed:
            failed += 1

    if failed:
        raise SystemExit(f"{failed} evaluation v2 self-check(s) failed")

    print("All evaluation v2 semantics self-checks passed.")


if __name__ == "__main__":
    main()
