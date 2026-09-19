from collections import Counter

from app.core.config import get_settings
from app.rag.chunking import split_documents
from app.rag.loaders import load_source_documents


def main() -> None:
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

    print("RagTest document inspection")
    print(f"Source directory : {settings.source_dir}")
    print(f"Files scanned    : {report.files_scanned}")
    print(f"Files loaded     : {report.files_loaded}")
    print(f"Page/doc units   : {len(report.documents)}")
    print(f"Chunks generated : {len(chunks)}")
    print(f"Categories       : {dict(sorted(categories.items()))}")
    print(f"File types       : {dict(sorted(file_types.items()))}")

    if report.errors:
        print("\nLoad errors:")
        for error in report.errors:
            print(f"- {error.source}: {error.message}")


if __name__ == "__main__":
    main()
