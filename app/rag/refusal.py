import re

from app.safety.triage import normalize_text

NO_CONTEXT_MARKER = "SEM_BASE_DOCUMENTAL"

_CITATION = re.compile(r"\[\d+\]")
_LIST_ITEM = re.compile(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+")
_REFUSAL = re.compile(
    r"nao (?:contem|ha|trazem|apresentam|possuem|incluem|mencionam|abordam) "
    r"(?:nenhuma |qualquer )?informac"
    r"|nao e possivel responder"
    r"|nao sao suficientes para responder"
    r"|nao (?:encontrei|foram encontrad\w*) (?:informac|trecho)"
)
_MAX_REFUSAL_CHARS = 500


def is_refusal(answer: str) -> bool:
    if NO_CONTEXT_MARKER in answer:
        return True
    text = _CITATION.sub("", answer).strip()
    if len(text) > _MAX_REFUSAL_CHARS or _LIST_ITEM.search(text):
        return False
    return bool(_REFUSAL.search(normalize_text(text)))
