export type DemoRetrievalMode = "dense" | "dense-rerank" | "hybrid"

export type DemoScore = {
  dense_score: number | null
  sparse_score: number | null
  rank_score: number | null
  fusion_score: number | null
}

export type DemoSource = {
  public_id: string
  document: string
  page: number | null
  order: number
  excerpt: string
  scores: DemoScore
}

export type DemoTimings = {
  retrieval_ms: number
  generation_ms: number | null
  total_ms: number
}

export type DemoRetrievalRequest = {
  query: string
  limit?: number
  category?: string | null
  audience?: string | null
  min_score?: number | null
  retrieval_mode?: DemoRetrievalMode | null
}

export type DemoRunRequest = DemoRetrievalRequest

export type DemoRetrievalResponse = {
  query: string
  retrieval_mode: DemoRetrievalMode
  sources: DemoSource[]
  timings: DemoTimings | null
}

export type DemoRunResponse = {
  answer: string
  model: string
  grounded: boolean
  citation_ids: number[]
  sources: DemoSource[]
  timings: DemoTimings
}

export type DemoRuntimeResponse = {
  version: string
  provider: string
  model: string
  embedding: string
  retrieval: DemoRetrievalMode
  collection: string
  demo_enabled: boolean
  policy_id: string
  policy_status: "configured" | "blocked"
}

export type DemoRuntime = DemoRuntimeResponse

export type DemoApiError = {
  code: string
  status: number | null
  message: string
}
