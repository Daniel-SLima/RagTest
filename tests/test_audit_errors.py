from app.conversation.models import (
    SessionBusyError,
    SessionConflictError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.llm.base import LLMServiceUnavailableError
from app.observability.errors import normalize_exception


def test_provider_error_normalizes_without_raw_detail() -> None:
    normalized = normalize_exception(
        RuntimeError("PROMPT_SECRET EXCERPT_SECRET https://private.invalid")
    )

    assert normalized.status_code == 502
    assert normalized.error_code == "provider_error"
    assert normalized.error_type == "provider"
    assert normalized.public_detail == "LLM provider request failed."
    assert "PROMPT_SECRET" not in normalized.public_detail


def test_unexpected_error_uses_stable_internal_class() -> None:
    normalized = normalize_exception(ValueError("ANSWER_SECRET"))

    assert normalized.status_code == 502
    assert normalized.error_code == "internal_error"
    assert normalized.error_type == "unhandled"
    assert "ANSWER_SECRET" not in normalized.public_detail


def test_known_session_and_provider_failures_keep_stable_taxonomy() -> None:
    cases = [
        (SessionNotFoundError("DETAIL_SECRET"), 404, "session_not_found", "session"),
        (SessionBusyError("DETAIL_SECRET"), 409, "session_busy", "session"),
        (SessionConflictError("DETAIL_SECRET"), 409, "session_conflict", "session"),
        (SessionExpiredError("DETAIL_SECRET"), 410, "session_expired", "session"),
        (
            LLMServiceUnavailableError("DETAIL_SECRET"),
            503,
            "provider_unavailable",
            "provider",
        ),
    ]

    for exception, status_code, error_code, error_type in cases:
        normalized = normalize_exception(exception)

        assert (normalized.status_code, normalized.error_code, normalized.error_type) == (
            status_code,
            error_code,
            error_type,
        )
        assert "DETAIL_SECRET" not in normalized.public_detail
