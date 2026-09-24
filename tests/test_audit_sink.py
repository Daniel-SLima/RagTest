import json
import logging
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID

from app.observability import audit


def make_completed_event() -> audit.AuditEvent:
    return audit.AuditEvent(
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
    sink_type = getattr(audit, "JsonLogAuditSink", None)
    assert sink_type is not None
    sink = sink_type()

    with caplog.at_level(logging.INFO, logger="ragtest.audit"):
        sink.emit(event)

    records = [record for record in caplog.records if record.name == "ragtest.audit"]
    assert len(records) == 1
    record = records[0]
    assert json.loads(record.message)["event_type"] == "chat.completed"
    assert record.message == event.to_json()
    assert "question" not in record.message
    assert "excerpt" not in record.message


def test_sink_failure_is_swallowed_and_does_not_log_exception_text(caplog) -> None:
    sink = Mock()
    sink.emit.side_effect = RuntimeError("PROMPT_SECRET EXCERPT_SECRET")
    event = make_completed_event()

    with caplog.at_level(logging.WARNING, logger="ragtest.audit.internal"):
        safe_emit = getattr(audit, "safe_emit", None)
        assert safe_emit is not None
        assert safe_emit(sink, event) is False

    assert "PROMPT_SECRET" not in caplog.text
    assert "EXCERPT_SECRET" not in caplog.text
    assert "RuntimeError" in caplog.text
