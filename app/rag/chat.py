from dataclasses import dataclass

from app.llm.base import LLMProvider
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.prompting import SYSTEM_PROMPT, build_user_prompt
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore, SearchHit


@dataclass(slots=True)
class ChatResult:
    answer: str
    sources: list[SearchHit]
    model: str


async def answer_with_rag(
    question: str,
    *,
    embeddings: EmbeddingProvider,
    sparse_embeddings: SparseEmbeddingProvider | None = None,
    vector_store: QdrantVectorStore,
    llm: LLMProvider,
    limit: int = 5,
    category: str | None = None,
    audience: str | None = None,
    min_score: float | None = None,
    candidate_multiplier: int = 8,
    score_margin: float = 0.22,
    merge_same_page: bool = True,
    max_group_chars: int = 5000,
    source_lexical_weight: float = 0.25,
    content_lexical_weight: float = 0.05,
    hybrid_dense_weight: float = 1.0,
    hybrid_sparse_weight: float = 1.2,
) -> ChatResult:
    hits = await semantic_search(
        question,
        embeddings=embeddings,
        sparse_embeddings=sparse_embeddings,
        vector_store=vector_store,
        limit=limit,
        category=category,
        audience=audience,
        min_score=min_score,
        candidate_multiplier=candidate_multiplier,
        score_margin=score_margin,
        merge_same_page=merge_same_page,
        max_group_chars=max_group_chars,
        source_lexical_weight=source_lexical_weight,
        content_lexical_weight=content_lexical_weight,
        hybrid_dense_weight=hybrid_dense_weight,
        hybrid_sparse_weight=hybrid_sparse_weight,
    )

    if not hits:
        return ChatResult(
            answer=(
                "Não encontrei trechos com relevância suficiente na base documental "
                "para responder a essa pergunta."
            ),
            sources=[],
            model=llm.model_name,
        )

    answer = await llm.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(question, hits),
    )

    if not answer:
        answer = (
            "O modelo não retornou uma resposta. Os trechos recuperados estão "
            "disponíveis no campo sources."
        )

    return ChatResult(answer=answer, sources=hits, model=llm.model_name)
