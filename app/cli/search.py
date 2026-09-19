import argparse
import asyncio

from app.core.config import get_settings
from app.rag.embeddings.factory import create_embedding_provider
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run semantic search in RagTest.")
    parser.add_argument("query", help="Natural-language search query.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--category", default=None)
    parser.add_argument("--audience", default=None)
    parser.add_argument("--min-score", type=float, default=None)
    return parser.parse_args()


async def run(
    query: str,
    limit: int,
    category: str | None,
    audience: str | None,
    min_score: float | None,
) -> None:
    settings = get_settings()
    qdrant = QdrantService(settings)
    try:
        embeddings = create_embedding_provider(settings)
        vector_store = QdrantVectorStore(
            qdrant.client,
            settings.qdrant_collection,
        )

        hits = await semantic_search(
            query,
            embeddings=embeddings,
            vector_store=vector_store,
            limit=limit,
            category=category,
            audience=audience,
            min_score=min_score,
        )

        print(f'Query: "{query}"')
        print(f"Results: {len(hits)}")
        for index, hit in enumerate(hits, start=1):
            page = f" | page {hit.page}" if hit.page is not None else ""
            excerpt = " ".join(hit.content.split())
            if len(excerpt) > 320:
                excerpt = excerpt[:317] + "..."
            print()
            print(f"#{index} score={hit.score:.4f}")
            print(
                f"{hit.source}{page} | "
                f"audience={hit.audience or '-'}"
            )
            print(excerpt)
    finally:
        await qdrant.close()


def main() -> None:
    args = parse_args()
    asyncio.run(
        run(
            args.query,
            args.limit,
            args.category,
            args.audience,
            args.min_score,
        )
    )


if __name__ == "__main__":
    main()
