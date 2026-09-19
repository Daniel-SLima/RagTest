import argparse
from collections import Counter

from app.core.config import get_settings
from app.rag.chunking import split_documents
from app.rag.corpus_audit import build_corpus_coverage
from app.rag.loaders import discover_source_files, load_source_documents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect RagTest source documents and extraction coverage."
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Optional substring to filter the per-file coverage output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    report = load_source_documents(settings.source_dir)
    chunks = split_documents(
        report.documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    categories = Counter(
        document.metadata.get("category", "unknown") for document in report.documents
    )
    file_types = Counter(
        document.metadata.get("file_type", "unknown") for document in report.documents
    )

    source_files = discover_source_files(settings.source_dir.resolve())
    coverage = build_corpus_coverage(
        settings.source_dir,
        source_files,
        report.documents,
        chunks,
    )

    print("RagTest document inspection")
    print(f"Source directory : {settings.source_dir}")
    print(f"Files scanned    : {report.files_scanned}")
    print(f"Files loaded     : {report.files_loaded}")
    print(f"Page/doc units   : {len(report.documents)}")
    print(f"Chunks generated : {len(chunks)}")
    print(f"Categories       : {dict(sorted(categories.items()))}")
    print(f"File types       : {dict(sorted(file_types.items()))}")

    print("\nPer-file extraction coverage:")
    print("STATUS        UNITS  TEXT  CHARS      CHUNKS  SOURCE")
    for row in coverage:
        if args.source and args.source.lower() not in row.source.lower():
            continue
        print(
            f"{row.status:<13} "
            f"{row.units:>5}  "
            f"{row.nonempty_units:>4}  "
            f"{row.text_chars:>9}  "
            f"{row.chunks:>6}  "
            f"{row.source}"
        )

    problems = [row for row in coverage if row.status != "OK"]
    print()
    print(f"Files with extraction warnings: {len(problems)}")
    for row in problems:
        print(
            f"- {row.status}: {row.source} "
            f"(units={row.units}, text_units={row.nonempty_units}, "
            f"chars={row.text_chars}, chunks={row.chunks})"
        )

    if report.errors:
        print("\nLoad errors:")
        for error in report.errors:
            print(f"- {error.source}: {error.message}")


if __name__ == "__main__":
    main()
