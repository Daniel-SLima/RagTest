import type {
  DemoApiError,
  DemoRetrievalMode,
  DemoRetrievalRequest,
  DemoRetrievalResponse,
  DemoRunResponse,
  DemoRuntime,
  DemoScore,
  DemoSource,
  DemoTimings,
} from "../types/api"

const MODES = new Set<DemoRetrievalMode>(["dense", "dense-rerank", "hybrid"])
const ERROR_MESSAGE = "Resposta do serviço de demonstração inválida."
const MAX_ANSWER_LENGTH = 20_000
const MAX_EXCERPT_LENGTH = 10_000
const MAX_LABEL_LENGTH = 500
const MAX_NUMERIC_MAGNITUDE = 1_000_000_000_000
const SENSITIVE_CONTENT = /(?:\.env\b|\bbearer\s+\S+|\b(?:api[_ -]?key|secret|password|token)\b|\b(?:system|user|developer)[_ -]?prompt\b|\bprompt\b|\btraceback\b|\bCHATSCM\b|[A-Za-z]:[\\/]|\\\\[A-Za-z]|\/(?:Users|home|root|private|tmp|var|etc)\/|(?:^|[\s("'])\/(?:[^\/\s]+\/)+[^\/\s]+|https?:\/\/(?:localhost|127\.0\.0\.1|10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.))/i

export function invalidDemoResponse(): DemoApiError {
  return { code: "invalid_demo_response", status: null, message: ERROR_MESSAGE }
}

function fail(): never {
  throw invalidDemoResponse()
}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) fail()
  return value as Record<string, unknown>
}

function exact(value: Record<string, unknown>, keys: readonly string[]): void {
  const actual = Object.keys(value).sort()
  const expected = [...keys].sort()
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) fail()
}

function stringValue(value: unknown, maxLength = MAX_LABEL_LENGTH): string {
  if (typeof value !== "string") fail()
  if (value.length > maxLength || SENSITIVE_CONTENT.test(value)) fail()
  return value
}

function finite(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value) || Math.abs(value) > MAX_NUMERIC_MAGNITUDE) fail()
  return value
}

function nullableNumber(value: unknown): number | null {
  if (value === null) return null
  return finite(value)
}

function nullableString(value: unknown): string | null {
  if (value === null) return null
  return stringValue(value)
}

export function parseDemoScore(value: unknown): DemoScore {
  const data = object(value)
  exact(data, ["dense_score", "sparse_score", "rank_score", "fusion_score"])
  return {
    dense_score: nullableNumber(data.dense_score),
    sparse_score: nullableNumber(data.sparse_score),
    rank_score: nullableNumber(data.rank_score),
    fusion_score: nullableNumber(data.fusion_score),
  }
}

export function parseDemoSource(value: unknown): DemoSource {
  const data = object(value)
  exact(data, ["public_id", "document", "page", "order", "excerpt", "scores"])
  const order = finite(data.order)
  if (!Number.isInteger(order) || order < 1) fail()
  const page = data.page === null ? null : finite(data.page)
  if (page !== null && (!Number.isInteger(page) || page < 1)) fail()
  return {
    public_id: stringValue(data.public_id),
    document: stringValue(data.document),
    page,
    order,
    excerpt: stringValue(data.excerpt, MAX_EXCERPT_LENGTH),
    scores: parseDemoScore(data.scores),
  }
}

export function parseDemoTimings(value: unknown): DemoTimings {
  const data = object(value)
  exact(data, ["retrieval_ms", "generation_ms", "total_ms"])
  const retrieval = finite(data.retrieval_ms)
  const generation = nullableNumber(data.generation_ms)
  const total = finite(data.total_ms)
  if (retrieval < 0 || (generation !== null && generation < 0) || total < 0) fail()
  return { retrieval_ms: retrieval, generation_ms: generation, total_ms: total }
}

function mode(value: unknown): DemoRetrievalMode {
  if (typeof value !== "string" || !MODES.has(value as DemoRetrievalMode)) fail()
  return value as DemoRetrievalMode
}

export function parseDemoRuntime(value: unknown): DemoRuntime {
  const data = object(value)
  exact(data, ["version", "provider", "model", "embedding", "retrieval", "collection", "demo_enabled", "policy_id", "policy_status"])
  if (typeof data.demo_enabled !== "boolean" || (data.policy_status !== "configured" && data.policy_status !== "blocked")) fail()
  return {
    version: stringValue(data.version), provider: stringValue(data.provider), model: stringValue(data.model),
    embedding: stringValue(data.embedding), retrieval: mode(data.retrieval), collection: stringValue(data.collection),
    demo_enabled: data.demo_enabled, policy_id: stringValue(data.policy_id), policy_status: data.policy_status,
  }
}

