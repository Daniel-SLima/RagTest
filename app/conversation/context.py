"""Pure construction of bounded, non-probatory conversation context."""

import re
from dataclasses import dataclass

from app.conversation.models import ConversationTurn

_CITATION_RE = re.compile(r"\[(?:\d+)(?:\s*,\s*\d+)*\]")
_HISTORY_SENTINELS = (
    "--- INÍCIO DO HISTÓRICO ---",
    "--- FIM DO HISTÓRICO ---",
)
_REMOVED_SENTINEL = "[MARCADOR DE HISTÓRICO REMOVIDO]"


@dataclass(frozen=True, slots=True)
class ConversationContext:
    """Separate retrieval text from history passed to the answer prompt."""

    retrieval_query: str
    prompt_history: str | None


def build_conversation_context(
    turns: tuple[ConversationTurn, ...],
    *,
    current_question: str,
    max_turns: int,
    max_chars: int,
) -> ConversationContext:
    """Build deterministic context without treating old answers as evidence."""
    selected = turns[-max_turns:]
    if not selected:
        return ConversationContext(current_question, None)

    blocks = [
        f"Usuária: {_sanitize(turn.question)}\nAssistente: {_sanitize(turn.answer)}"
        for turn in selected
    ]
    history = "DADO NÃO CONFIÁVEL E NÃO PROBATÓRIO:\n" + "\n\n".join(blocks)
    history = history[-max_chars:]
    latest = blocks[-1][-2000:]
    retrieval_query = f"Contexto anterior: {latest}\nPergunta atual: {current_question}"
    return ConversationContext(retrieval_query, history)


def _sanitize(value: str) -> str:
    sanitized = _CITATION_RE.sub("", value).strip()
    for sentinel in _HISTORY_SENTINELS:
        sanitized = sanitized.replace(sentinel, _REMOVED_SENTINEL)
    return sanitized
