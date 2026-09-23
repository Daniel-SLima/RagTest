import type { DemoApiError, DemoRetrievalRequest, DemoRetrievalResponse, DemoRunRequest, DemoRunResponse, DemoRuntime } from "../types/api"
import { getAllowedHttpsOrigins, invalidDemoResponse, parseDemoRetrievalResponse, parseDemoRunResponse, parseDemoRuntime, validateDemoBaseUrl, validateDemoRequest } from "./demo-api-validation"

export type DemoFetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>

const FALLBACK_ERROR = "demo_api_error"
const PUBLIC_ERROR_CODES = new Set(["invalid_retrieval_mode", "source_policy_blocked", "retrieval_unavailable", "generation_unavailable", "retrieval_failed", "generation_failed", "invalid_demo_request", "demo_disabled"])
const ERROR_MESSAGES: Record<string, string> = {
  invalid_retrieval_mode: "Modo de busca inválido para a demonstração.",
  source_policy_blocked: "Não há fontes públicas aprovadas para a demonstração.",
  retrieval_unavailable: "A busca documental está temporariamente indisponível.",
  generation_unavailable: "A geração está temporariamente indisponível.",
  retrieval_failed: "Não foi possível concluir a busca documental.",
  generation_failed: "Não foi possível gerar uma resposta agora.",
  invalid_demo_request: "Pergunta inválida para a demonstração.",
  demo_disabled: "A demonstração está desabilitada neste ambiente.",
  invalid_demo_response: "Resposta do serviço de demonstração inválida.",
  invalid_demo_base_url: "URL do serviço de demonstração inválida.",
  demo_api_error: "Não foi possível conectar ao serviço de demonstração.",
}

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

export function sanitizeDemoApiError(error: unknown): DemoApiError {
  const candidate = error && typeof error === "object" ? error as Record<string, unknown> : {}
  const rawCode = typeof candidate.code === "string" ? candidate.code.trim().toLowerCase() : FALLBACK_ERROR
  const code = PUBLIC_ERROR_CODES.has(rawCode) || rawCode === "invalid_demo_response" || rawCode === "invalid_demo_base_url" ? rawCode : FALLBACK_ERROR
  const rawStatus = candidate.status
  const status = typeof rawStatus === "number" && Number.isInteger(rawStatus) && rawStatus >= 100 && rawStatus <= 599 ? rawStatus : null
  return { code, status, message: ERROR_MESSAGES[code] ?? errorMessage(status) }
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
  return sanitizeDemoApiError(error)
}

export function createDemoApi(baseUrl: string, fetcher?: DemoFetcher, allowedHttpsOrigins?: readonly string[]) {
  const normalizedBaseUrl = validateDemoBaseUrl(baseUrl, { allowedHttpsOrigins: allowedHttpsOrigins ?? getAllowedHttpsOrigins(process.env.EXPO_PUBLIC_RAG_ALLOWED_HTTPS_ORIGINS) })
  const request = fetcher ?? ((input, init) => fetch(input, init))

  async function getJson<T>(path: string, parser: (value: unknown) => T, init?: RequestInit): Promise<T> {
    let response: Response
    try { response = await request(`${normalizedBaseUrl}${path}`, init) } catch (error) { throw toApiError(error) }
    if (!response.ok) throw await parseError(response)
    try { return parser(await response.json()) } catch (error) { throw sanitizeDemoApiError(error ?? invalidDemoResponse()) }
  }

  return {
    getRuntime: () => getJson<DemoRuntime>("/v1/demo/runtime", parseDemoRuntime),
    run: (requestBody: DemoRunRequest) => getJson<DemoRunResponse>("/v1/demo/run", parseDemoRunResponse, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(validateDemoRequest(requestBody)) }),
    retrieve: (requestBody: DemoRetrievalRequest) => getJson<DemoRetrievalResponse>("/v1/demo/retrieval", parseDemoRetrievalResponse, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(validateDemoRequest(requestBody)) }),
  }
}

export type DemoApi = ReturnType<typeof createDemoApi>
