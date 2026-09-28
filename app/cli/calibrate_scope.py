import argparse
import asyncio
import json
from importlib.resources import files

from app.core.config import get_settings
from app.evaluation.scope import suggest_min_score
from app.rag.embeddings.factory import create_embedding_provider
from app.rag.vector_store import QdrantVectorStore
from app.services.qdrant_service import QdrantService


def _dataset(name: str) -> list[dict[str, object]]:
    path = files("app.evaluation").joinpath("datasets", name)
    return json.loads(path.read_text(encoding="utf-8"))


async def _top_score(query: str, embeddings, vector_store: QdrantVectorStore) -> float:
    hits = await vector_store.search(await embeddings.embed_query(query), limit=1)
    if not hits:
        return 0.0
    hit = hits[0]
    return hit.dense_score if hit.dense_score is not None else hit.score


async def run(split: str) -> None:
    settings = get_settings()
    qdrant = QdrantService(settings)
    try:
        embeddings = create_embedding_provider(settings)
        vector_store = QdrantVectorStore(qdrant.client, settings.qdrant_collection)
        in_scope = _dataset(f"dominio-v2-{split}.json")
        out_scope = _dataset("dominio-v2-fora-escopo.json")

        print(f"RagTest scope calibration | split={split}")
        in_scores: list[float] = []
        for case in in_scope:
            score = await _top_score(str(case["query"]), embeddings, vector_store)
            in_scores.append(score)
            print(f"  in  {score:.4f}  {case['id']}")
        out_scores: list[float] = []
        for case in out_scope:
            score = await _top_score(str(case["query"]), embeddings, vector_store)
            out_scores.append(score)
            print(f"  out {score:.4f}  {case['id']}")

        suggestion = suggest_min_score(in_scope=in_scores, out_of_scope=out_scores)
        print()
        print(f"min in-scope      : {suggestion.min_in_scope:.4f}")
        print(f"max out-of-scope  : {suggestion.max_out_of_scope:.4f}")
        if suggestion.separable:
            print(f"Sugestão: RETRIEVAL_MIN_SCORE={suggestion.threshold}")
        else:
            print(
                "Sem separação limpa: "
                f"{suggestion.overlap_in_scope} pergunta(s) do domínio ficam abaixo do pior "
                "fora de escopo. Não configure o limiar sem analisar os casos."
            )
    finally:
        await qdrant.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibra RETRIEVAL_MIN_SCORE (fora de escopo).")
    parser.add_argument("--split", choices=("dev", "holdout"), default="dev")
    asyncio.run(run(parser.parse_args().split))
