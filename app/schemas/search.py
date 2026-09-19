from typing import Any

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)
    category: str | None = Field(default=None, max_length=100)
    audience: str | None = Field(default=None, max_length=100)
    min_score: float | None = Field(default=None, ge=-1.0, le=1.0)


class SemanticSearchHit(BaseModel):
    score: float
    content: str
    source: str
    category: str | None = None
    audience: str | None = None
    page: int | None = None
    chunk_count: int = 1
    metadata: dict[str, Any]


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchHit]
