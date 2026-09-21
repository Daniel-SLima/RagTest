export type ChatRequestInput = {
  message: string
  category?: string | null
  audience?: string | null
  limit?: number
  autoDecompose?: boolean
}

export type ChatApiRequest = {
  message: string
  limit: number
  category: string | null
  audience: string | null
  auto_decompose: boolean
}

export type ChatSource = {
  citation_id: number
  score: number
  source: string
  category: string | null
  audience: string | null
  page: number | null
  chunk_count: number
  excerpt: string
}

export type ChatApiResponse = {
  answer: string
  model: string
  grounded: boolean
  citation_ids: number[]
  citation_retry_count: number
  multi_query_used: boolean
  retrieval_queries: string[]
  decomposition_status: string
  sources: ChatSource[]
}

export function buildChatRequest(input: ChatRequestInput): ChatApiRequest {
  return {
    message: input.message.trim(),
    limit: input.limit ?? 5,
    category: input.category ?? null,
    audience: input.audience ?? null,
    auto_decompose: input.autoDecompose ?? true,
  }
}
