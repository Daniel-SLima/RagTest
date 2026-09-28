import json
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path("docs/contrato/openapi-v1.json")


def contract_document() -> dict[str, Any]:
    from app.main import app

    document = dict(app.openapi())
    document["info"] = {"title": "RagTest API", "version": "v1"}
    return document


def render_contract() -> str:
    return json.dumps(contract_document(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
