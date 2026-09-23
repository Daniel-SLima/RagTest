import type { DemoRetrievalMode } from "../types/api"

export type LaboratoryBenchmarkSplit = "DEV" | "HOLDOUT"

export type LaboratoryBenchmarkMetric = "HitRate@5" | "MRR@5" | "SourceRecall@5" | "SourceNDCG@5"

export type LaboratoryBenchmarkRow = {
  readonly datasetVersion: "2026-09-20-v1"
  readonly split: LaboratoryBenchmarkSplit
  readonly strategy: DemoRetrievalMode
  readonly metrics: Readonly<Record<LaboratoryBenchmarkMetric, number>>
  readonly source: string
}

const source = "docs/avaliacao-retrieval.md:176-224; docs/decisoes-tecnicas.md:D006-D008"

/**
 * Frozen historical evidence. These values describe the evaluation dataset,
 * not the result of a current laboratory request.
 */
export const LAB_BENCHMARKS: readonly LaboratoryBenchmarkRow[] = Object.freeze([
  { datasetVersion: "2026-09-20-v1", split: "DEV", strategy: "dense", metrics: { "HitRate@5": 1, "MRR@5": 0.857, "SourceRecall@5": 1, "SourceNDCG@5": 0.903 }, source },
  { datasetVersion: "2026-09-20-v1", split: "DEV", strategy: "dense-rerank", metrics: { "HitRate@5": 1, "MRR@5": 0.929, "SourceRecall@5": 1, "SourceNDCG@5": 0.936 }, source },
  { datasetVersion: "2026-09-20-v1", split: "DEV", strategy: "hybrid", metrics: { "HitRate@5": 1, "MRR@5": 0.821, "SourceRecall@5": 1, "SourceNDCG@5": 0.869 }, source },
  { datasetVersion: "2026-09-20-v1", split: "HOLDOUT", strategy: "dense", metrics: { "HitRate@5": 1, "MRR@5": 0.889, "SourceRecall@5": 1, "SourceNDCG@5": 0.917 }, source },
  { datasetVersion: "2026-09-20-v1", split: "HOLDOUT", strategy: "dense-rerank", metrics: { "HitRate@5": 1, "MRR@5": 0.933, "SourceRecall@5": 1, "SourceNDCG@5": 0.941 }, source },
  { datasetVersion: "2026-09-20-v1", split: "HOLDOUT", strategy: "hybrid", metrics: { "HitRate@5": 1, "MRR@5": 0.878, "SourceRecall@5": 0.967, "SourceNDCG@5": 0.885 }, source },
] as const)

export const LAB_RATIONALE = {
  title: "Por que o RAGTest usa essa estratégia?",
  simple: "As três estratégias são perfis experimentais com compromissos diferentes entre semântica, sinais lexicais e fusão. O laboratório permite observar o comportamento no mesmo enunciado.",
  technical: "Dense consulta a representação vetorial; Dense + rerank mantém a busca densa e aplica o perfil de reordenação lexical; Hybrid combina sinais densos e esparsos com fusão RRF no backend. A tela não inventa uma comparação pré/pós-rerank quando o contrato não a expõe.",
  method: "Problema → alternativas (dense, dense-rerank, hybrid) → experimento controlado → decisão apoiada por evidência. D006 mantém dense-rerank como padrão do produto com base no benchmark; D007 versiona os perfis. Isso não demonstra superioridade universal.",
  disclaimer: "Benchmarks são históricos e não são a pontuação desta execução. A tela não escolhe uma estratégia a partir dos scores da máquina local.",
  sources: "docs/decisoes-tecnicas.md:D006-D007; docs/avaliacao-retrieval.md:176-224",
} as const
