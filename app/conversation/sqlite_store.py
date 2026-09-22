"""SQLite implementation of the conversation-session persistence protocol."""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.conversation.models import (
    ConversationSession,
    ConversationTurn,
    NewTurn,
    SessionBusyError,
    SessionConflictError,
    SessionExpiredError,
    SessionLease,
    SessionNotFoundError,
    SessionSnapshot,
    StoredSource,
)

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 0,
    lease_token TEXT,
    lease_until TEXT
);

CREATE TABLE IF NOT EXISTS turns (
    turn_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TEXT NOT NULL,
    model TEXT NOT NULL,
    grounded INTEGER NOT NULL,
    citation_ids TEXT NOT NULL,
    citation_retry_count INTEGER NOT NULL,
    multi_query_used INTEGER NOT NULL,
    retrieval_queries TEXT NOT NULL,
    decomposition_status TEXT NOT NULL,
    sources TEXT NOT NULL,
    UNIQUE(session_id, sequence),
    FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_turns_session_sequence ON turns(session_id, sequence);
"""


class SQLiteSessionStore:
    """Persist sessions in a local SQLite file using short-lived connections."""

    def __init__(self, path: Path) -> None:
        self._path = path

    async def initialize(self) -> None:
        """Create the database directory and idempotent schema."""
        await asyncio.to_thread(self._initialize_sync)

    async def close(self) -> None:
        """Close the store lifecycle; connections are already operation-scoped."""
        return None

    async def create(self, *, now: datetime, expires_at: datetime) -> SessionSnapshot:
        """Create and return an empty session."""
        return await asyncio.to_thread(self._create_sync, now, expires_at, uuid4())

    async def get(self, session_id: UUID, *, now: datetime) -> SessionSnapshot:
        """Return a non-expired session snapshot."""
        return await asyncio.to_thread(self._get_sync, session_id, now)

    async def delete(self, session_id: UUID, *, now: datetime) -> None:
        """Delete a non-expired session and its turns atomically."""
        await asyncio.to_thread(self._delete_sync, session_id, now)

    async def acquire(
        self,
        session_id: UUID,
        *,
        now: datetime,
        lease_until: datetime,
    ) -> SessionLease:
        """Acquire an exclusive lease, replacing only an expired lease."""
        return await asyncio.to_thread(
            self._acquire_sync,
            session_id,
            now,
            lease_until,
            uuid4(),
        )

    async def complete(
        self,
        lease: SessionLease,
        turn: NewTurn,
        *,
        now: datetime,
        expires_at: datetime,
        max_turns: int,
    ) -> SessionSnapshot:
        """Commit a completed turn when the lease and revision still match."""
        return await asyncio.to_thread(
            self._complete_sync,
            lease,
            turn,
            now,
            expires_at,
            max_turns,
        )

    async def release(self, lease: SessionLease) -> None:
        """Release the matching lease without disturbing a replacement lease."""
        await asyncio.to_thread(self._release_sync, lease)

    async def purge_expired(self, *, now: datetime, limit: int = 100) -> int:
        """Delete a bounded number of expired sessions without active leases."""
        return await asyncio.to_thread(self._purge_expired_sync, now, limit)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize_sync(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(SCHEMA_V1)
            connection.execute("PRAGMA user_version = 1")

    def _create_sync(
        self,
        now: datetime,
        expires_at: datetime,
        session_id: UUID,
    ) -> SessionSnapshot:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO sessions (
                    session_id, created_at, updated_at, expires_at, revision
                ) VALUES (?, ?, ?, ?, 0)
                """,
                (str(session_id), _dump_datetime(now), _dump_datetime(now), _dump_datetime(expires_at)),
            )
            return self._snapshot(connection, session_id)

    def _get_sync(self, session_id: UUID, now: datetime) -> SessionSnapshot:
        with self._connect() as connection:
            session_row = self._required_session(connection, session_id)
            self._ensure_not_expired(session_row, now)
            return self._snapshot(connection, session_id, session_row=session_row)

    def _delete_sync(self, session_id: UUID, now: datetime) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session_row = self._required_session(connection, session_id)
            self._ensure_not_expired(session_row, now)
            connection.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (str(session_id),),
            )

    def _acquire_sync(
        self,
        session_id: UUID,
        now: datetime,
        lease_until: datetime,
        token: UUID,
    ) -> SessionLease:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session_row = self._required_session(connection, session_id)
            self._ensure_not_expired(session_row, now)
            if session_row["lease_token"] is not None and _load_datetime(
                session_row["lease_until"]
            ) > now:
                raise SessionBusyError
            snapshot = self._snapshot(connection, session_id, session_row=session_row)
            connection.execute(
                """
                UPDATE sessions
                SET lease_token = ?, lease_until = ?
                WHERE session_id = ?
                """,
                (str(token), _dump_datetime(lease_until), str(session_id)),
            )
            return SessionLease(
                session_id=session_id,
                token=token,
                expected_revision=snapshot.session.revision,
                snapshot=snapshot,
            )

    def _complete_sync(
        self,
        lease: SessionLease,
        turn: NewTurn,
        now: datetime,
        expires_at: datetime,
        max_turns: int,
    ) -> SessionSnapshot:
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session_row = self._required_session(connection, lease.session_id)
            if (
                session_row["lease_token"] != str(lease.token)
                or session_row["revision"] != lease.expected_revision
            ):
                raise SessionConflictError
            next_sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM turns WHERE session_id = ?",
                (str(lease.session_id),),
            ).fetchone()[0]
            connection.execute(
                """
                INSERT INTO turns (
                    turn_id, session_id, sequence, question, answer, created_at, model,
                    grounded, citation_ids, citation_retry_count, multi_query_used,
                    retrieval_queries, decomposition_status, sources
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    str(lease.session_id),
                    next_sequence,
                    turn.question,
                    turn.answer,
                    _dump_datetime(now),
                    turn.model,
                    int(turn.grounded),
                    _dump_json(list(turn.citation_ids)),
                    turn.citation_retry_count,
                    int(turn.multi_query_used),
                    _dump_json(list(turn.retrieval_queries)),
                    turn.decomposition_status,
                    _dump_sources(turn.sources),
                ),
            )
            updated = connection.execute(
                """
                UPDATE sessions
                SET updated_at = ?, expires_at = ?, revision = revision + 1,
                    lease_token = NULL, lease_until = NULL
                WHERE session_id = ? AND lease_token = ? AND revision = ?
                """,
                (
                    _dump_datetime(now),
                    _dump_datetime(expires_at),
                    str(lease.session_id),
                    str(lease.token),
                    lease.expected_revision,
                ),
            )
            if updated.rowcount != 1:
                raise SessionConflictError
            oldest_sequence_to_remove = next_sequence - max_turns
            if oldest_sequence_to_remove > 0:
                connection.execute(
                    """
                    DELETE FROM turns
                    WHERE session_id = ? AND sequence <= ?
                    """,
                    (str(lease.session_id), oldest_sequence_to_remove),
                )
            return self._snapshot(connection, lease.session_id)

    def _release_sync(self, lease: SessionLease) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE sessions
                SET lease_token = NULL, lease_until = NULL
                WHERE session_id = ? AND lease_token = ?
                """,
                (str(lease.session_id), str(lease.token)),
            )

    def _purge_expired_sync(self, now: datetime, limit: int) -> int:
        if limit <= 0:
            return 0
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """
                SELECT session_id
                FROM sessions
                WHERE expires_at <= ?
                  AND (
                      lease_token IS NULL OR lease_until IS NULL OR lease_until <= ?
                  )
                ORDER BY expires_at, session_id
                LIMIT ?
                """,
                (_dump_datetime(now), _dump_datetime(now), limit),
            ).fetchall()
            session_ids = [row["session_id"] for row in rows]
            if not session_ids:
                return 0
            placeholders = ",".join("?" for _ in session_ids)
            connection.execute(
                f"DELETE FROM sessions WHERE session_id IN ({placeholders})",  # noqa: S608
                session_ids,
            )
            return len(session_ids)

    @staticmethod
    def _required_session(
        connection: sqlite3.Connection,
        session_id: UUID,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (str(session_id),),
        ).fetchone()
        if row is None:
            raise SessionNotFoundError
        return row

    @staticmethod
    def _ensure_not_expired(session_row: sqlite3.Row, now: datetime) -> None:
        if _load_datetime(session_row["expires_at"]) <= now:
            raise SessionExpiredError

    def _snapshot(
        self,
        connection: sqlite3.Connection,
        session_id: UUID,
        *,
        session_row: sqlite3.Row | None = None,
    ) -> SessionSnapshot:
        row = session_row or self._required_session(connection, session_id)
        turn_rows = connection.execute(
            "SELECT * FROM turns WHERE session_id = ? ORDER BY sequence",
            (str(session_id),),
        ).fetchall()
        return SessionSnapshot(
            session=_session_from_row(row),
            turns=tuple(_turn_from_row(turn_row) for turn_row in turn_rows),
        )


