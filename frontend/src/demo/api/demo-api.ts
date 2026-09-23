import type {
  DemoApiError,
  DemoRetrievalRequest,
  DemoRetrievalResponse,
  DemoRunRequest,
  DemoRunResponse,
  DemoRuntime,
} from "../types/api"

export type DemoFetcher = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>

const FALLBACK_ERROR = "demo_api_error"
const PUBLIC_ERROR_CODES = new Set([
  "invalid_retrieval_mode",
  "retrieval_failed",
  "source_policy_blocked",
  "retrieval_unavailable",
  "generation_failed",
  "generation_unavailable",
  "invalid_demo_request",
  "demo_disabled",
  "validation_error",
])

function sanitizeCode(value: unknown): string {
  if (typeof value !== "string") return FALLBACK_ERROR
  const code = value.trim().toLowerCase()
  return PUBLIC_ERROR_CODES.has(code) ? code : FALLBACK_ERROR
}

function errorMessage(status: number | null): string {
  if (status === 503) return "Serviço de demonstração temporariamente indisponível."
  if (status !== null) return `Serviço de demonstração retornou HTTP ${status}.`
  return "Não foi possível conectar ao serviço de demonstração."
}

async function parseError(response: Response): Promise<DemoApiError> {
  let code = FALLBACK_ERROR
  try {
    const body: unknown = await response.json()
    if (typeof body === "object" && body !== null) {
      const directCode = "code" in body ? body.code : undefined
      const detail = "detail" in body ? body.detail : undefined
      const nestedCode = typeof detail === "object" && detail !== null && "code" in detail ? detail.code : undefined
      code = sanitizeCode(directCode ?? nestedCode)
    }
  } catch {
    // Deliberately discard malformed or private response bodies.
  }
  return { code, status: response.status, message: errorMessage(response.status) }
}

function toApiError(error: unknown): DemoApiError {
  if (error && typeof error === "object" && "status" in error) {
    const status = typeof error.status === "number" ? error.status : null
    return { code: FALLBACK_ERROR, status, message: errorMessage(status) }
  }
  return { code: FALLBACK_ERROR, status: null, message: errorMessage(null) }
}

export function createDemoApi(baseUrl: string, fetcher?: DemoFetcher) {
  const normalizedBaseUrl = baseUrl.replace(/\/$/, "")
  const request = fetcher ?? ((input, init) => fetch(input, init))

  async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response
    try {
      response = await request(`${normalizedBaseUrl}${path}`, init)
    } catch (error) {
      throw toApiError(error)
    }
    if (!response.ok) throw await parseError(response)
    try {
      return (await response.json()) as T
    } catch {
      throw { code: FALLBACK_ERROR, status: response.status, message: "Resposta inválida do serviço de demonstração." } satisfies DemoApiError
    }
  }

  return {
    getRuntime: () => getJson<DemoRuntime>("/v1/demo/runtime"),
    run: (requestBody: DemoRunRequest) =>
      getJson<DemoRunResponse>("/v1/demo/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      }),
    retrieve: (requestBody: DemoRetrievalRequest) =>
      getJson<DemoRetrievalResponse>("/v1/demo/retrieval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      }),
  }
}

export type DemoApi = ReturnType<typeof createDemoApi>
