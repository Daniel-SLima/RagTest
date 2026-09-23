import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.dependencies import (
    get_embedding_provider,
    get_llm_provider,
    get_sparse_embedding_provider,
    get_vector_store,
)
from app.core.config import Settings
from app.llm.base import LLMServiceUnavailableError
from app.main import create_app
from app.rag.chat import answer_with_rag
from app.rag.demo_policy import (
    DemoSourcePolicy,
    public_source_from_hit,
    sanitize_excerpt,
    sanitize_runtime_label,
)
from app.rag.diagnostics import DiagnosticsCollector
from app.rag.vector_store import SearchHit
from app.schemas.demo import DemoRetrievalRequest, DemoScore


def test_demo_is_disabled_by_default_and_routes_are_not_in_openapi() -> None:
    application = create_app(Settings(_env_file=None))

    paths = application.openapi()["paths"]

    assert Settings(_env_file=None).demo_enabled is False
    assert "/v1/chat" in paths
    assert "/v1/search" in paths
    assert "/v1/sessions" in paths
    assert "/v1/demo/run" not in paths
    assert "/v1/demo/retrieval" not in paths
    assert "/v1/demo/runtime" not in paths


def test_demo_routes_are_registered_only_when_enabled() -> None:
    application = create_app(
        Settings(
            _env_file=None,
            demo_enabled=True,
            demo_allowed_source_prefixes="vacinacao/",
        )
    )

    paths = application.openapi()["paths"]

    assert "/v1/demo/run" in paths
    assert "/v1/demo/retrieval" in paths
    assert "/v1/demo/runtime" in paths


def test_demo_dtos_forbid_extra_fields_and_retrieval_mode_is_closed() -> None:
    with pytest.raises(ValidationError):
        DemoScore(dense_score=0.1, unexpected=1)  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        DemoRetrievalRequest(query="vacinas", retrieval_mode="unsupported")  # type: ignore[arg-type]


def test_invalid_demo_retrieval_mode_is_rejected_before_pipeline() -> None:
    application = create_app(
        Settings(
            _env_file=None,
            demo_enabled=True,
            demo_allowed_source_prefixes="vacinacao/",
        )
    )
    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _AllowedStore()
    client = TestClient(application)
    try:
        response = client.post(
            "/v1/demo/retrieval",
            json={"query": "vacinas", "retrieval_mode": "unsupported"},
        )
    finally:
        client.close()

    assert response.status_code == 422


def test_demo_source_policy_is_positive_fail_closed_and_blocks_chatscm() -> None:
    policy = DemoSourcePolicy("vacinacao/")

    assert policy.allows("vacinacao/guia.pdf") is True
    assert policy.allows("CHATSCM/roteiro.docx") is False
    assert policy.allows("privado/guia.pdf") is False
    assert policy.allows("desconhecido/guia.pdf") is False
    assert DemoSourcePolicy("").allows("vacinacao/guia.pdf") is False


@pytest.mark.parametrize(
    "prefix",
    ["/", ".", "..", "/vacinacao", "C:\\docs\\vacinacao", "\\\\server\\share"],
)
def test_demo_source_policy_rejects_unsafe_prefixes(prefix: str) -> None:
    assert DemoSourcePolicy(prefix).allows("vacinacao/guia.pdf") is False


@pytest.mark.parametrize(
    "source",
    [
        "vacinacao/../outro.pdf",
        "./vacinacao/guia.pdf",
        "/data/source/vacinacao/guia.pdf",
        "C:\\data\\vacinacao\\guia.pdf",
        "\\\\server\\share\\vacinacao\\guia.pdf",
        "vacinacao-secrets/guia.pdf",
    ],
)
def test_demo_source_policy_rejects_traversal_absolute_and_boundary_sources(source: str) -> None:
    assert DemoSourcePolicy("vacinacao/").allows(source) is False


@pytest.mark.parametrize("value", ["c:/docs/vacinacao", "C:/docs/vacinacao", "D:\\docs\\vacinacao"])
def test_demo_source_policy_rejects_drive_paths_in_any_case(value: str) -> None:
    assert DemoSourcePolicy(value).allows("vacinacao/guia.pdf") is False
    assert DemoSourcePolicy("vacinacao/").allows(value + "/guia.pdf") is False


def test_demo_sanitizers_redact_credentials_paths_and_urls() -> None:
    value = (
        "Authorization: Bearer abc123 Basic dXNlcjpwYXNz token abc123 "
        "password=pass secret: value /Users/Ana/file.txt C:\\Users\\Ana\\file.txt "
        "\\\\server\\share\\file.txt https://example.test/private"
    )

    sanitized = sanitize_excerpt(value)
    runtime = sanitize_runtime_label(value)

    for secret in ("abc123", "dXNlcjpwYXNz", "pass", "value", "/Users/Ana", "C:\\Users", "example.test"):
        assert secret not in sanitized
    assert runtime == "configured"


