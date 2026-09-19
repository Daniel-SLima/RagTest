from pathlib import Path

from langchain_core.documents import Document

from app.rag.corpus_audit import build_corpus_coverage


def test_corpus_audit_detects_file_without_extractable_text(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    file_path = source_dir / "scan.pdf"
    file_path.write_bytes(b"fake")

    documents = [
        Document(
            page_content="",
            metadata={"source": "scan.pdf", "page": 1},
        ),
        Document(
            page_content="",
            metadata={"source": "scan.pdf", "page": 2},
        ),
    ]

    rows = build_corpus_coverage(
        source_dir,
        [file_path],
        documents,
        [],
    )

    assert len(rows) == 1
    assert rows[0].status == "NO_TEXT"
    assert rows[0].units == 2
    assert rows[0].nonempty_units == 0
    assert rows[0].chunks == 0


def test_corpus_audit_reports_partial_text_and_chunks(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    file_path = source_dir / "mixed.pdf"
    file_path.write_bytes(b"fake")

    documents = [
        Document(
            page_content="conteudo",
            metadata={"source": "mixed.pdf", "page": 1},
        ),
        Document(
            page_content="",
            metadata={"source": "mixed.pdf", "page": 2},
        ),
    ]
    chunks = [
        Document(
            page_content="conteudo",
            metadata={"source": "mixed.pdf", "page": 1},
        )
    ]

    rows = build_corpus_coverage(
        source_dir,
        [file_path],
        documents,
        chunks,
    )

    assert rows[0].status == "PARTIAL_TEXT"
    assert rows[0].text_chars == len("conteudo")
    assert rows[0].chunks == 1
