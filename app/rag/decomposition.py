import json
import logging
import re
from dataclasses import dataclass

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_DECOMPOSITION_SYSTEM_PROMPT = """Você é um planejador de recuperação documental.

Sua única tarefa é decidir se a pergunta do usuário contém múltiplas subintenções
independentes que se beneficiariam de buscas separadas.

Não responda à pergunta.

Retorne SOMENTE JSON válido em um destes formatos:

{"subqueries": []}

ou

{"subqueries": ["consulta 1", "consulta 2"]}

Regras:
- Use 2 ou 3 subconsultas somente quando houver realmente múltiplas intenções.
- Para uma pergunta de intenção única, retorne uma lista vazia.
- Cada subconsulta deve ser autossuficiente para busca documental.
- Preserve população, contexto, restrições e assunto da pergunta original.
- Não invente assunto, condição clínica, público ou requisito que não esteja na pergunta.
- Não repita a pergunta composta original como uma das subconsultas.
- Não explique a decisão.
"""

_COMPOUND_HINTS = (
    re.compile(r"\b(e|ou)\b", re.IGNORECASE),
    re.compile(r"\bal[eé]m de\b", re.IGNORECASE),
    re.compile(r"\bbem como\b", re.IGNORECASE),
    re.compile(r"\btamb[eé]m\b", re.IGNORECASE),
    re.compile(r"[;]"),
)


@dataclass(frozen=True, slots=True)
class DecompositionResult:
    attempted: bool
    used: bool
    subqueries: tuple[str, ...]
    status: str


def should_attempt_decomposition(question: str) -> bool:
    text = " ".join(question.split())
    if len(text) < 12:
        return False
    return any(pattern.search(text) for pattern in _COMPOUND_HINTS)


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    fence = chr(96) * 3
    if cleaned.startswith(fence):
        cleaned = re.sub(r"^\x60\x60\x60(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*\x60\x60\x60$", "", cleaned)
    return cleaned.strip()


def parse_subqueries(
    raw_text: str,
    original_question: str,
    *,
    max_subqueries: int = 3,
) -> tuple[str, ...]:
    cleaned = _strip_code_fence(raw_text)

    if "{" in cleaned and "}" in cleaned:
        cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]

    try:
        payload = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return ()

    if isinstance(payload, dict):
        raw_queries = payload.get("subqueries", [])
    elif isinstance(payload, list):
        raw_queries = payload
    else:
        return ()

    if not isinstance(raw_queries, list):
        return ()

    original_normalized = " ".join(original_question.casefold().split())
    seen: set[str] = set()
    result: list[str] = []

    for item in raw_queries:
        if not isinstance(item, str):
            continue

        query = " ".join(item.split()).strip()
        if len(query) < 4:
            continue

        normalized = query.casefold()
        if normalized == original_normalized or normalized in seen:
            continue

        seen.add(normalized)
        result.append(query)

        if len(result) >= max_subqueries:
            break

    return tuple(result)


async def decompose_question(
    question: str,
    *,
    llm: LLMProvider,
    enabled: bool = True,
    max_subqueries: int = 3,
) -> DecompositionResult:
    if not enabled:
        return DecompositionResult(False, False, (), "disabled")

    if not should_attempt_decomposition(question):
        return DecompositionResult(False, False, (), "not-needed")

    try:
        raw = await llm.generate(
            system_prompt=_DECOMPOSITION_SYSTEM_PROMPT,
            user_prompt=f"Pergunta do usuário:\n{question}",
        )
    except Exception:
        logger.warning(
            "Automatic query decomposition failed; using single-query retrieval.",
            exc_info=True,
        )
        return DecompositionResult(True, False, (), "fallback-error")

    subqueries = parse_subqueries(
        raw,
        question,
        max_subqueries=max_subqueries,
    )

    if len(subqueries) < 2:
        return DecompositionResult(True, False, (), "single-query")

    return DecompositionResult(True, True, subqueries, "multi-query")