def test_demo_sanitizers_redact_marker_variants_and_rooted_paths() -> None:
    value = (
        "Bearer: bearer-value Basic: basic-value access_token=access-value "
        "refresh_token=refresh-value client_secret=client-value .env.production=env-value "
        "C:\\Users\\Ana\\My Secret\\file.txt \\rooted\\private file.txt "
        "/Users/Ana/My Private/file.txt"
    )

    sanitized = sanitize_excerpt(value)

    for secret in (
        "bearer-value",
        "basic-value",
        "access-value",
        "refresh-value",
        "client-value",
        "env-value",
        "My Secret",
        "private file.txt",
        "/Users/Ana",
    ):
        assert secret not in sanitized
    assert sanitize_runtime_label(value) == "configured"


@pytest.mark.parametrize("value", ["/var/lib/model", "C:/Users/Ana/model", "https://example.test/model"])
def test_runtime_labels_redact_absolute_paths_and_urls(value: str) -> None:
    assert sanitize_runtime_label(value) == "configured"


def test_public_source_sanitizes_metadata_and_excerpt() -> None:
    hit = SearchHit(
        id="internal-id",
        score=0.7,
        dense_score=None,
        sparse_score=0.4,
        rank_score=None,
        content=(
            "  Informação\ncom token=super-secret e C:\\Users\\Ana\\arquivo.pdf "
            "SYSTEM_PROMPT=hidden Traceback (most recent call last) hidden  "
        ),
        source="vacinacao/guia.pdf",
        category="vacinacao",
        audience=None,
        page=2,
        metadata={"private_path": "C:\\Users\\Ana", "api_key": "secret"},
    )

    source = public_source_from_hit(hit, order=1)

    assert source.public_id.startswith("src_")
    assert source.document == "guia.pdf"
    assert source.order == 1
    assert source.scores.dense_score is None
    assert "super-secret" not in source.excerpt
    assert "C:\\Users" not in source.excerpt
    assert "hidden" not in source.excerpt
    assert "private_path" not in source.model_dump()


def test_diagnostics_uses_monotonic_timings_only() -> None:
    collector = DiagnosticsCollector()
    collector.start()
    collector.mark_retrieval()
    collector.mark_generation()
    timings = collector.finish()

    assert set(timings) == {"retrieval_ms", "generation_ms", "total_ms"}
    assert all(value >= 0 for value in timings.values())


def test_disabled_demo_returns_404_without_openapi_registration() -> None:
    application = create_app(Settings(_env_file=None))
    client = TestClient(application)
    try:
        assert client.get("/v1/demo/runtime").status_code == 404
    finally:
        client.close()


class _FakeEmbeddings:
    async def embed_query(self, query: str) -> list[float]:
        return [1.0]


class _FakeStore:
    async def search(self, query_vector: list[float], **kwargs: object) -> list[SearchHit]:
        return [
            SearchHit(
                id="private",
                score=0.9,
                content="private content",
                source="CHATSCM/roteiro.docx",
                category=None,
                audience=None,
                page=1,
                metadata={"secret": "must not leak"},
            )
        ]


class _AllowedStore:
    async def search(self, query_vector: list[float], **kwargs: object) -> list[SearchHit]:
        return [
            SearchHit(
                id="approved",
                score=0.9,
                content="Informação aprovada [1].",
                source="vacinacao/guia.pdf",
                category="vacinacao",
                audience=None,
                page=1,
                metadata={"arbitrary": "hidden"},
            )
        ]


class _FailingStore:
    async def search(self, query_vector: list[float], **kwargs: object) -> list[SearchHit]:
        raise RuntimeError("qdrant URL, secret and stack trace must not leak")


class _FakeLLM:
    model_name = "fake-model"

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        assert "Informação aprovada" in user_prompt
        return "A fonte informa vacinação anual contra influenza [1]."


class _FailingLLM:
    model_name = "fake-model"

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise LLMServiceUnavailableError("provider token must not leak")


def test_blocked_demo_run_does_not_construct_or_call_provider() -> None:
    application = create_app(
        Settings(
            _env_file=None,
            demo_enabled=True,
            demo_allowed_source_prefixes="vacinacao/",
        )
    )

    def forbidden_provider(*args: object, **kwargs: object) -> object:
        raise AssertionError("provider must not be constructed for blocked sources")

    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _FakeStore()
    application.dependency_overrides[get_llm_provider] = lambda: forbidden_provider()

    client = TestClient(application)
    try:
        response = client.post("/v1/demo/run", json={"query": "pergunta"})
    finally:
        client.close()

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "source_policy_blocked"


def test_demo_run_uses_real_pipeline_without_mutating_global_retrieval_mode() -> None:
    settings = Settings(
        _env_file=None,
        demo_enabled=True,
        demo_allowed_source_prefixes="vacinacao/",
        retrieval_mode="dense-rerank",
    )
    application = create_app(settings)
    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _AllowedStore()
    application.dependency_overrides[get_llm_provider] = lambda: _FakeLLM()

    client = TestClient(application)
    try:
        response = client.post(
            "/v1/demo/run",
            json={"query": "pergunta", "retrieval_mode": "dense"},
        )
    finally:
        client.close()

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "fake-model"
    assert body["sources"][0]["scores"]["fusion_score"] is None
    assert set(body["timings"]) == {"retrieval_ms", "generation_ms", "total_ms"}
    assert settings.retrieval_mode == "dense-rerank"


