import type { DemoRunState } from "../types/run-state"

export type DemoPipelineStageState = "available" | "not-required" | "unavailable" | "not-measured"
export type DemoPipelineStageView = { id: string; title: string; simpleExplanation: string; technicalDetails: string; state: DemoPipelineStageState; value?: string; source?: string }
const unavailable = "Não disponível"

export function buildDemoPipeline(state: DemoRunState): DemoPipelineStageView[] {
  const response = state.response; const runtime = state.runtime; const source = response?.sources[0]
  return [
    { id: "question", title: "Pergunta", simpleExplanation: "A pergunta recebida orienta a consulta.", technicalDetails: response && state.question ? "Pergunta enviada à execução demo M1." : "Execute uma pergunta no Chat para visualizar o pipeline.", state: state.question ? "available" : "unavailable", value: state.question ?? undefined },
    { id: "analysis", title: "Análise e decomposição", simpleExplanation: "Esta versão executa uma consulta única.", technicalDetails: "O endpoint demo M1 está configurado para executar single-query nesta versão", source: "configuração estática da rota M1", state: "not-required", value: "single-query" },
    { id: "embedding", title: "Embedding", simpleExplanation: "A pergunta pode ser representada para busca semântica.", technicalDetails: runtime?.embedding ? `Modelo: ${runtime.embedding}; dimensão: ${unavailable}` : unavailable, state: runtime ? "available" : "unavailable", value: runtime?.embedding, source: "runtime M1" },
    { id: "qdrant", title: "Qdrant", simpleExplanation: "A coleção vetorial participa da recuperação.", technicalDetails: runtime?.collection ? `Collection: ${runtime.collection}` : unavailable, state: runtime ? "available" : "unavailable", value: runtime?.collection, source: "runtime M1" },
    { id: "retrieval", title: "Retrieval", simpleExplanation: "As fontes públicas retornadas ficam visíveis.", technicalDetails: source ? `Ordem ${source.order}; documento ${source.document}; página ${source.page ?? unavailable}. Scores preservam valores nulos.` : unavailable, state: response ? "available" : "unavailable", value: source ? `${response.sources.length} fonte(s)` : undefined, source: "resposta M1" },
    { id: "reranking", title: "Reranking", simpleExplanation: "A UI não infere ranking além do DTO.", technicalDetails: "Pré-ranking e pós-reranking: Não disponível", state: "unavailable", value: unavailable },
    { id: "context", title: "Contexto", simpleExplanation: "O contexto final enviado ao LLM não é exposto.", technicalDetails: "Não disponível nesta versão da demo", state: "unavailable", value: unavailable },
    { id: "llm", title: "LLM", simpleExplanation: "O provider e o modelo vêm do runtime/resposta.", technicalDetails: runtime && response ? `Provider: ${runtime.provider}; modelo: ${response.model}; geração: ${response.timings.generation_ms ?? unavailable} ms` : unavailable, state: runtime && response ? "available" : "unavailable", source: "runtime e resposta M1" },
    { id: "citations", title: "Citações", simpleExplanation: "IDs de citação são preservados do DTO.", technicalDetails: response ? `IDs: ${response.citation_ids.length ? response.citation_ids.join(", ") : unavailable}. Retry count: ${unavailable}` : unavailable, state: response ? "available" : "unavailable", source: "resposta M1" },
    { id: "grounding", title: "Grounding", simpleExplanation: "Grounding indica cobertura estrutural de citações.", technicalDetails: response ? `${response.grounded ? "Citações cobertas estruturalmente" : "Citações não verificadas"}; não é garantia clínica.` : unavailable, state: response ? "available" : "unavailable", source: "resposta M1" },
    { id: "answer", title: "Resposta", simpleExplanation: "A resposta sanitizada é apresentada junto às fontes.", technicalDetails: response?.answer ?? unavailable, state: response ? "available" : "unavailable", source: "resposta M1" },
  ]
}
