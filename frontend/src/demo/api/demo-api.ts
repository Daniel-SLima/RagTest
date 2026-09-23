import type { DemoApiError, DemoRetrievalRequest, DemoRetrievalResponse, DemoRunRequest, DemoRunResponse, DemoRuntime } from "../types/api"
import { getAllowedHttpsOrigins, invalidDemoResponse, parseDemoRetrievalResponse, parseDemoRunResponse, parseDemoRuntime, validateDemoBaseUrl, validateDemoRequest } from "./demo-api-validation"

export type DemoFetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>

const FALLBACK_ERROR = "demo_api_error"
const PUBLIC_ERROR_CODES = new Set(["invalid_retrieval_mode", "source_policy_blocked", "retrieval_unavailable", "generation_unavailable", "retrieval_failed", "generation_failed", "invalid_demo_request", "demo_disabled"])

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
  } catch { /* discard raw response */ }
  return { code, status: response.status, message: errorMessage(response.status) }
}

function toApiError(error: unknown): DemoApiError {
  if (error && typeof error === "object" && "code" in error && "status" in error && "message" in error) {
    const candidate = error as DemoApiError
    if (candidate.code === "invalid_demo_request" || candidate.code === "invalid_demo_base_url") return { code: candidate.code, status: null, message: candidate.message }
  }
  return { code: FALLBACK_ERROR, status: null, message: errorMessage(null) }
}

export function createDemoApi(baseUrl: string, fetcher?: DemoFetcher, allowedHttpsOrigins?: readonly string[]) {
  const normalizedBaseUrl = validateDemoBaseUrl(baseUrl, { allowedHttpsOrigins: allowedHttpsOrigins ?? getAllowedHttpsOrigins(process.env.EXPO_PUBLIC_RAG_ALLOWED_HTTPS_ORIGINS) })
  const request = fetcher ?? ((input, init) => fetch(input, init))

  async function getJson<T>(path: string, parser: (value: unknown) => T, init?: RequestInit): Promise<T> {
    let response: Response
    try { response = await request(`${normalizedBaseUrl}${path}`, init) } catch (error) { throw toApiError(error) }
    if (!response.ok) throw await parseError(response)
    try { return parser(await response.json()) } catch (error) {
      if (error && typeof error === "object" && "code" in error && "status" in error && "message" in error) throw error
      throw invalidDemoResponse()
    }
  }

  return {
    getRuntime: () => getJson<DemoRuntime>("/v1/demo/runtime", parseDemoRuntime),
    run: (requestBody: DemoRunRequest) => getJson<DemoRunResponse>("/v1/demo/run", parseDemoRunResponse, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(validateDemoRequest(requestBody)) }),
    retrieve: (requestBody: DemoRetrievalRequest) => getJson<DemoRetrievalResponse>("/v1/demo/retrieval", parseDemoRetrievalResponse, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(validateDemoRequest(requestBody)) }),
  }
}

export type DemoApi = ReturnType<typeof createDemoApi>
