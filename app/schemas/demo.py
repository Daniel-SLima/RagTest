from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DemoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DemoScore(DemoModel):
    dense_score: float | None = None
    sparse_score: float | None = None
    rank_score: float | None = None
    fusion_score: float | None = None


class DemoSource(DemoModel):
    public_id: str
    document: str
    page: int | None = None
    order: int = Field(ge=1)
    excerpt: str
    scores: DemoScore


class DemoTimings(DemoModel):
    retrieval_ms: float = Field(ge=0)
    generation_ms: float | None = Field(default=None, ge=0)
    total_ms: float = Field(ge=0)


DemoRetrievalMode = Literal["dense", "dense-rerank", "hybrid"]


class DemoRetrievalRequest(DemoModel):
    query: str = Field(min_length=2, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    category: str | None = Field(default=None, max_length=100)
    audience: str | None = Field(default=None, max_length=100)
    min_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    retrieval_mode: DemoRetrievalMode | None = None


class DemoRunRequest(DemoRetrievalRequest):
    pass


class DemoRetrievalResponse(DemoModel):
    query: str
    retrieval_mode: DemoRetrievalMode
    sources: list[DemoSource]
    timings: DemoTimings | None = None


class DemoRunResponse(DemoModel):
    answer: str
    model: str
    grounded: bool
    citation_ids: list[int]
    sources: list[DemoSource]
    timings: DemoTimings


class DemoRuntimeResponse(DemoModel):
    version: str
    provider: str
    model: str
    embedding: str
    retrieval: DemoRetrievalMode
    collection: str
    demo_enabled: bool
    policy_id: str
    policy_status: Literal["configured", "blocked"]
