import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.observability.audit import (
    AuditEvent,
    AuditEventType,
    AuditOperation,
    AuditOutcome,
)

REQUEST_ID = UUID("00000000-0000-0000-0000-000000000001")
EVENT_ID = UUID("00000000-0000-0000-0000-000000000002")


def test_event_is_immutable_and_serializes_only_allowlisted_fields() -> None:
    event = AuditEvent(
        event_id=EVENT_ID,
        timestamp=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        request_id=REQUEST_ID,
        event_type="chat.completed",
        outcome="success",
        operation="chat",
        duration_ms=7,
        provider="groq",
        model="openai/gpt-oss-120b",
        grounded=True,
        source_count=2,
        citation_count=2,
        citation_retry_count=0,
        retrieval_query_count=1,
    )

    with pytest.raises(FrozenInstanceError):
        event.duration_ms = 8

    payload = json.loads(event.to_json())
    assert payload["timestamp"] == "2026-09-24T12:00:00Z"
    assert payload["request_id"] == str(REQUEST_ID)
    assert payload["duration_ms"] == 7
    assert payload["provider"] == "groq"
    assert payload["model"] == "openai/gpt-oss-120b"
    assert "question" not in payload
    assert "answer" not in payload
    assert "prompt" not in payload
    assert "source" not in payload
    assert "excerpt" not in payload
    assert "payload" not in payload
    assert "message" not in payload
    assert "details" not in payload


def test_event_omits_none_and_rejects_invalid_duration() -> None:
    event = AuditEvent(
        event_id=EVENT_ID,
        timestamp=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        request_id=REQUEST_ID,
        event_type="session.created",
        outcome="success",
        operation="session.create",
        duration_ms=0,
    )

    assert "session_id" not in event.to_dict()
    with pytest.raises(ValueError, match="duration_ms"):
        AuditEvent(
            event_id=event.event_id,
            timestamp=event.timestamp,
            request_id=event.request_id,
            event_type="session.created",
            outcome="success",
            operation="session.create",
            duration_ms=-1,
        )


def test_event_normalizes_aware_timestamp_and_uuid_fields() -> None:
    timestamp = datetime(2026, 9, 24, 9, 0, tzinfo=timezone(timedelta(hours=-3)))
    session_id = UUID("00000000-0000-0000-0000-000000000003")

    event = AuditEvent(
        event_id=EVENT_ID,
        timestamp=timestamp,
        request_id=REQUEST_ID,
        event_type=AuditEventType.SESSION_CREATED,
        outcome=AuditOutcome.SUCCESS,
        operation=AuditOperation.SESSION_CREATE,
        duration_ms=0,
        session_id=session_id,
    )

    assert event.timestamp == datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    assert event.to_dict()["event_id"] == str(EVENT_ID)
    assert event.to_dict()["session_id"] == str(session_id)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_type", "chat.started"),
        ("outcome", "partial"),
        ("operation", "search"),
        ("provider", "unknown-provider"),
        ("model", "unapproved-model"),
        ("status_code", 418),
        ("error_code", "raw_provider_error"),
        ("error_type", "raw_exception"),
    ],
)
def test_event_rejects_values_outside_the_closed_taxonomy(field: str, value: object) -> None:
    values: dict[str, object] = {
        "event_id": EVENT_ID,
        "timestamp": datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        "request_id": REQUEST_ID,
        "event_type": "chat.completed",
        "outcome": "success",
        "operation": "chat",
        "duration_ms": 0,
    }
    values[field] = value

    with pytest.raises((TypeError, ValueError), match=field):
        AuditEvent(**values)


def test_event_rejects_naive_or_non_integer_metrics_and_extra_fields() -> None:
    base = {
        "event_id": EVENT_ID,
        "timestamp": datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        "request_id": REQUEST_ID,
        "event_type": "chat.completed",
        "outcome": "success",
        "operation": "chat",
        "duration_ms": 0,
    }

    with pytest.raises(ValueError, match="timestamp"):
        AuditEvent(**{**base, "timestamp": datetime(2026, 9, 24, 12, 0)})

    with pytest.raises(TypeError, match="source_count"):
        AuditEvent(**{**base, "source_count": True})

    with pytest.raises(TypeError, match="payload"):
        AuditEvent(**{**base, "payload": "sensitive content"})
