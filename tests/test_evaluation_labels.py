import pytest

from app.evaluation.labels import parse_source_judgments, source_label_summary


def test_legacy_expected_sources_remain_explicitly_ambiguous() -> None:
    judgments = parse_source_judgments(
        {"expected_sources": ["a.pdf", "b.pdf"]}
    )

    assert judgments.mode == "legacy-ambiguous"
    assert judgments.legacy_expected_sources == ("a.pdf", "b.pdf")
    assert judgments.has_explicit_semantics is False


def test_explicit_acceptable_sources_mean_alternative_sources() -> None:
    judgments = parse_source_judgments(
        {"acceptable_sources": ["a.pdf", "b.pdf"]}
    )

    assert judgments.mode == "explicit"
    assert judgments.acceptable_sources == ("a.pdf", "b.pdf")
    assert judgments.required_sources == ()


def test_explicit_required_sources_are_separate_from_acceptable() -> None:
    judgments = parse_source_judgments(
        {
            "acceptable_sources": ["overview.pdf"],
            "required_sources": ["primary.pdf", "secondary.pdf"],
        }
    )

    assert judgments.acceptable_sources == ("overview.pdf",)
    assert judgments.required_sources == ("primary.pdf", "secondary.pdf")


def test_source_judgments_reject_mixed_legacy_and_explicit_schema() -> None:
    with pytest.raises(ValueError, match="cannot mix"):
        parse_source_judgments(
            {
                "expected_sources": ["legacy.pdf"],
                "acceptable_sources": ["new.pdf"],
            }
        )


def test_source_judgments_reject_empty_case() -> None:
    with pytest.raises(ValueError, match="must define"):
        parse_source_judgments({})


def test_source_label_summary_counts_legacy_multi_source_cases() -> None:
    summary = source_label_summary(
        [
            {"expected_sources": ["a.pdf"]},
            {"expected_sources": ["a.pdf", "b.pdf"]},
            {"acceptable_sources": ["c.pdf", "d.pdf"]},
            {"required_sources": ["e.pdf", "f.pdf"]},
        ]
    )

    assert summary == {
        "total_cases": 4,
        "legacy_cases": 2,
        "legacy_multi_source_cases": 1,
        "explicit_cases": 2,
        "explicit_with_acceptable": 1,
        "explicit_with_required": 1,
    }
