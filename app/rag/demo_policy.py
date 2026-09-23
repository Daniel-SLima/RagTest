from __future__ import annotations

import re
from hashlib import sha256

from app.rag.vector_store import SearchHit
from app.schemas.demo import DemoScore, DemoSource

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]+")
_AUTH_RE = re.compile(r"(?i)\bauthorization\s*:\s*\S+(?:\s+\S+)?")
_AUTH_SCHEME_RE = re.compile(r"(?i)\b(?:bearer|basic)\s+\S+")
_SECRET_RE = re.compile(
    r"(?i)\b(?:api[_ -]?key|token|secret|password)\s*(?:[:=]|\s)\s*\S+"
)
_URL_RE = re.compile(r"(?i)https?://\S+")
_WINDOWS_PATH_RE = re.compile(r"(?i)(?:[a-z]:[\\/]|\\\\)[^\s]+")
_POSIX_PATH_RE = re.compile(r"(?<![\w:])/(?:[^\s/]+/)*[^\s]+")
_DOTENV_RE = re.compile(r"(?i)\.env(?:\s*[:=]\s*\S+)?")
_PROMPT_RE = re.compile(r"(?i)(?:system|user|developer)[ _-]?prompt\s*[:=]\s*\S+")
_TRACEBACK_RE = re.compile(r"(?i)traceback\s*\(most recent call last\).*")
_UNSAFE_RUNTIME_RE = re.compile(
    r"(?i)(?:https?://|[a-z]:[\\/]|\\\\|\.env|api[_ -]?key|token|secret|password|bearer|basic)"
)


def _relative_components(value: str, *, prefix: bool) -> tuple[str, ...] | None:
    normalized = value.strip().replace("\\", "/")
    if not normalized or normalized.startswith("/") or re.match(r"^[a-z]:", normalized):
        return None
    if normalized.startswith("//"):
        return None
    if prefix:
        normalized = normalized.rstrip("/")
    parts = tuple(part.lower() for part in normalized.split("/"))
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return None
    return parts


def sanitize_excerpt(value: str, *, limit: int = 500) -> str:
    text = _CONTROL_RE.sub(" ", value)
    text = _URL_RE.sub("[redacted]", text)
    text = _AUTH_RE.sub("[redacted]", text)
    text = _AUTH_SCHEME_RE.sub("[redacted]", text)
    text = _SECRET_RE.sub("[redacted]", text)
    text = _DOTENV_RE.sub("[redacted]", text)
    text = _PROMPT_RE.sub("[redacted]", text)
    text = _TRACEBACK_RE.sub("[redacted]", text)
    text = _WINDOWS_PATH_RE.sub("[redacted]", text)
    text = _POSIX_PATH_RE.sub("[redacted]", text)
    return " ".join(text.split())[:limit].strip()


def sanitize_runtime_label(value: str, *, limit: int = 120) -> str:
    text = " ".join(_CONTROL_RE.sub(" ", value).split())
    if _UNSAFE_RUNTIME_RE.search(text) or sanitize_excerpt(text, limit=limit) != text[:limit]:
        return "configured"
    return text[:limit]


class DemoSourcePolicy:
    policy_id = "demo-source-allowlist-v1"

    def __init__(self, prefixes: str) -> None:
        self.prefixes = tuple(
            parts
            for prefix in prefixes.split(",")
            if (parts := _relative_components(prefix, prefix=True)) is not None
        )

    def allows(self, source: str) -> bool:
        components = _relative_components(source, prefix=False)
        if components is None:
            return False
        if "chatscm" in "/".join(components):
            return False
        if any(part == "private" or part.startswith("private_") for part in components):
            return False
        return bool(self.prefixes) and any(components[: len(prefix)] == prefix for prefix in self.prefixes)


def _public_document(source: str) -> str:
    normalized = source.replace("\\", "/")
    if ":" in normalized or normalized.startswith("/"):
        return "document-" + sha256(source.encode("utf-8")).hexdigest()[:12]
    name = normalized.rsplit("/", 1)[-1].strip()
    return name[:120] or "document"


def public_source_from_hit(
    hit: SearchHit,
    *,
    order: int,
    fusion_available: bool = False,
) -> DemoSource:
    identity = f"{hit.source}|{hit.page or 0}|{hit.content}"
    public_id = "src_" + sha256(identity.encode("utf-8")).hexdigest()[:16]
    return DemoSource(
        public_id=public_id,
        document=_public_document(hit.source),
        page=hit.page,
        order=order,
        excerpt=sanitize_excerpt(hit.content),
        scores=DemoScore(
            dense_score=hit.dense_score,
            sparse_score=hit.sparse_score,
            rank_score=hit.rank_score,
            fusion_score=hit.score if fusion_available else None,
        ),
    )