def _dump_datetime(value: datetime) -> str:
    return value.isoformat()


def _load_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _dump_sources(sources: tuple[StoredSource, ...]) -> str:
    return _dump_json(
        [
            {
                "citation_id": source.citation_id,
                "score": source.score,
                "source": source.source,
                "category": source.category,
                "audience": source.audience,
                "page": source.page,
                "chunk_count": source.chunk_count,
                "excerpt": source.excerpt,
            }
            for source in sources
        ]
    )


def _session_from_row(row: sqlite3.Row) -> ConversationSession:
    return ConversationSession(
        session_id=UUID(row["session_id"]),
        created_at=_load_datetime(row["created_at"]),
        updated_at=_load_datetime(row["updated_at"]),
        expires_at=_load_datetime(row["expires_at"]),
        revision=row["revision"],
    )


def _turn_from_row(row: sqlite3.Row) -> ConversationTurn:
    return ConversationTurn(
        turn_id=UUID(row["turn_id"]),
        sequence=row["sequence"],
        question=row["question"],
        answer=row["answer"],
        created_at=_load_datetime(row["created_at"]),
        model=row["model"],
        grounded=bool(row["grounded"]),
        citation_ids=tuple(json.loads(row["citation_ids"])),
        citation_retry_count=row["citation_retry_count"],
        multi_query_used=bool(row["multi_query_used"]),
        retrieval_queries=tuple(json.loads(row["retrieval_queries"])),
        decomposition_status=row["decomposition_status"],
        sources=tuple(StoredSource(**source) for source in json.loads(row["sources"])),
    )
