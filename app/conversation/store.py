"""Persistence protocol for conversation sessions."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.conversation.models import NewTurn, SessionLease, SessionSnapshot


class SessionStore(Protocol):
    """Async boundary implemented by durable conversation stores."""

    async def initialize(self) -> None: ...

    async def close(self) -> None: ...

    async def create(self, *, now: datetime, expires_at: datetime) -> SessionSnapshot: ...

    async def get(self, session_id: UUID, *, now: datetime) -> SessionSnapshot: ...

    async def delete(self, session_id: UUID, *, now: datetime) -> None: ...

    async def acquire(
        self,
        session_id: UUID,
        *,
        now: datetime,
        lease_until: datetime,
    ) -> SessionLease: ...

    async def complete(
        self,
        lease: SessionLease,
        turn: NewTurn,
        *,
        now: datetime,
        expires_at: datetime,
        max_turns: int,
    ) -> SessionSnapshot: ...

    async def release(self, lease: SessionLease) -> None: ...

    async def purge_expired(self, *, now: datetime, limit: int = 100) -> int: ...
