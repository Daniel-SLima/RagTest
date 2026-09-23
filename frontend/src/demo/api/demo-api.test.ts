import { createDemoApi } from "./demo-api"
import { isDemoEnabled } from "../config"
import { getAllowedHttpsOrigins, parseDemoRunResponse, validateDemoBaseUrl } from "./demo-api-validation"

// TEST DATA: minimal public-shaped fixtures, never sent to an external provider.
const runtime = { version: "M1", provider: "none", model: "none", embedding: "none", retrieval: "dense", collection: "public", demo_enabled: true, policy_id: "local", policy_status: "configured" as const }
const source = { public_id: "public-1", document: "public/doc.pdf", page: null, order: 1, excerpt: "public", scores: { dense_score: null, sparse_score: null, rank_score: null, fusion_score: null } }
const timings = { retrieval_ms: 1, generation_ms: null, total_ms: 1 }
const TEST_DATA = "TEST DATA"
const response = (body: unknown, ok = true, status = 200) => ({ ok, status, json: async () => body }) as Response

describe("demo configuration and client", () => {
  it.each(["http://localhost:8000/", "http://127.0.0.1:8000", "http://127.0.0.1:65535", "http://192.168.1.20:8000", "http://[::1]:8000"]) ("accepts safe base URL %s", (value) => {
    expect(validateDemoBaseUrl(value)).toMatch(/^http:\/\//)
  })

  it.each(["http://8.8.8.8", "http://[2001:db8::1]:8000", "http://127.0.0.1:0", "http://127.0.0.1:65536", "file:///tmp/demo", "http://user:pass@127.0.0.1", "http://127.0.0.1?token=x", "http://127.0.0.1#fragment"]) ("rejects unsafe base URL %s", (value) => {
    expect(() => validateDemoBaseUrl(value)).toThrow()
  })

  it("allows only explicitly listed HTTPS origins", () => {
    expect(getAllowedHttpsOrigins("https://localhost:8443,*,https://example.com/path")).toEqual(["https://localhost:8443"])
    expect(validateDemoBaseUrl("https://localhost:8443", { allowedHttpsOrigins: ["https://localhost:8443"] })).toBe("https://localhost:8443")
    expect(() => validateDemoBaseUrl("https://example.com", { allowedHttpsOrigins: [] })).toThrow()
    expect(() => validateDemoBaseUrl("https://localhost:9443", { allowedHttpsOrigins: ["https://localhost:8443"] })).toThrow()
  })
  it.each([undefined, "", "false", "1", "yes"]) ("keeps demo disabled for %p", (value) => expect(isDemoEnabled(value)).toBe(false))
  it.each(["TRUE", " true "]) ("enables demo only for normalized true %p", (value) => expect(isDemoEnabled(value)).toBe(true))

  it("reads the environment at call time", () => {
    process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED = "false"
    expect(isDemoEnabled()).toBe(false)
    process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED = " TRUE "
    expect(isDemoEnabled()).toBe(true)
    delete process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED
  })

  it("normalizes one trailing slash and preserves nullable schema values", async () => {
    const fetcher = jest.fn().mockResolvedValue(response({ query: "q", retrieval_mode: "dense", sources: [source], timings: null }))
    const api = createDemoApi("http://127.0.0.1:8000/", fetcher)
    const result = await api.retrieve({ query: "qq", retrieval_mode: null, category: null, audience: null, min_score: null })
    expect(fetcher).toHaveBeenCalledWith("http://127.0.0.1:8000/v1/demo/retrieval", expect.any(Object))
    expect(result.timings).toBeNull()
    expect(result.sources[0].scores.dense_score).toBeNull()
  })

  it("exposes the three typed endpoints without requests during construction", async () => {
    const fetcher = jest.fn()
      .mockResolvedValueOnce(response(runtime))
      .mockResolvedValueOnce(response({ answer: "", model: "none", grounded: false, citation_ids: [], sources: [], timings }))
      .mockResolvedValueOnce(response({ query: "qq", retrieval_mode: "hybrid", sources: [], timings }))
    const api = createDemoApi("http://127.0.0.1:8000", fetcher)
    expect(fetcher).not.toHaveBeenCalled()
    await api.getRuntime(); await api.run({ query: "qq" }); await api.retrieve({ query: "qq" })
    expect(fetcher).toHaveBeenCalledTimes(3)
  })

  it("sanitizes HTTP, network and invalid JSON failures", async () => {
    const cases = [
      () => createDemoApi("http://127.0.0.1:8000", jest.fn().mockResolvedValue(response({ detail: { code: "retrieval_unavailable", testData: TEST_DATA } }, false, 503))).getRuntime(),
      () => createDemoApi("http://127.0.0.1:8000", jest.fn().mockRejectedValue(new Error("private transport detail"))).getRuntime(),
      () => createDemoApi("http://127.0.0.1:8000", jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => { throw new Error("malformed") } } as unknown as Response)).getRuntime(),
    ]
    for (const makePending of cases) {
      const pending = makePending()
      await expect(pending).rejects.toMatchObject({ code: expect.any(String), message: expect.any(String) })
      await expect(pending).rejects.not.toHaveProperty("testData")
    }
  })

  it.each([
    "invalid_retrieval_mode",
    "retrieval_failed",
    "source_policy_blocked",
    "retrieval_unavailable",
    "generation_failed",
    "generation_unavailable",
    "invalid_demo_request",
  ])("preserves the public M1 error code %s", async (code) => {
    const api = createDemoApi("http://127.0.0.1:8000", jest.fn().mockResolvedValue(response({ detail: { code, testData: TEST_DATA } }, false, 422)))
    const pending = api.getRuntime()
    await expect(pending).rejects.toMatchObject({ code, status: 422 })
    await expect(pending).rejects.not.toHaveProperty("testData")
  })

  it("falls back for unknown error codes without exposing the body", async () => {
    const api = createDemoApi("http://127.0.0.1:8000", jest.fn().mockResolvedValue(response({ code: "unknown_internal_code", testData: TEST_DATA }, false, 500)))
    const pending = api.getRuntime()
    await expect(pending).rejects.toMatchObject({ code: "demo_api_error", status: 500 })
    await expect(pending).rejects.not.toHaveProperty("testData")
  })

  it("rejects closed DTO violations and non-finite values", () => {
    expect(() => parseDemoRunResponse({ ...response("TEST DATA"), extra: "secret" })).toThrow()
    expect(() => parseDemoRunResponse({ answer: "TEST DATA", model: "TEST DATA", grounded: true, citation_ids: [Number.NaN], sources: [], timings })).toThrow()
    expect(() => parseDemoRunResponse({ answer: "TEST DATA", model: "TEST DATA", grounded: true, citation_ids: [], sources: [], timings: { ...timings, total_ms: -1 } })).toThrow()
  })
})
