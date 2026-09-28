import json
from pathlib import Path

import pytest

from app.catalog.services import (
    ServiceCatalogError,
    load_service_catalog,
    render_service_text,
)
from app.rag.loaders import load_source_documents

REAL_CATALOG = Path("data/source/servicos/catalogo_servicos.json")


def _entry(service_id: str = "preventivo") -> dict[str, object]:
    return {
        "id": service_id,
        "nome": "Exame preventivo",
        "sinonimos": ["papanicolau"],
        "audience": "mulher",
        "publico": "25 a 64 anos",
        "periodicidade": "a cada 3 anos",
        "onde": "UBS",
        "como_agendar": "recepção da UBS",
        "documentos": ["Cartão SUS"],
        "preparo": ["evitar duchas vaginais 48 horas antes"],
        "link": {"rotulo": "Ver unidades", "url": "seucuida://unidades"},
        "lembretes": [{"rotulo": "Resultado normal", "dias": 1095}],
        "fontes": [{"titulo": "Diretriz", "orgao": "MS", "ano": 2025}],
    }


def _write(path: Path, entries: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"versao": "teste", "revisado_em": "2026-09-28", "servicos": entries}),
        encoding="utf-8",
    )
    return path


def test_load_service_catalog_validates_entries(tmp_path: Path) -> None:
    catalog = load_service_catalog(_write(tmp_path / "c.json", [_entry()]))

    assert catalog.versao == "teste"
    assert [service.id for service in catalog.servicos] == ["preventivo"]
    assert catalog.get("preventivo").lembretes[0].dias == 1095


def test_load_service_catalog_rejects_duplicated_ids(tmp_path: Path) -> None:
    path = _write(tmp_path / "c.json", [_entry(), _entry()])

    with pytest.raises(ServiceCatalogError):
        load_service_catalog(path)


def test_load_service_catalog_requires_sources(tmp_path: Path) -> None:
    entry = _entry()
    entry["fontes"] = []

    with pytest.raises(ServiceCatalogError):
        load_service_catalog(_write(tmp_path / "c.json", [entry]))


def test_render_service_text_contains_indexable_fields(tmp_path: Path) -> None:
    catalog = load_service_catalog(_write(tmp_path / "c.json", [_entry()]))

    text = render_service_text(catalog.servicos[0])

    for expected in ("Exame preventivo", "papanicolau", "25 a 64 anos", "recepção da UBS", "Diretriz"):
        assert expected in text


def test_loader_turns_catalog_into_one_document_per_service(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    _write(
        source_dir / "servicos" / "catalogo_servicos.json",
        [_entry("preventivo"), _entry("mamografia")],
    )

    report = load_source_documents(source_dir)

    assert report.files_scanned == 1
    assert report.files_loaded == 1
    assert [doc.metadata["service_id"] for doc in report.documents] == [
        "preventivo",
        "mamografia",
    ]
    metadata = report.documents[0].metadata
    assert metadata["source"] == "servicos/catalogo_servicos.json"
    assert metadata["category"] == "servicos"
    assert metadata["doc_type"] == "servico"
    assert metadata["audience"] == "mulher"
    assert metadata["extraction_method"] == "catalog"


def test_real_catalog_covers_core_domain() -> None:
    catalog = load_service_catalog(REAL_CATALOG)

    ids = {service.id for service in catalog.servicos}

    assert {"preventivo", "mamografia", "prenatal", "urgencia_obstetrica"} <= ids
    assert all(service.fontes for service in catalog.servicos)


def test_every_catalog_chunk_keeps_the_service_context() -> None:
    from app.rag.chunking import split_documents

    report = load_source_documents(REAL_CATALOG.parent)
    catalog_docs = [doc for doc in report.documents if doc.metadata.get("doc_type") == "servico"]
    chunks = split_documents(catalog_docs, chunk_size=1000, chunk_overlap=200)

    preventivo = [chunk for chunk in chunks if chunk.metadata["service_id"] == "preventivo"]
    assert len(preventivo) >= 2
    assert all(
        chunk.page_content.startswith("Serviço: Exame preventivo do câncer do colo do útero")
        for chunk in preventivo
    )
    assert all(chunk.metadata["chunk_context"] for chunk in preventivo)
