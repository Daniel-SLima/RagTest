from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.catalog.services import load_catalog_or_none
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
