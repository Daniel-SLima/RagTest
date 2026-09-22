"""Public response models for conversation-session endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.chat import ChatSource


class SessionTurnResponse(BaseModel):
    turn_id: UUID
    sequence: int
    question: str
    answer: str
    created_at: datetime
    model: str
    grounded: bool
    citation_ids: list[int]
    citation_retry_count: int
    multi_query_used: bool
    retrieval_queries: list[str]
    decomposition_status: str
    sources: list[ChatSource]


class SessionResponse(BaseModel):
    session_id: UUID
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    status: Literal["active"] = "active"
    turns: list[SessionTurnResponse]
