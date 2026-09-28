import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator


class ServiceCatalogError(ValueError):
    pass


class ServiceLink(BaseModel):
    rotulo: str
    url: str


class ServiceReminder(BaseModel):
    rotulo: str
    dias: int = Field(gt=0)


class ServiceSource(BaseModel):
    titulo: str
    orgao: str
    ano: int
    url: str | None = None


class ServiceEntry(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    nome: str
    sinonimos: list[str] = Field(default_factory=list)
    audience: str
    publico: str
    periodicidade: str | None = None
    onde: str
    como_agendar: str
    documentos: list[str] = Field(default_factory=list)
    preparo: list[str] = Field(default_factory=list)
    sinais_alarme: list[str] = Field(default_factory=list)
    telefone_emergencia: str | None = None
    observacoes: list[str] = Field(default_factory=list)
    link: ServiceLink | None = None
    lembretes: list[ServiceReminder] = Field(default_factory=list)
    fontes: list[ServiceSource]

    @field_validator("fontes")
    @classmethod
    def _requires_sources(cls, value: list[ServiceSource]) -> list[ServiceSource]:
        if not value:
            raise ValueError("cada serviço precisa de ao menos uma fonte")
        return value


class Suggestion(BaseModel):
    texto: str = Field(min_length=3)
    topico: str | None = None


class ServiceCatalog(BaseModel):
    versao: str
    revisado_em: str
    aviso: str | None = None
    sugestoes: list[Suggestion] = Field(default_factory=list)
    servicos: list[ServiceEntry]

    def get(self, service_id: str) -> ServiceEntry:
        for service in self.servicos:
            if service.id == service_id:
                return service
        raise KeyError(service_id)


def load_service_catalog(path: Path) -> ServiceCatalog:
    try:
        catalog = ServiceCatalog.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ServiceCatalogError(f"catálogo inválido: {path.name}") from exc

    ids = [service.id for service in catalog.servicos]
    if len(ids) != len(set(ids)):
        raise ServiceCatalogError("ids de serviço duplicados no catálogo")
    return catalog


def _section(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return [f"{title}:", *(f"- {item}" for item in items)]


def render_service_text(service: ServiceEntry) -> str:
    lines = [f"Serviço: {service.nome}"]
    if service.sinonimos:
        lines.append(f"Também chamado de: {', '.join(service.sinonimos)}")
    lines.append(f"Para quem: {service.publico}")
    if service.periodicidade:
        lines.append(f"Periodicidade: {service.periodicidade}")
    lines.append(f"Onde: {service.onde}")
    lines.append(f"Como agendar: {service.como_agendar}")
    lines += _section("Documentos", service.documentos)
    lines += _section("Preparo", service.preparo)
    lines += _section("Sinais de alarme", service.sinais_alarme)
    if service.telefone_emergencia:
        lines.append(f"Telefone de emergência: {service.telefone_emergencia}")
    lines += _section("Observações", service.observacoes)
    lines.append(
        "Fontes: "
        + "; ".join(f"{source.titulo} ({source.orgao}, {source.ano})" for source in service.fontes)
    )
    return "\n".join(lines)


DEFAULT_CATALOG_RELATIVE_PATH = Path("servicos/catalogo_servicos.json")


def load_catalog_or_none(source_dir: Path) -> ServiceCatalog | None:
    path = source_dir / DEFAULT_CATALOG_RELATIVE_PATH
    if not path.is_file():
        return None
    try:
        return load_service_catalog(path)
    except ServiceCatalogError:
        return None
