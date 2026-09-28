import argparse
import asyncio
import time
from pathlib import Path

from app.cli.evaluate_retrieval import load_packaged_dataset
from app.core.config import get_settings
from app.evaluation.answers import answer_row, write_rows_csv
from app.llm.factory import create_llm_provider
from app.rag.chat import answer_with_rag
from app.rag.embeddings.factory import (
    create_embedding_provider,
    create_sparse_embedding_provider,
)
from app.rag.retrieval_profiles import get_profile
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


async def run(datasets: list[str], output: Path) -> None:
    settings = get_settings()
    profile = get_profile(settings.retrieval_mode)
    qdrant = QdrantService(settings)
    try:
        embeddings = create_embedding_provider(settings)
        sparse = create_sparse_embedding_provider(settings) if profile.use_sparse else None
        store = QdrantVectorStore(qdrant.client, settings.qdrant_collection)
        llm = create_llm_provider(settings)
        rows = []
        cases = [case for name in datasets for case in load_packaged_dataset(name)]
        for number, case in enumerate(cases, start=1):
            started = time.monotonic()
            result = await answer_with_rag(
                str(case["query"]),
                embeddings=embeddings,
                sparse_embeddings=sparse,
                vector_store=store,
                llm=llm,
                candidate_multiplier=profile.candidate_multiplier,
                score_margin=profile.score_margin,
                merge_same_page=settings.retrieval_merge_same_page,
                max_group_chars=settings.retrieval_max_group_chars,
                source_lexical_weight=profile.source_lexical_weight,
                content_lexical_weight=profile.content_lexical_weight,
                hybrid_dense_weight=profile.dense_weight,
                hybrid_sparse_weight=profile.sparse_weight,
                auto_decompose=settings.retrieval_auto_decompose,
                max_subqueries=settings.retrieval_max_subqueries,
            )
            row = answer_row(case, result, (time.monotonic() - started) * 1000)
            rows.append(row)
            print(f"[{number}/{len(cases)}] {row['status']:<12} {row['latency_ms']:>6} ms  {row['id']}")
        write_rows_csv(rows, output)
        print(f"CSV salvo em {output}")
    finally:
        await qdrant.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera respostas reais para a rubrica manual.")
    parser.add_argument(
        "--dataset",
        action="append",
        default=None,
        help="Dataset empacotado (repetível). Padrão: dominio-v2-dev e dominio-v2-fora-escopo.",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    settings = get_settings()
    output = args.output or Path(settings.session_db_path).parent / "respostas_modelo.csv"
    datasets = args.dataset or ["dominio-v2-dev", "dominio-v2-fora-escopo"]
    asyncio.run(run(datasets, output))
