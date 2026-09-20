from app.evaluation.retrieval_profiles import PROFILES, selected_profiles


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


def test_hybrid_profile_uses_sparse_and_no_legacy_score_margin() -> None:
    assert PROFILES["hybrid"].use_sparse is True
    assert PROFILES["hybrid"].score_margin == 0.0
