import csv
from pathlib import Path

from app.evaluation.answers import RUBRIC_COLUMNS, answer_row, write_rows_csv
from app.rag.chat import ChatResult
from app.rag.vector_store import SearchHit
from app.safety.triage import triage_message


def _hit(source: str) -> SearchHit:
    return SearchHit(
        id="1", score=0.5, content="c", source=source, category=None,
        audience=None, page=3, metadata={},
    )


def test_answer_row_flattens_result_and_leaves_rubric_blank() -> None:
    result = ChatResult(
        answer="Resposta [1].", sources=[_hit("chatscm/chatscm.docx")], model="m",
        grounded=True, citation_ids=[1], citation_retry_count=1,
    )

    row = answer_row(
        {"id": "v2-dev-x", "topic": "rastreamento", "query": "pergunta"}, result, 1234.4
    )

    assert row["id"] == "v2-dev-x"
    assert row["status"] == "verified"
    assert row["citation_ids"] == "1"
    assert row["retries"] == 1
    assert row["latency_ms"] == 1234
    assert row["sources"] == "[1] chatscm/chatscm.docx p.3"
    assert all(row[column] == "" for column in RUBRIC_COLUMNS)
    assert row["blocos_sem_citacao"] == ""


def test_answer_row_lists_uncited_blocks_from_all_attempts() -> None:
    from app.rag.chat import CitationValidationAttempt

    attempt = CitationValidationAttempt(
        stage="initial", valid=False, syntax_valid=True, total_claim_blocks=2,
        cited_claim_blocks=1, uncited_claim_blocks=1, coverage=0.5,
        reason="x", uncited_blocks=("Bloco sem fonte.",), answer="Resposta bruta.",
    )
    result = ChatResult(
        answer="fallback", sources=[], model="m", grounded=False, citation_ids=[],
        citation_validation_attempts=(attempt,),
    )

    row = answer_row({"id": "a", "query": "q"}, result, 1.0)

    assert row["blocos_sem_citacao"] == "initial: Bloco sem fonte."
    assert row["resposta_rejeitada"] == "Resposta bruta."


def test_select_cases_filters_by_id() -> None:
    from app.cli.collect_answers import select_cases

    cases = [{"id": "a"}, {"id": "b"}, {"id": "c"}]

    assert select_cases(cases, ["c", "a"]) == [{"id": "a"}, {"id": "c"}]
    assert select_cases(cases, None) == cases


def test_answer_row_marks_triage() -> None:
    result = ChatResult(
        answer="x", sources=[], model="triagem-deterministica", grounded=False,
        citation_ids=[], safety=triage_message("estou grávida e sangrando"),
    )

    assert answer_row({"id": "a", "query": "q"}, result, 1.0)["status"] == "emergency"


def test_write_rows_csv_is_excel_friendly(tmp_path: Path) -> None:
    path = tmp_path / "respostas.csv"
    write_rows_csv([{"id": "a", "answer": "ção"}], path)

    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    assert rows == [{"id": "a", "answer": "ção"}]
