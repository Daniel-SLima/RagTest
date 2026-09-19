from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_qdrant_service
from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.qdrant_service import QdrantService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness check")
async def ready(
    qdrant: Annotated[QdrantService, Depends(get_qdrant_service)],
) -> ReadinessResponse:
    if not await qdrant.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Qdrant is unavailable",
        )

    return ReadinessResponse(dependencies={"qdrant": "ok"})
