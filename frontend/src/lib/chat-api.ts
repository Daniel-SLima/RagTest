import type { components } from "./api-types"

export class ChatApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ChatApiError"
    this.status = status
  }
}

function getErrorMessage(body: unknown, status: number): string {
  if (
    typeof body === "object" &&
    body !== null &&
    "detail" in body &&
    typeof body.detail === "string"
  ) {
    return body.detail
  }

  return `RagTest API retornou HTTP ${status}.`
}

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

type Schemas = components["schemas"]

export type ChatSource = Schemas["ChatSource"]
export type ChatSafety = Schemas["ChatSafety"]
export type ChatAction = Schemas["ChatAction"]
export type ChatDisplay = Schemas["ChatDisplay"]
export type ChatApiResponse = Schemas["ChatResponse"]

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
    headers: Record<string, string>
    body: string
  },
) => Promise<ChatFetchResponse>

type SendChatOptions = {
  baseUrl: string
  apiKey?: string
  fetcher?: ChatFetcher
}

function authHeaders(apiKey?: string): Record<string, string> {
  return apiKey ? { "X-API-Key": apiKey } : {}
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
    headers: { "Content-Type": "application/json", ...authHeaders(options.apiKey) },
    body: JSON.stringify(buildChatRequest(input)),
  })

  const body = await response.json()

  if (!response.ok) {
    throw new ChatApiError(
      response.status,
      getErrorMessage(body, response.status),
    )
  }

  return body as ChatApiResponse
}

export type SuggestionsLoader = () => Promise<string[]>

export function createSuggestionsLoader(baseUrl: string, apiKey?: string): SuggestionsLoader {
  return async () => {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/v1/suggestions`, {
      headers: authHeaders(apiKey),
    })
    if (!response.ok) {
      return []
    }
    const body = (await response.json()) as { suggestions?: { text: string }[] }
    return (body.suggestions ?? []).map((item) => item.text)
  }
}
