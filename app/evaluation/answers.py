import csv
from pathlib import Path
from typing import Any

from app.presentation import build_display
from app.rag.chat import ChatResult

RUBRIC_COLUMNS = ("fidelidade_0a2", "relevancia_0a2", "clareza_0a2", "observacao")


def _sources(result: ChatResult) -> str:
    parts = []
    for index, hit in enumerate(result.sources, start=1):
        page = f" p.{hit.page}" if hit.page is not None else ""
        parts.append(f"[{index}] {hit.source}{page}")
    return " | ".join(parts)


def _uncited(result: ChatResult) -> str:
    return " || ".join(
        f"{attempt.stage}: {block}"
        for attempt in result.citation_validation_attempts
        for block in attempt.uncited_blocks
    )


def answer_row(case: dict[str, Any], result: ChatResult, latency_ms: float) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": case.get("id", ""),
        "topic": case.get("topic", ""),
        "query": case.get("query", ""),
        "status": build_display(result).status,
        "grounded": result.grounded,
        "citation_ids": ",".join(str(item) for item in result.citation_ids),
        "retries": result.citation_retry_count,
        "latency_ms": round(latency_ms),
        "model": result.model,
        "answer": result.answer,
        "sources": _sources(result),
        "blocos_sem_citacao": _uncited(result),
        "resposta_rejeitada": next(
            (attempt.answer for attempt in result.citation_validation_attempts if not attempt.valid),
            "",
        ),
    }
    row.update({column: "" for column in RUBRIC_COLUMNS})
    return row


def write_rows_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
