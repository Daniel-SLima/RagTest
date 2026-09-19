import argparse
import asyncio

from app.core.config import get_settings
from app.llm.factory import create_llm_provider
from app.rag.chat import answer_with_rag
from app.rag.embeddings.factory import create_embedding_provider
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask a grounded question to RagTest.")
    parser.add_argument("message", help="Question to send to the RAG chat.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--category", default=None)
    parser.add_argument("--audience", default=None)
    parser.add_argument("--min-score", type=float, default=None)
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    settings = get_settings()
    qdrant = QdrantService(settings)

    try:
        embeddings = create_embedding_provider(settings)
        vector_store = QdrantVectorStore(
            qdrant.client,
            settings.qdrant_collection,
        )
        llm = create_llm_provider(settings)

        result = await answer_with_rag(
            args.message,
            embeddings=embeddings,
            vector_store=vector_store,
            llm=llm,
            limit=args.limit,
            category=args.category,
            audience=args.audience,
            min_score=args.min_score,
        )

        print()
        print("Answer:")
        print(result.answer)
        print()
        print(f"Model: {result.model}")
        print("Sources:")
        for index, hit in enumerate(result.sources, start=1):
            page = f", page {hit.page}" if hit.page is not None else ""
            print(
                f"[{index}] {hit.source}{page} "
                f"(score={hit.score:.4f}, audience={hit.audience or '-'})"
            )
    finally:
        await qdrant.close()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
