from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.rag.chat import ChatResult

DisplayStatus = Literal["emergency", "out_of_scope", "verified", "unverified", "no_sources"]
DisplayTone = Literal["danger", "neutral", "success", "warning"]

_BRASILIA = timezone(timedelta(hours=-3))

_SOURCE_TITLES = {
    "servicos/catalogo_servicos.json": "Catálogo de serviços do Se Cuida Mulher",
}


@dataclass(frozen=True, slots=True)
class Display:
    status: DisplayStatus
    tone: DisplayTone
    title: str
    message: str


_DISPLAYS: dict[DisplayStatus, Display] = {
    "emergency": Display(
        "emergency",
        "danger",
        "Sinal de alerta",
        "Procure atendimento agora. Não espere a resposta do chat.",
    ),
    "out_of_scope": Display(
        "out_of_scope",
        "neutral",
        "Fora dos temas disponíveis",
        "Esta pergunta não está coberta pelas cartilhas e orientações disponíveis.",
    ),
    "verified": Display(
        "verified",
        "success",
        "Citações verificadas",
        "As afirmações informativas estão acompanhadas de referências do corpus.",
    ),
    "unverified": Display(
        "unverified",
        "warning",
        "Citações não verificadas",
        "Não foi possível validar as citações desta resposta. Consulte as fontes recuperadas.",
    ),
    "no_sources": Display(
        "no_sources",
        "warning",
        "Sem base documental suficiente",
        "Não foram encontrados trechos relevantes o bastante para fundamentar uma resposta.",
    ),
}


def build_display(result: ChatResult) -> Display:
    if result.safety is not None and result.safety.triggered:
        return _DISPLAYS["emergency"]
    if result.out_of_scope:
        return _DISPLAYS["out_of_scope"]
    if result.grounded:
        return _DISPLAYS["verified"]
    if result.sources:
        return _DISPLAYS["unverified"]
    return _DISPLAYS["no_sources"]


def source_title(source: str) -> str:
    normalized = source.replace("\\", "/")
    if normalized in _SOURCE_TITLES:
        return _SOURCE_TITLES[normalized]
    return normalized.rsplit("/", 1)[-1]


def source_location_label(page: int | None) -> str | None:
    return None if page is None else f"Página {page}"


def local_today(timezone_name: str) -> date:
    try:
        tz = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        tz = _BRASILIA
    return datetime.now(UTC).astimezone(tz).date()
