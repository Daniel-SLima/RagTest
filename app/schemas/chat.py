from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    limit: int = Field(default=5, ge=1, le=10)
    category: str | None = Field(default=None, max_length=100)
    audience: str | None = Field(default=None, max_length=100)
    min_score: float | None = Field(default=None, ge=-1.0, le=1.0)


class ChatSource(BaseModel):
    citation_id: int
    score: float
    source: str
    category: str | None = None
    audience: str | None = None
    page: int | None = None
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    model: str
    sources: list[ChatSource]
