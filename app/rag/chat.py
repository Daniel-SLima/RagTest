from dataclasses import dataclass

from app.llm.base import LLMProvider
from app.rag.citations import extract_citation_ids, normalize_citation_markup
from app.rag.decomposition import decompose_question
from app.rag.embeddings.base import EmbeddingProvider, SparseEmbeddingProvider
from app.rag.grounding import (
    CitationCoverage,
    prune_uncited_claim_blocks,
    validate_citation_coverage,
)
from app.rag.multi_query import multi_query_search
from app.rag.prompting import (
    SYSTEM_PROMPT,
    build_citation_repair_prompt,
    build_user_prompt,
)
from app.rag.search import semantic_search
from app.rag.vector_store import QdrantVectorStore, SearchHit


@dataclass(frozen=True, slots=True)
class CitationValidationAttempt:
    stage: str
    valid: bool
    syntax_valid: bool
    total_claim_blocks: int
    cited_claim_blocks: int
    uncited_claim_blocks: int
    coverage: float
    reason: str | None

    @classmethod
    def from_coverage(
        cls,
        coverage: CitationCoverage,
        *,
        stage: str,
    ) -> "CitationValidationAttempt":
        return cls(
            stage=stage,
            valid=coverage.valid,
            syntax_valid=coverage.syntax_valid,
            total_claim_blocks=coverage.total_claim_blocks,
            cited_claim_blocks=coverage.cited_claim_blocks,
            uncited_claim_blocks=coverage.uncited_claim_blocks,
            coverage=coverage.coverage,
            reason=coverage.reason,
        )


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
    citation_validation_attempts: tuple[CitationValidationAttempt, ...] = ()


_GROUNDING_FALLBACK = (
    "Não foi possível gerar uma resposta com citações verificáveis a partir dos "
    "trechos recuperados. Consulte as fontes retornadas antes de usar a informação."
)


def _can_postprocess_safely(validation: CitationCoverage) -> bool:
    return (
        validation.syntax_valid
        and validation.uncited_claim_blocks == 1
        and validation.cited_claim_blocks > 0
        and validation.coverage >= 0.8
    )


def _postprocess_if_fully_grounded(
    answer: str,
    source_count: int,
) -> tuple[str, CitationCoverage] | None:
    postprocessed_answer = prune_uncited_claim_blocks(answer, source_count)
    postprocessed_validation = validate_citation_coverage(
        postprocessed_answer,
        source_count,
    )
    if not postprocessed_validation.valid:
        return None
    return postprocessed_answer, postprocessed_validation


async def _generate_with_validated_citations(
    question: str,
    hits: list[SearchHit],
    llm: LLMProvider,
) -> tuple[str, bool, list[int], int, tuple[CitationValidationAttempt, ...]]:
    answer = await llm.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(question, hits),
    )
    answer = normalize_citation_markup(answer)
    validation = validate_citation_coverage(answer, len(hits))

    first_attempt = CitationValidationAttempt.from_coverage(
        validation,
        stage="initial",
    )

    if validation.valid:
        return answer, True, list(extract_citation_ids(answer)), 0, (first_attempt,)

    if _can_postprocess_safely(validation):
        postprocessed = _postprocess_if_fully_grounded(answer, len(hits))
        if postprocessed is not None:
            postprocessed_answer, postprocessed_validation = postprocessed
            postprocess_attempt = CitationValidationAttempt.from_coverage(
                postprocessed_validation,
                stage="postprocess",
            )
            return (
                postprocessed_answer,
                True,
                list(extract_citation_ids(postprocessed_answer)),
                0,
                (first_attempt, postprocess_attempt),
            )

    repaired_answer = await llm.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_citation_repair_prompt(
            question,
            hits,
            previous_answer=answer,
            validation_reason=validation.reason,
            uncited_blocks=validation.uncited_blocks,
        ),
    )
    repaired_answer = normalize_citation_markup(repaired_answer)
    repaired_validation = validate_citation_coverage(repaired_answer, len(hits))

    second_attempt = CitationValidationAttempt.from_coverage(
        repaired_validation,
        stage="repair",
    )
    attempts = (first_attempt, second_attempt)

    if repaired_validation.valid:
        return repaired_answer, True, list(extract_citation_ids(repaired_answer)), 1, attempts

    if _can_postprocess_safely(repaired_validation):
        postprocessed = _postprocess_if_fully_grounded(
            repaired_answer,
            len(hits),
        )
        if postprocessed is None:
            return _GROUNDING_FALLBACK, False, [], 1, attempts

        postprocessed_answer, postprocessed_validation = postprocessed
        postprocess_attempt = CitationValidationAttempt.from_coverage(
            postprocessed_validation,
            stage="postprocess",
        )
        attempts = (*attempts, postprocess_attempt)

        if postprocessed_validation.valid:
            return (
                postprocessed_answer,
                True,
                list(extract_citation_ids(postprocessed_answer)),
                1,
                attempts,
            )

    return _GROUNDING_FALLBACK, False, [], 1, attempts


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

    (
        answer,
        grounded,
        citation_ids,
        retry_count,
        citation_validation_attempts,
    ) = await _generate_with_validated_citations(
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
        citation_validation_attempts=citation_validation_attempts,
    )
