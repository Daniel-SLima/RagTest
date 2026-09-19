import logging

from qdrant_client import AsyncQdrantClient

from app.core.config import Settings

logger = logging.getLogger(__name__)


class QdrantService:
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=settings.qdrant_timeout_seconds,
        )

    @property
    def client(self) -> AsyncQdrantClient:
        return self._client

    async def is_ready(self) -> bool:
        try:
            await self._client.get_collections()
        except Exception as exc:  # readiness must never crash the API process
            logger.warning("Qdrant readiness check failed: %s", exc)
            return False
        return True

    async def close(self) -> None:
        await self._client.close()
