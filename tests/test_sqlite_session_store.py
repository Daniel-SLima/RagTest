import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from app.conversation.models import (
    NewTurn,
    SessionBusyError,
    SessionConflictError,
    SessionExpiredError,
    SessionLease,
    SessionNotFoundError,
    StoredSource,
)
from app.conversation.sqlite_store import SQLiteSessionStore


def sample_turn(question: str, answer: str) -> NewTurn:
    return NewTurn(
        question=question,
        answer=answer,
        model="fake-model",
        grounded=True,
        citation_ids=(1,),
        citation_retry_count=0,
        multi_query_used=False,
        retrieval_queries=(question,),
        decomposition_status="not-needed",
        sources=(
            StoredSource(1, 0.9, "guia.pdf", "saude", "mulher", 2, 1, "Trecho"),
        ),
    )


async def store_with_lease(
    tmp_path: Path,
) -> tuple[SQLiteSessionStore, SessionLease, datetime]:
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    await store.initialize()
    now = datetime(2026, 9, 22, tzinfo=UTC)
    created = await store.create(now=now, expires_at=now + timedelta(days=7))
    lease = await store.acquire(
        created.session.session_id,
        now=now,
        lease_until=now + timedelta(minutes=10),
    )
    return store, lease, now


@pytest.mark.asyncio
async def test_sqlite_store_persists_completed_turn_after_reopen(tmp_path: Path) -> None:
    path = tmp_path / "sessions.sqlite3"
    now = datetime(2026, 9, 22, tzinfo=UTC)
    store = SQLiteSessionStore(path)
    await store.initialize()
    created = await store.create(now=now, expires_at=now + timedelta(days=7))
    lease = await store.acquire(
        created.session.session_id,
        now=now,
        lease_until=now + timedelta(minutes=10),
    )
    await store.complete(
        lease,
        sample_turn("Pergunta", "Resposta"),
        now=now,
        expires_at=now + timedelta(days=7),
        max_turns=20,
    )
    await store.close()

    reopened = SQLiteSessionStore(path)
    await reopened.initialize()
    snapshot = await reopened.get(created.session.session_id, now=now)

    assert [(turn.sequence, turn.question) for turn in snapshot.turns] == [(1, "Pergunta")]
    assert snapshot.session.revision == 1
    assert snapshot.turns[0].sources[0].excerpt == "Trecho"


@pytest.mark.asyncio
async def test_get_distinguishes_missing_and_expired(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    await store.initialize()
    now = datetime(2026, 9, 22, tzinfo=UTC)

    with pytest.raises(SessionNotFoundError):
        await store.get(uuid4(), now=now)

    created = await store.create(now=now, expires_at=now + timedelta(seconds=1))
    with pytest.raises(SessionExpiredError):
        await store.get(created.session.session_id, now=now + timedelta(seconds=2))


@pytest.mark.asyncio
async def test_active_lease_blocks_second_writer_but_expired_lease_recovers(
    tmp_path: Path,
) -> None:
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    await store.initialize()
    now = datetime(2026, 9, 22, tzinfo=UTC)
    created = await store.create(now=now, expires_at=now + timedelta(days=7))
    first = await store.acquire(
        created.session.session_id,
        now=now,
        lease_until=now + timedelta(seconds=30),
    )

    with pytest.raises(SessionBusyError):
        await store.acquire(
            created.session.session_id,
            now=now + timedelta(seconds=1),
            lease_until=now + timedelta(seconds=31),
        )

    recovered = await store.acquire(
        created.session.session_id,
        now=now + timedelta(seconds=31),
        lease_until=now + timedelta(seconds=61),
    )
    assert recovered.token != first.token


@pytest.mark.asyncio
async def test_complete_rejects_wrong_token_and_revision(tmp_path: Path) -> None:
    store, lease, now = await store_with_lease(tmp_path)
    wrong = replace(lease, token=uuid4())

    with pytest.raises(SessionConflictError):
        await store.complete(
            wrong,
            sample_turn("P", "R"),
            now=now,
            expires_at=now + timedelta(days=7),
            max_turns=20,
        )

    stale = replace(lease, expected_revision=lease.expected_revision + 1)
    with pytest.raises(SessionConflictError):
        await store.complete(
            stale,
            sample_turn("P", "R"),
            now=now,
            expires_at=now + timedelta(days=7),
            max_turns=20,
        )


@pytest.mark.asyncio
async def test_delete_cascades_completed_turns(tmp_path: Path) -> None:
    path = tmp_path / "sessions.sqlite3"
    store, lease, now = await store_with_lease(tmp_path)
    await store.complete(
        lease,
        sample_turn("P", "R"),
        now=now,
        expires_at=now + timedelta(days=7),
        max_turns=20,
    )

    await store.delete(lease.session_id, now=now)

    with pytest.raises(SessionNotFoundError):
        await store.get(lease.session_id, now=now)
    with sqlite3.connect(path) as connection:
        remaining = connection.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    assert remaining == 0


@pytest.mark.asyncio
async def test_purge_expired_is_limited(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    await store.initialize()
    now = datetime(2026, 9, 22, tzinfo=UTC)
    expired_ids = []
    for _ in range(2):
        snapshot = await store.create(now=now, expires_at=now + timedelta(seconds=1))
        expired_ids.append(snapshot.session.session_id)

    assert await store.purge_expired(now=now + timedelta(seconds=2), limit=1) == 1
    missing = 0
    for session_id in expired_ids:
        try:
            await store.get(session_id, now=now + timedelta(seconds=2))
        except SessionNotFoundError:
            missing += 1
        except SessionExpiredError:
            pass
    assert missing == 1


@pytest.mark.asyncio
async def test_purge_preserves_session_with_active_lease(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    await store.initialize()
    now = datetime(2026, 9, 22, tzinfo=UTC)
    created = await store.create(now=now, expires_at=now + timedelta(seconds=1))
    await store.acquire(
        created.session.session_id,
        now=now,
        lease_until=now + timedelta(minutes=10),
    )

    assert await store.purge_expired(now=now + timedelta(seconds=2), limit=100) == 0
    with pytest.raises(SessionExpiredError):
        await store.get(created.session.session_id, now=now + timedelta(seconds=2))


@pytest.mark.asyncio
async def test_release_is_idempotent_and_allows_reacquire(tmp_path: Path) -> None:
    store, lease, now = await store_with_lease(tmp_path)

    await store.release(lease)
    await store.release(lease)
    reacquired = await store.acquire(
        lease.session_id,
        now=now,
        lease_until=now + timedelta(minutes=10),
    )

    assert reacquired.token != lease.token


@pytest.mark.asyncio
async def test_complete_keeps_only_newest_max_turns(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    await store.initialize()
    now = datetime(2026, 9, 22, tzinfo=UTC)
    snapshot = await store.create(now=now, expires_at=now + timedelta(days=7))

    for sequence in range(1, 4):
        lease = await store.acquire(
            snapshot.session.session_id,
            now=now,
            lease_until=now + timedelta(minutes=10),
        )
        snapshot = await store.complete(
            lease,
            sample_turn(f"P{sequence}", f"R{sequence}"),
            now=now,
            expires_at=now + timedelta(days=7),
            max_turns=2,
        )

    assert [turn.sequence for turn in snapshot.turns] == [2, 3]
