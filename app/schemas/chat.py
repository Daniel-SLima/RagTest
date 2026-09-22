from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: UUID | None = None
    message: str = Field(min_length=2, max_length=4000)
    limit: int = Field(default=5, ge=1, le=10)
    category: str | None = Field(default=None, max_length=100)
    audience: str | None = Field(default=None, max_length=100)
    min_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    auto_decompose: bool | None = None


class ChatSource(BaseModel):
    citation_id: int
    score: float
    source: str
    category: str | None = None
    audience: str | None = None
    page: int | None = None
    chunk_count: int = 1
    excerpt: str


class ChatResponse(BaseModel):
    session_id: UUID | None = None
    answer: str
    model: str
    grounded: bool
    citation_ids: list[int]
    citation_retry_count: int
    multi_query_used: bool
    retrieval_queries: list[str]
    decomposition_status: str
    sources: list[ChatSource]