function citationIds(value: unknown): number[] {
  if (!Array.isArray(value)) fail()
  return value.map((id) => {
    const number = finite(id)
    if (!Number.isInteger(number) || number < 1) fail()
    return number
  })
}

export function parseDemoRunResponse(value: unknown): DemoRunResponse {
  const data = object(value)
  exact(data, ["answer", "model", "grounded", "citation_ids", "sources", "timings"])
  if (typeof data.grounded !== "boolean" || !Array.isArray(data.sources)) fail()
  return { answer: stringValue(data.answer, MAX_ANSWER_LENGTH), model: stringValue(data.model), grounded: data.grounded, citation_ids: citationIds(data.citation_ids), sources: data.sources.map(parseDemoSource), timings: parseDemoTimings(data.timings) }
}

export function parseDemoRetrievalResponse(value: unknown): DemoRetrievalResponse {
  const data = object(value)
  exact(data, ["query", "retrieval_mode", "sources", "timings"])
  if (!Array.isArray(data.sources)) fail()
  return { query: stringValue(data.query, 2_000), retrieval_mode: mode(data.retrieval_mode), sources: data.sources.map(parseDemoSource), timings: data.timings === null ? null : parseDemoTimings(data.timings) }
}

function optionalString(value: unknown, max: number): string | null | undefined {
  if (value === undefined) return undefined
  const result = nullableString(value)
  if (result !== null && result.length > max) throw invalidRequest()
  return result
}

function invalidRequest(): DemoApiError {
  return { code: "invalid_demo_request", status: null, message: "Pergunta inválida para a demonstração." }
}

export function validateDemoRequest(value: DemoRetrievalRequest): DemoRetrievalRequest {
  if (typeof value !== "object" || value === null) throw invalidRequest()
  const query = typeof value.query === "string" ? value.query.trim() : ""
  if (query.length < 2 || query.length > 2000) throw invalidRequest()
  if (value.limit !== undefined && (!Number.isInteger(value.limit) || value.limit < 1 || value.limit > 10)) throw invalidRequest()
  const category = optionalString(value.category, 100)
  const audience = optionalString(value.audience, 100)
  if (value.min_score !== undefined && value.min_score !== null && (typeof value.min_score !== "number" || !Number.isFinite(value.min_score) || value.min_score < -1 || value.min_score > 1)) throw invalidRequest()
  if (value.retrieval_mode !== undefined && value.retrieval_mode !== null && !MODES.has(value.retrieval_mode)) throw invalidRequest()
  return { query, ...(value.limit === undefined ? {} : { limit: value.limit }), ...(category === undefined ? {} : { category }), ...(audience === undefined ? {} : { audience }), ...(value.min_score === undefined ? {} : { min_score: value.min_score }), ...(value.retrieval_mode === undefined ? {} : { retrieval_mode: value.retrieval_mode }) }
}

function exactOrigin(value: string): string | null {
  try {
    const parsed = new URL(value)
    if (parsed.protocol !== "https:" || parsed.username || parsed.password || parsed.pathname !== "/" || parsed.search || parsed.hash || parsed.hostname.includes("*")) return null
    return `${parsed.protocol}//${parsed.host}`
  } catch { return null }
}

export function getAllowedHttpsOrigins(value?: string): readonly string[] {
  if (!value) return []
  return value.split(",").map((item) => exactOrigin(item.trim())).filter((item): item is string => item !== null)
}

function isPrivateIPv4(host: string): boolean {
  const parts = host.split(".").map(Number)
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part) || part < 0 || part > 255)) return false
  return parts[0] === 10 || parts[0] === 127 || (parts[0] === 192 && parts[1] === 168) || (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31)
}

export function validateDemoBaseUrl(value: string, options: { allowedHttpsOrigins?: readonly string[] } = {}): string {
  try {
    const parsed = new URL(value)
    if ((parsed.protocol !== "http:" && parsed.protocol !== "https:") || parsed.username || parsed.password || parsed.pathname !== "/" || parsed.search || parsed.hash || !parsed.hostname || parsed.port === "0") throw new Error()
    const normalized = `${parsed.protocol}//${parsed.host}`
    if (parsed.protocol === "https:") {
      if (!(options.allowedHttpsOrigins ?? []).includes(normalized)) throw new Error()
    } else {
      const host = parsed.hostname.toLowerCase()
      if (!(host === "localhost" || host === "::1" || host === "[::1]" || isPrivateIPv4(host))) throw new Error()
    }
    return normalized
  } catch { throw { code: "invalid_demo_base_url", status: null, message: "URL do serviço de demonstração inválida." } satisfies DemoApiError }
}
