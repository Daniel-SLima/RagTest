export type ChatRequestInput = {
  message: string
  category?: string | null
  audience?: string | null
  limit?: number
  minScore?: number
  autoDecompose?: boolean
}

export type ChatApiRequest = {
  message: string
  limit: number
  category: string | null
  audience: string | null
  min_score?: number
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
    ...(input.minScore === undefined ? {} : { min_score: input.minScore }),
    auto_decompose: input.autoDecompose ?? true,
  }
}

type ChatFetchResponse = {
  ok: boolean
  status: number
  json(): Promise<unknown>
}

export type ChatFetcher = (
  url: string,
  init: {
    method: "POST"
    headers: { "Content-Type": "application/json" }
    body: string
  },
) => Promise<ChatFetchResponse>

type SendChatOptions = {
  baseUrl: string
  fetcher?: ChatFetcher
}

export async function sendChatMessage(
  input: ChatRequestInput,
  options: SendChatOptions,
): Promise<ChatApiResponse> {
  const baseUrl = options.baseUrl.replace(/\/$/, "")
  const fetcher: ChatFetcher =
    options.fetcher ??
    ((url, init) => fetch(url, init) as Promise<ChatFetchResponse>)

  const response = await fetcher(`${baseUrl}/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildChatRequest(input)),
  })

  return (await response.json()) as ChatApiResponse
}
