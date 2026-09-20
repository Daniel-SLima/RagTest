import pytest

from app.rag.retrieval_profiles import PROFILES, get_profile, selected_profiles


def test_all_profiles_are_returned_in_experimental_order() -> None:
    profiles = selected_profiles("all")

    assert [profile.name for profile in profiles] == [
        "dense",
        "dense-rerank",
        "hybrid",
    ]


def test_dense_profile_does_not_use_sparse_retrieval() -> None:
    assert PROFILES["dense"].use_sparse is False
    assert PROFILES["dense"].source_lexical_weight == 0.0


def test_dense_rerank_matches_selected_runtime_candidate() -> None:
    profile = get_profile("dense-rerank")

    assert profile.use_sparse is False
    assert profile.candidate_multiplier == 8
    assert profile.score_margin == 0.22
    assert profile.source_lexical_weight == 0.25
    assert profile.content_lexical_weight == 0.05


def test_hybrid_uses_sparse_and_no_legacy_score_margin() -> None:
    assert PROFILES["hybrid"].use_sparse is True
    assert PROFILES["hybrid"].score_margin == 0.0
    assert PROFILES["hybrid"].dense_weight == 1.0
    assert PROFILES["hybrid"].sparse_weight == 1.0


def test_unknown_profile_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported retrieval mode"):
        get_profile("unknown")
