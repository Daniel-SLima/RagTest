from app.rag.grounding import validate_citation_coverage


def main() -> None:
    cases = [
        (
            "all informative blocks cited",
            "A vacina é anual [1].\nA fonte também descreve o público-alvo [2].",
            2,
            True,
            1.0,
        ),
        (
            "uncited block detected",
            "A vacina é anual [1].\nOutra afirmação aparece sem referência.",
            1,
            False,
            0.5,
        ),
        (
            "heading is not treated as a claim",
            "Orientações principais:\n- A recomendação consta no documento [1].",
            1,
            True,
            1.0,
        ),
        (
            "out-of-range citation still fails syntax",
            "A recomendação consta no documento [9].",
            1,
            False,
            0.0,
        ),
    ]

    print("RagTest citation coverage self-check")
    failed = 0

    for name, answer, source_count, expected_valid, expected_coverage in cases:
        result = validate_citation_coverage(answer, source_count)
        passed = (
            result.valid is expected_valid
            and result.coverage == expected_coverage
        )
        print(
            f"[{'PASS' if passed else 'FAIL'}] {name} "
            f"| coverage={result.coverage:.3f} "
            f"| blocks={result.cited_claim_blocks}/{result.total_claim_blocks}"
        )
        if not passed:
            failed += 1

    if failed:
        raise SystemExit(f"{failed} citation coverage self-check(s) failed")

    print("All citation coverage self-checks passed.")
    print(
        "This check validates citation coverage structure only; "
        "it does not prove semantic entailment."
    )


if __name__ == "__main__":
    main()
