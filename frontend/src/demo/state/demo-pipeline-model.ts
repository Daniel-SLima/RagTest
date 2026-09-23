import type { DemoRunState } from "../types/run-state"

export type DemoPipelineStageState = "available" | "not-required" | "unavailable" | "not-measured"
export type DemoPipelineStageView = { id: string; title: string; simpleExplanation: string; technicalDetails: string; state: DemoPipelineStageState; value?: string; source?: string }
const unavailable = "Não disponível"

export function buildDemoPipeline(state: DemoRunState): DemoPipelineStageView[] {
  const response = state.response; const runtime = state.runtime; const source = response?.sources[0]
  const retrievalMode = runtime?.retrieval
  const retrievalSummary = response?.sources.length
    ? response.sources.map((item) => `#${item.order} ${item.document} · página ${item.page ?? unavailable} · dense ${item.scores.dense_score ?? unavailable} · sparse ${item.scores.sparse_score ?? unavailable} · ranking ${item.scores.rank_score ?? unavailable} · fusão ${item.scores.fusion_score ?? unavailable}`).join("; ")
    : response ? "Nenhuma fonte retornada" : unavailable
  const rerankingStage = retrievalMode === "dense-rerank"
    ? { id: "reranking", title: "Reranking", simpleExplanation: "O perfil runtime indica uma etapa de reranking.", technicalDetails: "Perfil dense-rerank habilitado; comparação pré/pós e métricas de reranking: Não disponível", state: "available" as const, value: "dense-rerank", source: "runtime M1" }
    : { id: "reranking", title: "Reranking", simpleExplanation: "A UI não infere ranking além do DTO.", technicalDetails: retrievalMode === "dense" ? "O perfil dense não declara reranking; comparação pré/pós: Não disponível" : unavailable, state: retrievalMode === "dense" ? "not-required" as const : "unavailable" as const, value: retrievalMode === "dense" ? "não requerido pelo perfil" : unavailable, source: runtime ? "runtime M1" : undefined }
  return [
    { id: "question", title: "Pergunta", simpleExplanation: "A pergunta recebida orienta a consulta.", technicalDetails: response && state.question ? "Pergunta enviada à execução demo M1." : "Execute uma pergunta no Chat para visualizar o pipeline.", state: state.question ? "available" : "unavailable", value: state.question ?? undefined },
    { id: "analysis", title: "Análise e decomposição", simpleExplanation: "Esta versão executa uma consulta única.", technicalDetails: "O endpoint demo M1 está configurado para executar single-query nesta versão", source: "configuração estática da rota M1", state: "not-required", value: "single-query" },
    { id: "embedding", title: "Embedding", simpleExplanation: "A pergunta pode ser representada para busca semântica.", technicalDetails: runtime?.embedding ? `Modelo: ${runtime.embedding}; dimensão: ${unavailable}` : unavailable, state: runtime ? "available" : "unavailable", value: runtime?.embedding, source: "runtime M1" },
    { id: "qdrant", title: "Qdrant", simpleExplanation: "A coleção vetorial participa da recuperação.", technicalDetails: runtime?.collection ? `Collection: ${runtime.collection}` : unavailable, state: runtime ? "available" : "unavailable", value: runtime?.collection, source: "runtime M1" },
    { id: "retrieval", title: "Retrieval", simpleExplanation: "As fontes públicas retornadas ficam visíveis.", technicalDetails: response ? `Modo: ${retrievalMode ?? unavailable}. Resumo permitido: ${retrievalSummary ?? unavailable}. Os detalhes completos e scores estão no cartão da resposta no Chat.` : unavailable, state: response ? "available" : "unavailable", value: source ? `${response.sources.length} fonte(s) · ${retrievalMode ?? unavailable}` : undefined, source: "resposta M1 e runtime M1" },
    rerankingStage,
    { id: "context", title: "Contexto", simpleExplanation: "O contexto final enviado ao LLM não é exposto.", technicalDetails: "Não disponível nesta versão da demo", state: "unavailable", value: unavailable },
    { id: "llm", title: "LLM", simpleExplanation: "O provider e o modelo vêm do runtime/resposta.", technicalDetails: runtime && response ? `Provider: ${runtime.provider}; modelo: ${response.model}; geração: ${response.timings.generation_ms ?? unavailable} ms` : unavailable, state: runtime && response ? "available" : "unavailable", source: "runtime e resposta M1" },
    { id: "citations", title: "Citações", simpleExplanation: "IDs de citação são preservados do DTO.", technicalDetails: response ? `IDs: ${response.citation_ids.length ? response.citation_ids.join(", ") : unavailable}. Retry count: ${unavailable}` : unavailable, state: response ? "available" : "unavailable", source: "resposta M1" },
    { id: "grounding", title: "Grounding", simpleExplanation: "Grounding indica cobertura estrutural de citações.", technicalDetails: response ? `${response.grounded ? "Citações cobertas estruturalmente" : "Citações não verificadas"}; não é garantia clínica.` : unavailable, state: response ? "available" : "unavailable", source: "resposta M1" },
    { id: "answer", title: "Resposta", simpleExplanation: "A resposta sanitizada é apresentada junto às fontes.", technicalDetails: response?.answer ?? unavailable, state: response ? "available" : "unavailable", source: "resposta M1" },
  ]
}
