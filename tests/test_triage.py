import pytest

from app.safety.triage import triage_message


@pytest.mark.parametrize(
    ("message", "rule"),
    [
        ("minha pressão tá alta e eu tô grávida", "pressao_alta"),
        ("estou grávida e com a vista embaçada", "alteracao_visual"),
        ("tô vendo estrelinhas, estou gestante", "alteracao_visual"),
        ("estou com uma dor de cabeça muito forte na gravidez", "cefaleia_forte"),
        ("tô sangrando na gravidez, o que eu faço", "sangramento"),
        ("minha bolsa estourou mas não sinto contração", "perda_liquido"),
        ("estou perdendo líquido pela vagina", "perda_liquido"),
        ("meu pé e meu rosto estão muito inchados na gestação", "inchaco"),
        ("estou com contrações fortes e frequentes", "contracoes"),
        ("estou grávida e com febre", "febre_gestacao"),
    ],
)
def test_triage_detects_alarm_signs(message: str, rule: str) -> None:
    result = triage_message(message)

    assert result.triggered
    assert result.rule_id == rule
    assert "192" in result.answer


def test_triage_sends_pregnant_women_to_maternity() -> None:
    result = triage_message("estou grávida e sangrando")

    assert result.pregnancy_context
    assert "maternidade" in result.answer.lower()


def test_triage_treats_fluid_loss_as_pregnancy_context() -> None:
    result = triage_message("estou perdendo líquido pela vagina")

    assert result.pregnancy_context
    assert "maternidade" in result.answer.lower()


def test_triage_sends_non_pregnant_bleeding_to_upa() -> None:
    result = triage_message("estou sangrando muito")

    assert not result.pregnancy_context
    assert "UPA" in result.answer


@pytest.mark.parametrize(
    "message",
    [
        "com quantos anos tenho que fazer o papanicolau?",
        "o que é sangramento de escape?",
        "quais são os sinais de alerta na gravidez?",
        "estou com febre",
        "como agendo a mamografia",
    ],
)
def test_triage_ignores_non_urgent_or_informational_messages(message: str) -> None:
    result = triage_message(message)

    assert not result.triggered
    assert result.rule_id is None
