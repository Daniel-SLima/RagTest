from pathlib import Path

from app.rag.loaders import infer_audience


def test_infer_audience_from_known_document_paths() -> None:
    assert infer_audience(Path("pessoa_idosa/caderneta.pdf")) == "idoso"
    assert infer_audience(Path("vacinacao/calendario_nacional_vacinacao_idoso.pdf")) == "idoso"
    assert infer_audience(Path("gestacao/caderneta_gestante.pdf")) == "gestante"
    assert infer_audience(Path("vacinacao/calendario_nacional_vacinacao_crianca.pdf")) == "crianca"
    assert (
        infer_audience(Path("vacinacao/calendario_nacional_vacinacao_adolescentes_jovens.pdf"))
        == "adolescente_jovem"
    )
    assert infer_audience(Path("vacinacao/calendario_nacional_vacinacao_adulto.pdf")) == "adulto"


def test_infer_audience_does_not_guess_generic_documents() -> None:
    assert infer_audience(Path("medicamentos/relacao_nacional_medicamentos_2024.pdf")) is None
