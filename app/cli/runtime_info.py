import argparse
import asyncio
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from app.core.config import get_settings
from app.services.qdrant_service import QdrantService


def _package_version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "not-installed"


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _collection_lines(info: Any) -> list[str]:
    lines: list[str] = []
    params = info.config.params
    vectors = params.vectors
    sparse_vectors = params.sparse_vectors or {}

    if isinstance(vectors, dict):
        for name, vector_params in sorted(vectors.items()):
            lines.append(
                "  dense "
                f"{name}: size={vector_params.size} "
                f"distance={_enum_value(vector_params.distance)}"
            )
    else:
        lines.append(
            "  dense default: "
            f"size={getattr(vectors, 'size', '?')} "
            f"distance={_enum_value(getattr(vectors, 'distance', '?'))}"
        )

    for name, sparse_params in sorted(sparse_vectors.items()):
        modifier = getattr(sparse_params, "modifier", None)
        modifier_text = _enum_value(modifier) if modifier is not None else "none"
        lines.append(f"  sparse {name}: modifier={modifier_text}")

    metadata = getattr(info.config, "metadata", None)
    lines.append(f"  metadata: {metadata or '-'}")
    lines.append(f"  points_count: {getattr(info, 'points_count', None)}")
    lines.append(
        "  indexed_vectors_count: "
        f"{getattr(info, 'indexed_vectors_count', None)}"
    )
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a reproducibility fingerprint for the RagTest runtime."
    )
    parser.add_argument(
        "--skip-qdrant",
        action="store_true",
        help="Print package/config information without connecting to Qdrant.",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    settings = get_settings()

    print("RagTest runtime fingerprint")
    print(f"app_version: {settings.app_version}")
    print(f"python_package_ragtest: {_package_version('ragtest')}")
    print(f"fastembed: {_package_version('fastembed')}")
    print(f"qdrant-client: {_package_version('qdrant-client')}")
    print(f"google-genai: {_package_version('google-genai')}")
    print(f"fastapi: {_package_version('fastapi')}")
    print(f"pymupdf: {_package_version('pymupdf')}")
    print(f"pypdf: {_package_version('pypdf')}")
    print(f"embedding_model: {settings.embedding_model}")
    print(f"sparse_embedding_model: {settings.sparse_embedding_model}")
    print(f"sparse_embedding_language: {settings.sparse_embedding_language}")
    print(f"retrieval_mode: {settings.retrieval_mode}")
    print(f"chunk_size: {settings.chunk_size}")
    print(f"chunk_overlap: {settings.chunk_overlap}")
    print(f"collection: {settings.qdrant_collection}")

    if args.skip_qdrant:
        print("qdrant_server: skipped")
        return

    qdrant = QdrantService(settings)
    try:
        server_info = await qdrant.client.info()
        print(f"qdrant_server: {server_info.version}")
        print(f"qdrant_commit: {server_info.commit or '-'}")

        exists = await qdrant.client.collection_exists(settings.qdrant_collection)
        print(f"collection_exists: {'yes' if exists else 'no'}")
        if exists:
            info = await qdrant.client.get_collection(settings.qdrant_collection)
            print("collection_config:")
            for line in _collection_lines(info):
                print(line)
    finally:
        await qdrant.close()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
