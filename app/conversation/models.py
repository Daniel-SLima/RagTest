"""Provider-agnostic domain models for persistent conversation sessions."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StoredSource:
    """Small, public-safe source representation stored with a completed turn."""

    citation_id: int
    score: float
    source: str
    category: str | None
    audience: str | None
    page: int | None
    chunk_count: int
    excerpt: str


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    """A completed RAG turn persisted in sequence within one session."""

    turn_id: UUID
    sequence: int
    question: str
    answer: str
    created_at: datetime
    model: str
    grounded: bool
    citation_ids: tuple[int, ...]
    citation_retry_count: int
    multi_query_used: bool
    retrieval_queries: tuple[str, ...]
    decomposition_status: str
    sources: tuple[StoredSource, ...]


@dataclass(frozen=True, slots=True)
class ConversationSession:
    """Session metadata used for retention and optimistic concurrency."""

    session_id: UUID
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    revision: int


@dataclass(frozen=True, slots=True)
class SessionSnapshot:
    """Consistent view of session metadata and completed turns."""

    session: ConversationSession
    turns: tuple[ConversationTurn, ...]


@dataclass(frozen=True, slots=True)
class SessionLease:
    """Opaque processing lease tied to the revision acquired by a caller."""

    session_id: UUID
    token: UUID
    expected_revision: int
    snapshot: SessionSnapshot


@dataclass(frozen=True, slots=True)
class NewTurn:
    """Completed turn payload accepted by a session store."""

    question: str
    answer: str
    model: str
    grounded: bool
    citation_ids: tuple[int, ...]
    citation_retry_count: int
    multi_query_used: bool
    retrieval_queries: tuple[str, ...]
    decomposition_status: str
    sources: tuple[StoredSource, ...]


class SessionNotFoundError(Exception):
    """Raised when a session identifier is unknown."""


class SessionExpiredError(Exception):
    """Raised when a known session has exceeded its retention deadline."""


class SessionBusyError(Exception):
    """Raised when an unexpired lease already protects a session."""


class SessionConflictError(Exception):
    """Raised when a lease no longer matches the current session revision."""
