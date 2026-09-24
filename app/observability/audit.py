"""Closed, content-free audit event contract and interchangeable sinks."""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Final, Protocol
from uuid import UUID


class AuditEventType(str, Enum):
    """Lifecycle event names accepted by the audit contract."""

    SESSION_CREATED = "session.created"
    SESSION_READ = "session.read"
    SESSION_DELETED = "session.deleted"
    CHAT_COMPLETED = "chat.completed"
    CHAT_FAILED = "chat.failed"


class AuditOutcome(str, Enum):
    """Stable result classes for audit events."""

    SUCCESS = "success"
    FAILURE = "failure"


class AuditOperation(str, Enum):
    """Operations represented by the first audit contract."""

    SESSION_CREATE = "session.create"
    SESSION_READ = "session.read"
    SESSION_DELETE = "session.delete"
    CHAT = "chat"


class AuditSink(Protocol):
    """Destination for one structured audit event."""

    def emit(self, event: "AuditEvent") -> None: ...


_ALLOWED_PROVIDERS: Final = frozenset({"gemini", "groq", "ollama"})
_ALLOWED_MODELS: Final = frozenset(
    {
        "gemini-3.6-flash",
        "openai/gpt-oss-120b",
        "qwen3:8b",
    }
)
_ALLOWED_STATUS_CODES: Final = frozenset({404, 409, 410, 422, 502, 503})
_ALLOWED_ERROR_CODES: Final = frozenset(
    {
        "session_not_found",
        "session_busy",
        "session_conflict",
        "session_expired",
        "validation_error",
        "provider_error",
        "internal_error",
        "provider_unavailable",
    }
)
_ALLOWED_ERROR_TYPES: Final = frozenset({"session", "validation", "provider", "unhandled"})


def _coerce_enum[T: Enum](field_name: str, enum_type: type[T], value: object) -> T:
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or {enum_type.__name__}")
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise ValueError(f"{field_name} must be one of: {allowed}") from exc


def _require_uuid(field_name: str, value: object) -> UUID:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be a UUID")
    return value


def _require_timestamp(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("timestamp must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_negative_int(field_name: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _optional_uuid(field_name: str, value: UUID | None) -> UUID | None:
    if value is None:
        return None
    return _require_uuid(field_name, value)


def _optional_allowlisted_string(
    field_name: str,
    value: str | None,
    allowed: frozenset[str],
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {choices}")
    return value


def _optional_non_negative_int(field_name: str, value: int | None) -> int | None:
    if value is None:
        return None
    return _require_non_negative_int(field_name, value)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Immutable, allowlisted metadata for one operational event."""

    event_id: UUID
    timestamp: datetime
    request_id: UUID
    event_type: AuditEventType | str
    outcome: AuditOutcome | str
    operation: AuditOperation | str
    duration_ms: int
    session_id: UUID | None = None
    provider: str | None = None
    model: str | None = None
    status_code: int | None = None
    error_code: str | None = None
    error_type: str | None = None
    grounded: bool | None = None
    source_count: int | None = None
    citation_count: int | None = None
    citation_retry_count: int | None = None
    retrieval_query_count: int | None = None
    turn_count: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_uuid("event_id", self.event_id))
        object.__setattr__(self, "timestamp", _require_timestamp(self.timestamp))
        object.__setattr__(self, "request_id", _require_uuid("request_id", self.request_id))
        object.__setattr__(
            self,
            "event_type",
            _coerce_enum("event_type", AuditEventType, self.event_type),
        )
        object.__setattr__(self, "outcome", _coerce_enum("outcome", AuditOutcome, self.outcome))
        object.__setattr__(
            self,
            "operation",
            _coerce_enum("operation", AuditOperation, self.operation),
        )
        object.__setattr__(
            self,
            "duration_ms",
            _require_non_negative_int("duration_ms", self.duration_ms),
        )
        object.__setattr__(self, "session_id", _optional_uuid("session_id", self.session_id))
        object.__setattr__(
            self,
            "provider",
            _optional_allowlisted_string("provider", self.provider, _ALLOWED_PROVIDERS),
        )
        object.__setattr__(
            self,
            "model",
            _optional_allowlisted_string("model", self.model, _ALLOWED_MODELS),
        )
        if self.status_code is not None:
            if not isinstance(self.status_code, int) or isinstance(self.status_code, bool):
                raise TypeError("status_code must be an integer")
            if self.status_code not in _ALLOWED_STATUS_CODES:
                raise ValueError("status_code must be an allowlisted HTTP status")
        object.__setattr__(
            self,
            "error_code",
            _optional_allowlisted_string("error_code", self.error_code, _ALLOWED_ERROR_CODES),
        )
        object.__setattr__(
            self,
            "error_type",
            _optional_allowlisted_string("error_type", self.error_type, _ALLOWED_ERROR_TYPES),
        )
        if self.grounded is not None and not isinstance(self.grounded, bool):
            raise TypeError("grounded must be a boolean")
        object.__setattr__(
            self,
            "source_count",
            _optional_non_negative_int("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "citation_count",
            _optional_non_negative_int("citation_count", self.citation_count),
        )
        object.__setattr__(
            self,
            "citation_retry_count",
            _optional_non_negative_int("citation_retry_count", self.citation_retry_count),
        )
        object.__setattr__(
            self,
            "retrieval_query_count",
            _optional_non_negative_int("retrieval_query_count", self.retrieval_query_count),
        )
        object.__setattr__(self, "turn_count", _optional_non_negative_int("turn_count", self.turn_count))

    def to_dict(self) -> dict[str, object]:
        """Return only the explicit allowlisted fields, omitting optional nulls."""

        payload: dict[str, object] = {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "request_id": str(self.request_id),
            "event_type": self.event_type.value,
            "outcome": self.outcome.value,
            "operation": self.operation.value,
            "duration_ms": self.duration_ms,
        }
        optional_fields = (
            ("session_id", str(self.session_id) if self.session_id is not None else None),
            ("provider", self.provider),
            ("model", self.model),
            ("status_code", self.status_code),
            ("error_code", self.error_code),
            ("error_type", self.error_type),
            ("grounded", self.grounded),
            ("source_count", self.source_count),
            ("citation_count", self.citation_count),
            ("citation_retry_count", self.citation_retry_count),
            ("retrieval_query_count", self.retrieval_query_count),
            ("turn_count", self.turn_count),
        )
        payload.update({key: value for key, value in optional_fields if value is not None})
        return payload

    def to_json(self) -> str:
        """Return deterministic JSON without an extensible payload surface."""

        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )


class JsonLogAuditSink:
    """Emit the event's deterministic JSON on the structured audit logger."""

    def emit(self, event: AuditEvent) -> None:
        logging.getLogger("ragtest.audit").info(event.to_json())


def safe_emit(sink: AuditSink, event: AuditEvent) -> bool:
    """Emit an event without allowing sink failures to affect application behavior."""

    try:
        sink.emit(event)
    except Exception as exc:  # noqa: BLE001 - sink failures must never escape
        logging.getLogger("ragtest.audit.internal").warning(
            "audit sink emission failed: %s", type(exc).__name__
        )
        return False
    return True
