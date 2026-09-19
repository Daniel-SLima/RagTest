from fastapi import Request

from app.services.qdrant_service import QdrantService


def get_qdrant_service(request: Request) -> QdrantService:
    service = getattr(request.app.state, "qdrant", None)
    if service is None:
        raise RuntimeError("Qdrant service was not initialized")
    return service
