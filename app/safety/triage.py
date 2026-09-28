import re
import unicodedata
from dataclasses import dataclass

TRIAGE_MODEL_NAME = "triagem-deterministica"

_FIRST_PERSON = re.compile(
    r"\b(estou|esta|to|tou|tenho|sinto|sentindo|minha|meu|meus|minhas|me|eu)\b"
)
_PREGNANCY = re.compile(
    r"gravid|gestant|gestacao|\bbebe\b|pre-?natal|bolsa\s+(\w+\s+)?(estourou|rompeu)|contrac"
    r"|perd\w*\s+(de\s+)?liquido"
)
_BODY_PART = re.compile(r"\b(pes?|pernas?|rosto|maos?)\b")

_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("pressao_alta", re.compile(r"pressao\s+(\w+\s+){0,2}(alta|subiu|subindo)")),
    (
        "alteracao_visual",
        re.compile(r"(visao|vista)\s+(\w+\s+){0,2}(embacad|embaralhad|turva|escurecid)|estrelinha"),
    ),
    (
        "cefaleia_forte",
        re.compile(r"dor(es)?\s+de\s+cabeca\s+(\w+\s+){0,2}fort|fort\w*\s+dor(es)?\s+de\s+cabeca"),
    ),
    ("sangramento", re.compile(r"sangrando|sangramento|perdendo\s+sangue|saindo\s+sangue")),
    (
        "perda_liquido",
        re.compile(
            r"bolsa\s+(\w+\s+)?(estourou|rompeu|estourada|rompida)"
            r"|perd\w*\s+(de\s+)?liquido|saindo\s+(agua|liquido)"
        ),
    ),
    ("inchaco", re.compile(r"inchad|inchaco")),
    ("contracoes", re.compile(r"contrac\w*\s+(\w+\s+){0,2}(fort|dolorosa|frequente)")),
    ("febre_gestacao", re.compile(r"\bfebre\b")),
)

_PREGNANCY_ONLY = frozenset({"febre_gestacao"})
_REQUIRES_BODY_PART = frozenset({"inchaco"})

_ANSWER_PREGNANT = (
    "Isso pode ser um sinal de alerta na gestação. Procure **agora** a maternidade de "
    "referência para atendimento de urgência/emergência. Se não conseguir se deslocar ou se "
    "os sintomas piorarem, ligue **192 (SAMU)**.\n\n"
    "Esta orientação não substitui a avaliação de um profissional de saúde."
)
_ANSWER_GENERAL = (
    "Isso pode precisar de atendimento imediato. Procure uma **UPA** ou pronto-atendimento. "
    "Em caso de emergência, ligue **192 (SAMU)**.\n\n"
    "Esta orientação não substitui a avaliação de um profissional de saúde."
)


@dataclass(frozen=True, slots=True)
class TriageResult:
    triggered: bool
    rule_id: str | None = None
    pregnancy_context: bool = False
    answer: str = ""


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", stripped)


def triage_message(message: str) -> TriageResult:
    text = normalize_text(message)
    if not _FIRST_PERSON.search(text):
        return TriageResult(triggered=False)

    pregnancy = bool(_PREGNANCY.search(text))
    for rule_id, pattern in _RULES:
        if not pattern.search(text):
            continue
        if rule_id in _PREGNANCY_ONLY and not pregnancy:
            continue
        if rule_id in _REQUIRES_BODY_PART and not _BODY_PART.search(text):
            continue
        return TriageResult(
            triggered=True,
            rule_id=rule_id,
            pregnancy_context=pregnancy,
            answer=_ANSWER_PREGNANT if pregnancy else _ANSWER_GENERAL,
        )
    return TriageResult(triggered=False)
