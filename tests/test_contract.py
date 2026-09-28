from app.contract.openapi import CONTRACT_PATH, render_contract

UPDATE_HINT = (
    "O contrato público da API mudou. Se a mudança for intencional, rode "
    "`ragtest-export-openapi`, revise o diff de docs/contrato/openapi-v1.json, "
    "regenere o cliente (`cd frontend && npm run generate:api`) e registre a mudança."
)


def test_openapi_matches_frozen_contract() -> None:
    assert CONTRACT_PATH.read_text(encoding="utf-8") == render_contract(), UPDATE_HINT


def test_contract_exposes_integration_endpoints() -> None:
    paths = set(__import__("json").loads(render_contract())["paths"])

    assert {
        "/v1/chat",
        "/v1/sessions",
        "/v1/sessions/{session_id}",
        "/v1/suggestions",
        "/v1/services",
        "/v1/services/{service_id}",
    } <= paths
