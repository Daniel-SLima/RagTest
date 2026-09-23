from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import (
    get_embedding_provider,
    get_llm_provider,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.core.config import Settings, get_settings
from app.llm.base import LLMServiceUnavailableError
from app.rag.chat import answer_with_rag
from app.rag.demo_policy import (
    DemoSourcePolicy,
    public_source_from_hit,
    sanitize_runtime_label,
)
from app.rag.diagnostics import DiagnosticsCollector
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.retrieval_profiles import get_profile
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore, SearchHit
from app.schemas.demo import (
    DemoRetrievalRequest,
    DemoRetrievalResponse,
    DemoRunRequest,
    DemoRunResponse,
    DemoRuntimeResponse,
    DemoSource,
    DemoTimings,
)

router = APIRouter(prefix="/v1/demo", tags=["demo"])


def _policy(settings: Settings) -> DemoSourcePolicy:
    return DemoSourcePolicy(settings.demo_allowed_source_prefixes)


def _profile(settings: Settings, requested: str | None):
    try:
        return get_profile(requested or settings.retrieval_mode)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_retrieval_mode", "message": "Unsupported retrieval mode."},
        ) from exc


def _sources(hits: list[SearchHit], *, fusion_available: bool = False) -> list[DemoSource]:
    return [
        public_source_from_hit(
            hit,
            order=index,
            fusion_available=fusion_available,
        )
        for index, hit in enumerate(hits, start=1)
    ]


async def _search(
    request: DemoRetrievalRequest,
    *,
    embeddings: EmbeddingProvider,
    sparse_embeddings: SparseEmbeddingProvider,
    vector_store: QdrantVectorStore,
    settings: Settings,
) -> tuple[list[SearchHit], str, dict[str, float | None]]:
    profile = _profile(settings, request.retrieval_mode)
    collector = DiagnosticsCollector()
    collector.start()
    try:
        hits = await semantic_search(
            request.query,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings if profile.use_sparse else None,
            vector_store=vector_store,
            limit=request.limit,
            category=request.category,
            audience=request.audience,
            min_score=request.min_score,
            candidate_multiplier=profile.candidate_multiplier,
            score_margin=profile.score_margin,
            merge_same_page=settings.retrieval_merge_same_page,
            max_group_chars=settings.retrieval_max_group_chars,
            source_lexical_weight=profile.source_lexical_weight,
            content_lexical_weight=profile.content_lexical_weight,
            hybrid_dense_weight=profile.dense_weight,
            hybrid_sparse_weight=profile.sparse_weight,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "retrieval_unavailable", "message": "Retrieval service unavailable."},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "retrieval_failed", "message": "Retrieval failed."},
        ) from exc
    finally:
        collector.mark_retrieval()
        timings = collector.finish()
    allowed = _policy(settings)
    return [hit for hit in hits if allowed.allows(hit.source)], request.retrieval_mode or profile.name, timings


@router.post("/retrieval", response_model=DemoRetrievalResponse)
async def demo_retrieval(
    request: DemoRetrievalRequest,
    embeddings: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    sparse_embeddings: Annotated[SparseEmbeddingProvider, Depends(get_sparse_embedding_provider)],
    vector_store: Annotated[QdrantVectorStore, Depends(get_vector_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DemoRetrievalResponse:
    hits, mode, timings = await _search(
        request,
        embeddings=embeddings,
        sparse_embeddings=sparse_embeddings,
        vector_store=vector_store,
        settings=settings,
    )
    return DemoRetrievalResponse(
        query=request.query,
        retrieval_mode=mode,
        sources=_sources(hits, fusion_available=mode == "hybrid"),
        timings=DemoTimings(**timings),
    )


@router.post("/run", response_model=DemoRunResponse)
async def demo_run(
    request: DemoRunRequest,
    embeddings: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    sparse_embeddings: Annotated[SparseEmbeddingProvider, Depends(get_sparse_embedding_provider)],
    vector_store: Annotated[QdrantVectorStore, Depends(get_vector_store)],
    settings: Annotated[Settings, Depends(get_settings)],
    request_context: Request,
) -> DemoRunResponse:
    policy = _policy(settings)
    if not policy.prefixes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "source_policy_blocked", "message": "No approved demo sources configured."},
        )
    profile = _profile(settings, request.retrieval_mode)
    collector = DiagnosticsCollector()
    class LazyLLMProvider:
        def __init__(self) -> None:
            self._provider: object | None = None

        @property
        def model_name(self) -> str:
            if self._provider is not None:
                return str(getattr(self._provider, "model_name", "configured"))
            return {
                "gemini": settings.gemini_model,
                "groq": settings.groq_model,
                "ollama": settings.ollama_model,
            }.get(settings.llm_provider, "configured")

        async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
            override = request_context.app.dependency_overrides.get(get_llm_provider)
            self._provider = (
                override()
                if override is not None
                else get_llm_provider(request_context, settings)
            )
            return await self._provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

    timings: dict[str, float | None]
    try:
        result = await answer_with_rag(
            request.query,
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings if profile.use_sparse else None,
            vector_store=vector_store,
            llm=LazyLLMProvider(),
            limit=request.limit,
            category=request.category,
            audience=request.audience,
            min_score=request.min_score,
            candidate_multiplier=profile.candidate_multiplier,
            score_margin=profile.score_margin,
            merge_same_page=settings.retrieval_merge_same_page,
            max_group_chars=settings.retrieval_max_group_chars,
            source_lexical_weight=profile.source_lexical_weight,
            content_lexical_weight=profile.content_lexical_weight,
            hybrid_dense_weight=profile.dense_weight,
            hybrid_sparse_weight=profile.sparse_weight,
            auto_decompose=False,
            source_policy=lambda hit: policy.allows(hit.source),
            diagnostics=collector,
        )
    except LLMServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "generation_unavailable", "message": "Generation service unavailable."},
        ) from exc
    except HTTPException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "generation_unavailable", "message": "Generation service unavailable."},
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "retrieval_unavailable", "message": "RAG service unavailable."},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "generation_failed", "message": "Generation failed."},
        ) from exc
    finally:
        timings = collector.finish()
    if not result.sources:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "source_policy_blocked", "message": "No approved sources available."},
        )
    return DemoRunResponse(
        answer=result.answer,
        model=sanitize_runtime_label(result.model),
        grounded=result.grounded,
        citation_ids=result.citation_ids,
        sources=_sources(result.sources, fusion_available=profile.use_sparse),
        timings=DemoTimings(**timings),
    )


@router.get("/runtime", response_model=DemoRuntimeResponse)
async def demo_runtime(settings: Annotated[Settings, Depends(get_settings)]) -> DemoRuntimeResponse:
    policy = _policy(settings)
    model = {
        "gemini": settings.gemini_model,
        "groq": settings.groq_model,
        "ollama": settings.ollama_model,
    }.get(settings.llm_provider, "configured")
    return DemoRuntimeResponse(
        version=sanitize_runtime_label(settings.app_version),
        provider=sanitize_runtime_label(settings.llm_provider),
        model=sanitize_runtime_label(model),
        embedding=sanitize_runtime_label(settings.embedding_model),
        retrieval=settings.retrieval_mode,
        collection=sanitize_runtime_label(settings.qdrant_collection),
        demo_enabled=settings.demo_enabled,
        policy_id=policy.policy_id,
        policy_status="configured" if policy.prefixes else "blocked",
    )