def test_demo_runtime_is_sanitized_and_retrieval_has_no_provider_dependency() -> None:
    settings = Settings(
        _env_file=None,
        demo_enabled=True,
        demo_allowed_source_prefixes="vacinacao/",
        qdrant_url="http://secret.example",
        qdrant_collection="safe_collection",
    )
    application = create_app(settings)
    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _AllowedStore()
    application.dependency_overrides[get_llm_provider] = lambda: (_ for _ in ()).throw(
        AssertionError("retrieval must not construct provider")
    )

    client = TestClient(application)
    try:
        runtime = client.get("/v1/demo/runtime")
        retrieval = client.post("/v1/demo/retrieval", json={"query": "pergunta"})
    finally:
        client.close()

    assert runtime.status_code == 200
    runtime_body = runtime.json()
    assert "secret.example" not in str(runtime_body)
    assert "http" not in str(runtime_body)
    assert retrieval.status_code == 200
    assert retrieval.json()["sources"][0]["document"] == "guia.pdf"
    assert retrieval.json()["timings"]["generation_ms"] is None


def test_demo_run_model_is_sanitized() -> None:
    class UnsafeModelLLM(_FakeLLM):
        model_name = "C:\\Users\\Ana\\secret-model"

    application = create_app(
        Settings(
            _env_file=None,
            demo_enabled=True,
            demo_allowed_source_prefixes="vacinacao/",
        )
    )
    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _AllowedStore()
    application.dependency_overrides[get_llm_provider] = lambda: UnsafeModelLLM()

    client = TestClient(application)
    try:
        response = client.post("/v1/demo/run", json={"query": "pergunta"})
    finally:
        client.close()

    assert response.status_code == 200
    assert response.json()["model"] == "configured"
    assert "Users" not in response.text


def test_demo_validation_error_does_not_echo_extra_secret() -> None:
    application = create_app(
        Settings(
            _env_file=None,
            demo_enabled=True,
            demo_allowed_source_prefixes="vacinacao/",
        )
    )
    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _AllowedStore()
    client = TestClient(application)
    try:
        response = client.post(
            "/v1/demo/retrieval",
            json={"query": "pergunta", "token": "super-secret"},
        )
    finally:
        client.close()

    assert response.status_code == 422
    assert "super-secret" not in response.text
    assert "input" not in response.text
    assert response.json()["detail"]["code"] == "invalid_demo_request"


def test_normal_route_validation_contract_remains_default() -> None:
    application = create_app(Settings(_env_file=None, demo_enabled=True))
    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _AllowedStore()
    client = TestClient(application)
    try:
        response = client.post(
            "/v1/search",
            json={"query": "pergunta", "token": "secret"},
        )
    finally:
        client.close()

    assert response.status_code == 200
    assert "token" not in response.text
    assert "invalid_demo_request" not in response.text


def test_demo_retrieval_error_has_stable_sanitized_code() -> None:
    application = create_app(
        Settings(
            _env_file=None,
            demo_enabled=True,
            demo_allowed_source_prefixes="vacinacao/",
        )
    )
    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _FailingStore()

    client = TestClient(application)
    try:
        response = client.post("/v1/demo/retrieval", json={"query": "pergunta"})
    finally:
        client.close()

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "retrieval_unavailable",
            "message": "Retrieval service unavailable.",
        }
    }
    assert "qdrant URL" not in response.text


def test_demo_provider_error_has_stable_sanitized_code() -> None:
    application = create_app(
        Settings(
            _env_file=None,
            demo_enabled=True,
            demo_allowed_source_prefixes="vacinacao/",
        )
    )
    application.dependency_overrides[get_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_sparse_embedding_provider] = lambda: _FakeEmbeddings()
    application.dependency_overrides[get_vector_store] = lambda: _AllowedStore()
    application.dependency_overrides[get_llm_provider] = lambda: _FailingLLM()

    client = TestClient(application)
    try:
        response = client.post("/v1/demo/run", json={"query": "pergunta"})
    finally:
        client.close()

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "generation_unavailable"
    assert "provider token" not in response.text


@pytest.mark.asyncio
async def test_real_chat_pipeline_accepts_optional_policy_and_collector() -> None:
    collector = DiagnosticsCollector()
    result = await answer_with_rag(
        "pergunta",
        embeddings=_FakeEmbeddings(),
        vector_store=_AllowedStore(),
        llm=_FakeLLM(),
        auto_decompose=False,
        source_policy=lambda hit: hit.source.startswith("vacinacao/"),
        diagnostics=collector,
    )

    timings = collector.finish()
    assert result.grounded is True
    assert result.sources[0].source == "vacinacao/guia.pdf"
    assert set(timings) == {"retrieval_ms", "generation_ms", "total_ms"}
