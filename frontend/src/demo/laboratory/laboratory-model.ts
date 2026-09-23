import type { DemoApiError, DemoRetrievalMode, DemoRetrievalResponse, DemoSource } from "../types/api"
import { LAB_BENCHMARKS, LAB_RATIONALE } from "../data/laboratory-benchmarks"

export { LAB_BENCHMARKS, LAB_RATIONALE }

export const LAB_STRATEGIES = [
  { id: "dense", label: "Dense", description: "Busca semântica densa." },
  { id: "dense-rerank", label: "Dense + rerank", description: "Busca densa com reordenação lexical do perfil." },
  { id: "hybrid", label: "Hybrid", description: "Sinais densos e esparsos com fusão." },
] as const satisfies readonly { id: DemoRetrievalMode; label: string; description: string }[]

export type LabStrategy = (typeof LAB_STRATEGIES)[number]["id"]
export type LabExecutionStatus = "idle" | "loading" | "success" | "error"

export type LabExecution = {
  strategy: LabStrategy
  status: LabExecutionStatus
  response: DemoRetrievalResponse | null
  error: DemoApiError | null
  revision: number
}

export type LabSourceDetail = {
  key: string
  document: string
  page: number | null
  denseScore: number | null
  sparseScore: number | null
  rankScore: number | null
  fusionScore: number | null
}

export type LabStrategyMetrics = {
  resultCount: number
  uniqueDocuments: number
  sourceKeys: readonly string[]
  sourceDetails: readonly LabSourceDetail[]
}

export type LabPairOverlap = {
  left: LabStrategy
  right: LabStrategy
  count: number
  keys: readonly string[]
}

export type LabExclusiveSources = {
  strategy: LabStrategy
  count: number
  keys: readonly string[]
}

export type LabRankDelta = {
  key: string
  document: string
  page: number | null
  ranks: Partial<Record<LabStrategy, number>>
  deltas: Partial<Record<LabStrategy, number>>
}

export type LabComparisonMetrics = {
  byStrategy: Record<LabStrategy, LabStrategyMetrics>
  pairOverlap: readonly LabPairOverlap[]
  allThree: { count: number; keys: readonly string[] }
  exclusive: readonly LabExclusiveSources[]
  rankDeltas: readonly LabRankDelta[]
}

export type LabResponseEntry = { strategy: LabStrategy; response: DemoRetrievalResponse }

export function sourceKey(source: Pick<DemoSource, "public_id" | "document" | "page">): string {
  return `${source.public_id}|${source.document}|${source.page === null ? "null" : source.page}`
}

function emptyStrategyMetrics(): LabStrategyMetrics {
  return { resultCount: 0, uniqueDocuments: 0, sourceKeys: [], sourceDetails: [] }
}

function entriesFrom(value: ReadonlyArray<LabResponseEntry> | ReadonlyMap<LabStrategy, DemoRetrievalResponse | null> | Partial<Record<LabStrategy, DemoRetrievalResponse | null>>): LabResponseEntry[] {
  if (Array.isArray(value)) return value.filter((item): item is LabResponseEntry => Boolean(item?.response))
  if (value instanceof Map) return Array.from(value.entries()).flatMap(([strategy, response]) => response ? [{ strategy, response }] : [])
  const record = value as Partial<Record<LabStrategy, DemoRetrievalResponse | null>>
  return LAB_STRATEGIES.flatMap(({ id }) => record[id] ? [{ strategy: id, response: record[id] as DemoRetrievalResponse }] : [])
}

export function deriveComparisonMetrics(value: ReadonlyArray<LabResponseEntry> | ReadonlyMap<LabStrategy, DemoRetrievalResponse | null> | Partial<Record<LabStrategy, DemoRetrievalResponse | null>>): LabComparisonMetrics {
  const entries = entriesFrom(value)
  const byStrategy = Object.fromEntries(LAB_STRATEGIES.map(({ id }) => [id, emptyStrategyMetrics()])) as Record<LabStrategy, LabStrategyMetrics>
  const sets = new Map<LabStrategy, Set<string>>()
  const ranks = new Map<string, { source: DemoSource; byStrategy: Partial<Record<LabStrategy, number>> }>()

  for (const { strategy, response } of entries) {
    const keys: string[] = []
    const details: LabSourceDetail[] = []
    const documents = new Set<string>()
    response.sources.forEach((source, index) => {
      const key = sourceKey(source)
      keys.push(key)
      documents.add(source.document)
      details.push({ key, document: source.document, page: source.page, denseScore: source.scores.dense_score, sparseScore: source.scores.sparse_score, rankScore: source.scores.rank_score, fusionScore: source.scores.fusion_score })
      const current = ranks.get(key) ?? { source, byStrategy: {} }
      current.byStrategy[strategy] = index + 1
      ranks.set(key, current)
    })
    byStrategy[strategy] = { resultCount: response.sources.length, uniqueDocuments: documents.size, sourceKeys: keys, sourceDetails: details }
    sets.set(strategy, new Set(keys))
  }

  const pairOverlap: LabPairOverlap[] = []
  for (let leftIndex = 0; leftIndex < LAB_STRATEGIES.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < LAB_STRATEGIES.length; rightIndex += 1) {
      const left = LAB_STRATEGIES[leftIndex].id
      const right = LAB_STRATEGIES[rightIndex].id
      const keys = [...(sets.get(left) ?? [])].filter((key) => sets.get(right)?.has(key))
      pairOverlap.push({ left, right, count: keys.length, keys })
    }
  }

  const allThreeKeys = [...(sets.get("dense") ?? [])].filter((key) => sets.get("dense-rerank")?.has(key) && sets.get("hybrid")?.has(key))
  const exclusive = LAB_STRATEGIES.map(({ id: strategy }) => {
    const keys = [...(sets.get(strategy) ?? [])].filter((key) => LAB_STRATEGIES.every(({ id }) => id === strategy || !sets.get(id)?.has(key)))
    return { strategy, count: keys.length, keys }
  })
  const rankDeltas: LabRankDelta[] = []
  for (const [key, valueForKey] of ranks) {
    const strategyRanks = valueForKey.byStrategy
    const available = LAB_STRATEGIES.map(({ id }) => strategyRanks[id]).filter((rank): rank is number => rank !== undefined)
    const baseline = available[0]
    const deltas: Partial<Record<LabStrategy, number>> = {}
    if (baseline !== undefined) for (const { id } of LAB_STRATEGIES) if (strategyRanks[id] !== undefined) deltas[id] = strategyRanks[id]! - baseline
    rankDeltas.push({ key, document: valueForKey.source.document, page: valueForKey.source.page, ranks: strategyRanks, deltas })
  }

  return { byStrategy, pairOverlap, allThree: { count: allThreeKeys.length, keys: allThreeKeys }, exclusive, rankDeltas }
}
