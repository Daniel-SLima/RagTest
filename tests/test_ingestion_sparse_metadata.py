from langchain_core.documents import Document

from app.rag.ingestion import build_sparse_index_text


def test_sparse_index_text_includes_metadata_and_content() -> None:
    document = Document(
        page_content="Conteúdo da carta.",
        metadata={
            "source": "direitos_saude/carta_direitos_deveres.pdf",
            "filename": "carta_direitos_deveres.pdf",
            "category": "direitos_saude",
            "audience": "adulto",
        },
    )

    text = build_sparse_index_text(document)

    assert "direitos_saude/carta_direitos_deveres.pdf" in text
    assert "carta_direitos_deveres.pdf" in text
    assert "direitos_saude" in text
    assert "adulto" in text
    assert "Conteúdo da carta." in text
