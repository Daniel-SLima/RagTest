from dataclasses import dataclass
from typing import Literal

from app.catalog.services import ServiceCatalog
from app.rag.chat import ChatResult

ActionType = Literal["open_link", "schedule_reminder", "call_emergency"]

EMERGENCY_LABEL = "Ligar para o SAMU (192)"
EMERGENCY_URL = "tel:192"


@dataclass(frozen=True, slots=True)
class SuggestedAction:
    type: ActionType
    label: str
    url: str | None = None
    service_id: str | None = None
    suggested_in_days: int | None = None


def _emergency() -> SuggestedAction:
    return SuggestedAction(type="call_emergency", label=EMERGENCY_LABEL, url=EMERGENCY_URL)


def _cited_service_ids(result: ChatResult) -> list[str]:
    service_ids: list[str] = []
    for citation_id in result.citation_ids:
        if not 1 <= citation_id <= len(result.sources):
            continue
        service_id = result.sources[citation_id - 1].metadata.get("service_id")
        if isinstance(service_id, str) and service_id not in service_ids:
            service_ids.append(service_id)
    return service_ids


def build_actions(result: ChatResult, catalog: ServiceCatalog | None) -> list[SuggestedAction]:
    if result.safety is not None and result.safety.triggered:
        return [_emergency()]
    if not result.grounded or catalog is None:
        return []

    actions: list[SuggestedAction] = []
    for service_id in _cited_service_ids(result):
        try:
            service = catalog.get(service_id)
        except KeyError:
            continue
        if service.telefone_emergencia:
            actions.append(_emergency())
            continue
        if service.link is not None:
            actions.append(
                SuggestedAction(
                    type="open_link",
                    label=service.link.rotulo,
                    url=service.link.url,
                    service_id=service.id,
                )
            )
        actions.extend(
            SuggestedAction(
                type="schedule_reminder",
                label=reminder.rotulo,
                service_id=service.id,
                suggested_in_days=reminder.dias,
            )
            for reminder in service.lembretes
        )
    return actions
