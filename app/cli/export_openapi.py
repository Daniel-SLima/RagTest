import argparse
from pathlib import Path

from app.contract.openapi import CONTRACT_PATH, render_contract


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta o contrato OpenAPI congelado da API v1.")
    parser.add_argument("--output", type=Path, default=CONTRACT_PATH)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_contract(), encoding="utf-8")
    print(f"Contrato salvo em {args.output}")
