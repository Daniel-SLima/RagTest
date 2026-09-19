from langchain_core.prompts import PromptTemplate

from app.rag.vector_store import SearchHit

SYSTEM_PROMPT = """Você é o módulo de resposta de um sistema RAG documental.

Regras obrigatórias:
- Responda somente com informações sustentadas pelos trechos recuperados.
- Não complete lacunas com conhecimento externo, suposições ou recomendações próprias.
- Quando a base não trouxer informação suficiente, diga claramente que os documentos recuperados não são suficientes para responder.
- Preserve qualificadores, exceções, faixas etárias, periodicidade e condições descritas nas fontes.
- Use citações no formato [1], [2], etc., correspondentes aos blocos de contexto fornecidos.
- Não invente números de fonte.
- Não apresente diagnóstico individual nem substitua avaliação de profissional de saúde.
- Responda em português do Brasil, de forma clara e objetiva.
"""

USER_TEMPLATE = PromptTemplate.from_template(
    """Pergunta do usuário:
{question}

Contexto documental recuperado:
{context}

Elabore a resposta usando apenas o contexto acima e cite as fontes relevantes com [n]."""
)


def build_context(hits: list[SearchHit]) -> str:
    blocks: list[str] = []

    for index, hit in enumerate(hits, start=1):
        location = hit.source
        if hit.page is not None:
            location += f" — página {hit.page}"

        blocks.append(
            f"[{index}] Fonte: {location}\n"
            f"Categoria: {hit.category or 'não informada'}\n"
            f"Público: {hit.audience or 'não informado'}\n"
            f"Score de recuperação: {hit.score:.4f}\n"
            f"Trecho:\n{hit.content.strip()}"
        )

    return "\n\n".join(blocks)


def build_user_prompt(question: str, hits: list[SearchHit]) -> str:
    return USER_TEMPLATE.format(
        question=question,
        context=build_context(hits),
    )
