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
            metadata={
                "source": "scan.pdf",
                "page": 1,
                "extraction_method": "empty",
            },
        ),
        Document(
            page_content="",
            metadata={
                "source": "scan.pdf",
                "page": 2,
                "extraction_method": "empty",
            },
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
    assert rows[0].ocr_units == 0
    assert rows[0].chunks == 0


def test_corpus_audit_counts_ocr_units(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    file_path = source_dir / "scan.pdf"
    file_path.write_bytes(b"fake")

    documents = [
        Document(
            page_content="texto reconhecido",
            metadata={
                "source": "scan.pdf",
                "page": 1,
                "extraction_method": "ocr",
            },
        )
    ]
    chunks = [
        Document(
            page_content="texto reconhecido",
            metadata={"source": "scan.pdf", "page": 1},
        )
    ]

    rows = build_corpus_coverage(
        source_dir,
        [file_path],
        documents,
        chunks,
    )

    assert rows[0].status == "OK"
    assert rows[0].ocr_units == 1
    assert rows[0].text_chars == len("texto reconhecido")
    assert rows[0].chunks == 1
