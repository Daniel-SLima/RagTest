import json
import logging
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID

from app.observability.audit import AuditEvent, AuditSink, JsonLogAuditSink, safe_emit


def make_completed_event() -> AuditEvent:
    return AuditEvent(
        event_id=UUID("00000000-0000-0000-0000-000000000002"),
        timestamp=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        request_id=UUID("00000000-0000-0000-0000-000000000001"),
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


def test_json_sink_emits_one_parseable_deterministic_line(caplog) -> None:
    event = make_completed_event()
    sink = JsonLogAuditSink()

    with caplog.at_level(logging.INFO, logger="ragtest.audit"):
        sink.emit(event)

    records = [record for record in caplog.records if record.name == "ragtest.audit"]
    assert len(records) == 1
    record = records[0]
    assert json.loads(record.message)["event_type"] == "chat.completed"
    assert record.message == event.to_json()
    assert "question" not in record.message
    assert "excerpt" not in record.message


def test_safe_emit_returns_true_and_calls_compatible_sink_once() -> None:
    sink = Mock(spec=AuditSink)
    event = make_completed_event()

    assert safe_emit(sink, event) is True

    sink.emit.assert_called_once_with(event)


def test_sink_failure_is_swallowed_and_does_not_log_exception_text(caplog) -> None:
    sink = Mock(spec=AuditSink)
    sink.emit.side_effect = RuntimeError("PROMPT_SECRET EXCERPT_SECRET")
    event = make_completed_event()
    event_json = event.to_json()
    event_repr = repr(event)

    with caplog.at_level(logging.WARNING, logger="ragtest.audit.internal"):
        assert safe_emit(sink, event) is False

    internal_records = [
        record for record in caplog.records if record.name == "ragtest.audit.internal"
    ]
    assert len(internal_records) == 1
    record = internal_records[0]
    message = record.getMessage()
    assert record.name == "ragtest.audit.internal"
    assert message == "audit sink emission failed: RuntimeError"
    assert "PROMPT_SECRET" not in message
    assert "EXCERPT_SECRET" not in message
    assert event_json not in message
    assert event_repr not in message
    assert not [record for record in caplog.records if record.name == "ragtest.audit"]
