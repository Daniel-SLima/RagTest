import pytest
from langchain_core.documents import Document

from app.rag.chunking import split_documents


def test_split_documents_preserves_metadata_and_adds_start_index() -> None:
    documents = [
        Document(
            page_content="A" * 80 + " " + "B" * 80,
            metadata={"source": "vacinacao/exemplo.pdf", "page": 2},
        )
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=20)

    assert len(chunks) >= 2
    assert all(chunk.metadata["source"] == "vacinacao/exemplo.pdf" for chunk in chunks)
    assert all(chunk.metadata["page"] == 2 for chunk in chunks)
    assert all("start_index" in chunk.metadata for chunk in chunks)


def test_split_documents_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="smaller than chunk_size"):
        split_documents([], chunk_size=100, chunk_overlap=100)
