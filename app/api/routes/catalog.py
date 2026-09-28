from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.catalog.services import ServiceCatalog, ServiceEntry, load_catalog_or_none
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["catalog"])

DEFAULT_SUGGESTIONS = (
    ("Quando devo fazer o preventivo?", "rastreamento"),
    ("Como agendo a mamografia?", "agendamento"),
    ("Estou grávida, e agora?", "gestacao"),
)


class SuggestionItem(BaseModel):
    text: str
    topic: str | None = None


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]


class ServiceLinkOut(BaseModel):
    label: str
    url: str


class ServiceReminderOut(BaseModel):
    label: str
    days: int


class ServiceSourceOut(BaseModel):
    title: str
    publisher: str
    year: int
    url: str | None = None


class ServiceSummary(BaseModel):
    id: str
    name: str
    audience: str
    link: ServiceLinkOut | None = None


class ServiceDetail(ServiceSummary):
    synonyms: list[str]
    who: str
    frequency: str | None = None
    where: str
    how_to_schedule: str
    documents: list[str]
    preparation: list[str]
    alarm_signs: list[str]
    emergency_phone: str | None = None
    notes: list[str]
    reminders: list[ServiceReminderOut]
    sources: list[ServiceSourceOut]


class ServicesResponse(BaseModel):
    catalog_version: str
    reviewed_at: str
    notice: str | None = None
    services: list[ServiceSummary]


def _catalog(settings: Settings) -> ServiceCatalog:
    catalog = load_catalog_or_none(settings.source_dir)
    if catalog is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service catalog unavailable.",
        )
    return catalog


def _link(service: ServiceEntry) -> ServiceLinkOut | None:
    if service.link is None:
        return None
    return ServiceLinkOut(label=service.link.rotulo, url=service.link.url)


def _summary(service: ServiceEntry) -> ServiceSummary:
    return ServiceSummary(
        id=service.id, name=service.nome, audience=service.audience, link=_link(service)
    )


def _detail(service: ServiceEntry) -> ServiceDetail:
    return ServiceDetail(
        id=service.id,
        name=service.nome,
        audience=service.audience,
        link=_link(service),
        synonyms=service.sinonimos,
        who=service.publico,
        frequency=service.periodicidade,
        where=service.onde,
        how_to_schedule=service.como_agendar,
        documents=service.documentos,
        preparation=service.preparo,
        alarm_signs=service.sinais_alarme,
        emergency_phone=service.telefone_emergencia,
        notes=service.observacoes,
        reminders=[
            ServiceReminderOut(label=item.rotulo, days=item.dias) for item in service.lembretes
        ],
        sources=[
            ServiceSourceOut(title=item.titulo, publisher=item.orgao, year=item.ano, url=item.url)
            for item in service.fontes
        ],
    )


@router.get("/suggestions", response_model=SuggestionsResponse)
async def list_suggestions(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuggestionsResponse:
    catalog = load_catalog_or_none(settings.source_dir)
    if catalog is not None and catalog.sugestoes:
        items = [SuggestionItem(text=item.texto, topic=item.topico) for item in catalog.sugestoes]
    else:
        items = [SuggestionItem(text=text, topic=topic) for text, topic in DEFAULT_SUGGESTIONS]
    return SuggestionsResponse(suggestions=items)


@router.get("/services", response_model=ServicesResponse)
async def list_services(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ServicesResponse:
    catalog = _catalog(settings)
    return ServicesResponse(
        catalog_version=catalog.versao,
        reviewed_at=catalog.revisado_em,
        notice=catalog.aviso,
        services=[_summary(service) for service in catalog.servicos],
    )


@router.get("/services/{service_id}", response_model=ServiceDetail)
async def get_service(
    service_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ServiceDetail:
    try:
        service = _catalog(settings).get(service_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found."
        ) from None
    return _detail(service)
