from dataclasses import dataclass, field
from pathlib import Path

from docx import Document as DocxDocument
from langchain_core.documents import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


@dataclass(slots=True)
class LoadError:
    source: str
    message: str


@dataclass(slots=True)
class LoadReport:
    documents: list[Document] = field(default_factory=list)
    files_scanned: int = 0
    files_loaded: int = 0
    errors: list[LoadError] = field(default_factory=list)


def discover_source_files(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        return []

    return sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def _base_metadata(path: Path, source_dir: Path) -> dict[str, str]:
    relative_path = path.relative_to(source_dir)
    category = relative_path.parts[0] if len(relative_path.parts) > 1 else "uncategorized"
    return {
        "source": relative_path.as_posix(),
        "filename": path.name,
        "category": category,
        "file_type": path.suffix.lower().lstrip("."),
    }


def load_pdf(path: Path, source_dir: Path) -> list[Document]:
    reader = PdfReader(path)
    base_metadata = _base_metadata(path, source_dir)
    documents: list[Document] = []

    for page_number, page in enumerate(reader.pages, start=1):
        documents.append(
            Document(
                page_content=page.extract_text() or "",
                metadata={**base_metadata, "page": page_number},
            )
        )

    return documents


def load_docx(path: Path, source_dir: Path) -> list[Document]:
    document = DocxDocument(path)
    text = "\n".join(
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )

    return [
        Document(
            page_content=text,
            metadata=_base_metadata(path, source_dir),
        )
    ]


def load_source_documents(source_dir: Path) -> LoadReport:
    source_dir = source_dir.resolve()
    files = discover_source_files(source_dir)
    report = LoadReport(files_scanned=len(files))

    for path in files:
        try:
            if path.suffix.lower() == ".pdf":
                loaded = load_pdf(path, source_dir)
            elif path.suffix.lower() == ".docx":
                loaded = load_docx(path, source_dir)
            else:
                continue
        except Exception as exc:
            report.errors.append(
                LoadError(
                    source=path.relative_to(source_dir).as_posix(),
                    message=str(exc),
                )
            )
            continue

        report.documents.extend(loaded)
        report.files_loaded += 1

    return report
