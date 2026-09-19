from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document


@dataclass(slots=True)
class CorpusCoverage:
    source: str
    units: int
    nonempty_units: int
    text_chars: int
    chunks: int

    @property
    def status(self) -> str:
        if self.units == 0:
            return "NO_UNITS"
        if self.text_chars == 0:
            return "NO_TEXT"
        if self.chunks == 0:
            return "NO_CHUNKS"
        if self.nonempty_units < self.units:
            return "PARTIAL_TEXT"
        return "OK"


def build_corpus_coverage(
    source_dir: Path,
    source_files: list[Path],
    documents: list[Document],
    chunks: list[Document],
) -> list[CorpusCoverage]:
    source_dir = source_dir.resolve()

    units = Counter(str(document.metadata.get("source", "")) for document in documents)
    nonempty_units = Counter(
        str(document.metadata.get("source", ""))
        for document in documents
        if document.page_content.strip()
    )
    text_chars: Counter[str] = Counter()
    for document in documents:
        source = str(document.metadata.get("source", ""))
        text_chars[source] += len(document.page_content.strip())

    chunk_counts = Counter(str(chunk.metadata.get("source", "")) for chunk in chunks)

    rows: list[CorpusCoverage] = []
    for path in sorted(source_files):
        source = path.resolve().relative_to(source_dir).as_posix()
        rows.append(
            CorpusCoverage(
                source=source,
                units=units[source],
                nonempty_units=nonempty_units[source],
                text_chars=text_chars[source],
                chunks=chunk_counts[source],
            )
        )

    return rows
