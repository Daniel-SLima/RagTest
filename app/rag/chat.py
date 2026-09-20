from dataclasses import dataclass

from app.llm.base import LLMProvider
from app.rag.citations import validate_citations
from app.rag.decomposition import decompose_question
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.multi_query import multi_query_search
from app.rag.prompting import (
    SYSTEM_PROMPT,
    build_citation_repair_prompt,
    build_user_prompt,
)
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore, SearchHit


@dataclass(slots=True)
class ChatResult:
    answer: str
    sources: list[SearchHit]
    model: str
    grounded: bool
    citation_ids: list[int]
    citation_retry_count: int = 0
    multi_query_used: bool = False
    retrieval_queries: list[str] | None = None
    decomposition_status: str = "not-needed"


_GROUNDING_FALLBACK = (
    "Não foi possível gerar uma resposta com citações verificáveis a partir dos "
    "trechos recuperados. Consulte as fontes retornadas antes de usar a informação."
)


async def _generate_with_validated_citations(
    question: str,
    hits: list[SearchHit],
    llm: LLMProvider,
) -> tuple[str, bool, list[int], int]:
    answer = await llm.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(question, hits),
    )
    validation = validate_citations(answer, len(hits))

    if validation.valid:
        return answer, True, list(validation.citation_ids), 0

    repaired_answer = await llm.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_citation_repair_prompt(question, hits),
    )
    repaired_validation = validate_citations(repaired_answer, len(hits))

    if repaired_validation.valid:
        return repaired_answer, True, list(repaired_validation.citation_ids), 1

    return _GROUNDING_FALLBACK, False, [], 1


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
    auto_decompose: bool = True,
    max_subqueries: int = 3,
) -> ChatResult:
    decomposition = await decompose_question(
        question,
        llm=llm,
        enabled=auto_decompose,
        max_subqueries=max_subqueries,
    )

    if decomposition.used:
        retrieval_queries, _, fused = await multi_query_search(
            list(decomposition.subqueries),
            embeddings=embeddings,
            sparse_embeddings=sparse_embeddings,
            vector_store=vector_store,
            limit=limit,
            per_query_limit=limit,
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
        hits = [item.hit for item in fused]
    else:
        retrieval_queries = [question]
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
            grounded=False,
            citation_ids=[],
            multi_query_used=decomposition.used,
            retrieval_queries=list(retrieval_queries),
            decomposition_status=decomposition.status,
        )

    answer, grounded, citation_ids, retry_count = await _generate_with_validated_citations(
        question,
        hits,
        llm,
    )

    return ChatResult(
        answer=answer,
        sources=hits,
        model=llm.model_name,
        grounded=grounded,
        citation_ids=citation_ids,
        citation_retry_count=retry_count,
        multi_query_used=decomposition.used,
        retrieval_queries=list(retrieval_queries),
        decomposition_status=decomposition.status,
    )
