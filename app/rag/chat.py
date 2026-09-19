from dataclasses import dataclass

from app.llm.base import LLMProvider
from app.rag.embeddings.base import EmbeddingProvider
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
    vector_store: QdrantVectorStore,
    llm: LLMProvider,
    limit: int = 5,
    category: str | None = None,
    audience: str | None = None,
    min_score: float | None = None,
) -> ChatResult:
    hits = await semantic_search(
        question,
        embeddings=embeddings,
        vector_store=vector_store,
        limit=limit,
        category=category,
        audience=audience,
        min_score=min_score,
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

    return ChatResult(
        answer=answer,
        sources=hits,
        model=llm.model_name,
    )
