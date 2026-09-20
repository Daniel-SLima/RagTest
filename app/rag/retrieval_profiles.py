from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievalProfile:
    name: str
    use_sparse: bool
    candidate_multiplier: int
    score_margin: float
    source_lexical_weight: float
    content_lexical_weight: float
    dense_weight: float = 1.0
    sparse_weight: float = 1.0


PROFILES: dict[str, RetrievalProfile] = {
    "dense": RetrievalProfile(
        name="dense",
        use_sparse=False,
        candidate_multiplier=4,
        score_margin=0.22,
        source_lexical_weight=0.0,
        content_lexical_weight=0.0,
    ),
    "dense-rerank": RetrievalProfile(
        name="dense-rerank",
        use_sparse=False,
        candidate_multiplier=8,
        score_margin=0.22,
        source_lexical_weight=0.25,
        content_lexical_weight=0.05,
    ),
    "hybrid": RetrievalProfile(
        name="hybrid",
        use_sparse=True,
        candidate_multiplier=8,
        score_margin=0.0,
        source_lexical_weight=0.25,
        content_lexical_weight=0.05,
        dense_weight=1.0,
        sparse_weight=1.0,
    ),
}


def get_profile(name: str) -> RetrievalProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        supported = ", ".join(PROFILES)
        raise ValueError(
            f"Unsupported retrieval mode: {name}. Supported modes: {supported}"
        ) from exc


def selected_profiles(mode: str) -> list[RetrievalProfile]:
    if mode == "all":
        return [PROFILES["dense"], PROFILES["dense-rerank"], PROFILES["hybrid"]]
    return [get_profile(mode)]
