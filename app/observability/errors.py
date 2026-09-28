"""Stable, content-free error classifications for public chat failures."""

from dataclasses import dataclass

from fastapi import HTTPException

from app.conversation.models import (
    SessionBusyError,
    SessionConflictError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.llm.base import LLMProviderRequestError, LLMServiceUnavailableError


@dataclass(frozen=True, slots=True)
class NormalizedError:
    """Safe error metadata that never copies exception details."""

    status_code: int
    error_code: str
    error_type: str
    public_detail: str


def _session_error(
    status_code: int,
    error_code: str,
    public_detail: str,
) -> NormalizedError:
    return NormalizedError(status_code, error_code, "session", public_detail)


def normalize_status(status_code: int) -> NormalizedError:
    """Map an observed HTTP status to a safe audit/public error class."""

    if status_code == 401:
        return NormalizedError(401, "unauthorized", "auth", "Invalid or missing API key.")
    if status_code == 429:
        return NormalizedError(429, "rate_limited", "rate_limit", "Too many requests.")
    if status_code == 404:
        return _session_error(404, "session_not_found", "Session not found.")
    if status_code == 409:
        return _session_error(409, "session_conflict", "Session conflict.")
    if status_code == 410:
        return _session_error(410, "session_expired", "Session expired.")
    if status_code == 422:
        return NormalizedError(
            422,
            "validation_error",
            "validation",
            "Request validation failed.",
        )
    if status_code == 503:
        return NormalizedError(
            503,
            "provider_unavailable",
            "provider",
            "LLM provider is temporarily unavailable.",
        )
    return NormalizedError(502, "provider_error", "provider", "LLM provider request failed.")


def normalize_exception(exception: Exception) -> NormalizedError:
    """Convert known exceptions to stable classes without exposing their text."""

    if isinstance(exception, SessionNotFoundError):
        return _session_error(404, "session_not_found", "Session not found.")
    if isinstance(exception, SessionBusyError):
        return _session_error(409, "session_busy", "Session is busy.")
    if isinstance(exception, SessionConflictError):
        return _session_error(409, "session_conflict", "Session conflict.")
    if isinstance(exception, SessionExpiredError):
        return _session_error(410, "session_expired", "Session expired.")
    if isinstance(exception, LLMServiceUnavailableError):
        return NormalizedError(
            503,
            "provider_unavailable",
            "provider",
            "LLM provider is temporarily unavailable.",
        )
    if isinstance(exception, LLMProviderRequestError):
        return NormalizedError(502, "provider_error", "provider", "LLM provider request failed.")
    if isinstance(exception, HTTPException):
        return normalize_status(exception.status_code)
    return NormalizedError(502, "internal_error", "unhandled", "Internal server error.")
