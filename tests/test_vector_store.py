from langchain_core.documents import Document

from app.rag.vector_store import deterministic_point_id


def test_deterministic_point_id_is_stable() -> None:
    document = Document(
        page_content="conteúdo de exemplo",
        metadata={
            "source": "vacinacao/exemplo.pdf",
            "page": 2,
            "start_index": 100,
        },
    )

    assert deterministic_point_id(document) == deterministic_point_id(document)


def test_deterministic_point_id_changes_when_content_changes() -> None:
    first = Document(
        page_content="conteúdo A",
        metadata={"source": "arquivo.pdf", "page": 1, "start_index": 0},
    )
    second = Document(
        page_content="conteúdo B",
        metadata={"source": "arquivo.pdf", "page": 1, "start_index": 0},
    )

    assert deterministic_point_id(first) != deterministic_point_id(second)
