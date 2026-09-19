from typing import Any

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)
    category: str | None = Field(default=None, max_length=100)


class SemanticSearchHit(BaseModel):
    score: float
    content: str
    source: str
    category: str | None = None
    page: int | None = None
    metadata: dict[str, Any]


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchHit]
