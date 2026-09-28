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
REQUIRED_AUDIT_KEYS = {
    "event_id",
    "timestamp",
    "request_id",
    "event_type",
    "outcome",
    "operation",
    "duration_ms",
}
OPTIONAL_AUDIT_KEYS = {
    "session_id",
    "provider",
    "model",
    "status_code",
    "error_code",
    "error_type",
    "grounded",
    "source_count",
    "citation_count",
    "citation_retry_count",
    "retrieval_query_count",
    "turn_count",
}


def _minimal_event_kwargs() -> dict[str, object]:
    return {
        "event_id": EVENT_ID,
        "timestamp": datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        "request_id": REQUEST_ID,
        "event_type": "chat.completed",
        "outcome": "success",
        "operation": "chat",
        "duration_ms": 0,
    }


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
    serialized = event.to_json()
    assert serialized == event.to_json()
    assert "\n" not in serialized
    assert ": " not in serialized
    assert ", " not in serialized
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

    assert set(event.to_dict()) == REQUIRED_AUDIT_KEYS
    assert not (set(event.to_dict()) & OPTIONAL_AUDIT_KEYS)
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


def test_event_serializes_the_exact_allowlisted_key_set_and_no_sensitive_sentinels() -> None:
    event = AuditEvent(
        **_minimal_event_kwargs(),
        session_id=UUID("00000000-0000-0000-0000-000000000003"),
        provider="groq",
        model="openai/gpt-oss-120b",
        status_code=503,
        error_code="provider_unavailable",
        error_type="provider",
        grounded=False,
        source_count=2,
        citation_count=1,
        citation_retry_count=0,
        retrieval_query_count=1,
        turn_count=3,
    )

    payload = event.to_dict()
    assert set(payload) == REQUIRED_AUDIT_KEYS | OPTIONAL_AUDIT_KEYS
    serialized = event.to_json()
    for sentinel in (
        "METADATA_SENTINEL",
        "HISTORY_SENTINEL",
        "FILENAME_SENTINEL",
        "AUTHORIZATION_SENTINEL",
        "API_KEY_SENTINEL",
        "TOKEN_SENTINEL",
        "TRACEBACK_SENTINEL",
    ):
        assert sentinel not in serialized


@pytest.mark.parametrize("field", ["event_id", "request_id", "session_id"])
def test_event_rejects_string_uuids(field: str) -> None:
    values = _minimal_event_kwargs()
    values[field] = "UUID_SENTINEL"

    with pytest.raises(TypeError, match=field):
        AuditEvent(**values)


@pytest.mark.parametrize(
    "field",
    [
        "source_count",
        "citation_count",
        "citation_retry_count",
        "retrieval_query_count",
        "turn_count",
    ],
)
def test_event_rejects_negative_optional_counts(field: str) -> None:
    values = _minimal_event_kwargs()
    values[field] = -1

    with pytest.raises(ValueError, match=field):
        AuditEvent(**values)


def test_event_slots_reject_arbitrary_attributes() -> None:
    event = AuditEvent(**_minimal_event_kwargs())

    assert not hasattr(event, "__dict__")
    with pytest.raises((AttributeError, TypeError)):
        event.arbitrary_attribute = "ATTRIBUTE_SENTINEL"


@pytest.mark.parametrize(
    "field",
    [
        "question",
        "answer",
        "prompt",
        "source",
        "excerpt",
        "metadata",
        "history",
        "filename",
        "authorization",
        "api_key",
        "token",
        "traceback",
    ],
)
def test_event_rejects_content_and_generic_fields(field: str) -> None:
    values = _minimal_event_kwargs()
    values[field] = f"{field.upper()}_SENTINEL"

    with pytest.raises(TypeError, match=field):
        AuditEvent(**values)
