import { createDemoApi } from "./demo-api"
import { isDemoEnabled } from "../config"

// TEST DATA: minimal public-shaped fixtures, never sent to an external provider.
const runtime = { version: "M1", provider: "none", model: "none", embedding: "none", retrieval: "dense", collection: "public", demo_enabled: true, policy_id: "local", policy_status: "configured" as const }
const source = { public_id: "public-1", document: "public/doc.pdf", page: null, order: 1, excerpt: "public", scores: { dense_score: null, sparse_score: null, rank_score: null, fusion_score: null } }
const timings = { retrieval_ms: 1, generation_ms: null, total_ms: 1 }
const TEST_DATA = "TEST DATA"
const response = (body: unknown, ok = true, status = 200) => ({ ok, status, json: async () => body }) as Response

describe("demo configuration and client", () => {
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
    const api = createDemoApi("http://demo/", fetcher)
    const result = await api.retrieve({ query: "q", retrieval_mode: null, category: null, audience: null, min_score: null })
    expect(fetcher).toHaveBeenCalledWith("http://demo/v1/demo/retrieval", expect.any(Object))
    expect(result.timings).toBeNull()
    expect(result.sources[0].scores.dense_score).toBeNull()
  })

  it("exposes the three typed endpoints without requests during construction", async () => {
    const fetcher = jest.fn()
      .mockResolvedValueOnce(response(runtime))
      .mockResolvedValueOnce(response({ answer: "", model: "none", grounded: false, citation_ids: [], sources: [], timings }))
      .mockResolvedValueOnce(response({ query: "q", retrieval_mode: "hybrid", sources: [], timings }))
    const api = createDemoApi("http://demo", fetcher)
    expect(fetcher).not.toHaveBeenCalled()
    await api.getRuntime(); await api.run({ query: "q" }); await api.retrieve({ query: "q" })
    expect(fetcher).toHaveBeenCalledTimes(3)
  })

  it("sanitizes HTTP, network and invalid JSON failures", async () => {
    const cases = [
      () => createDemoApi("http://demo", jest.fn().mockResolvedValue(response({ detail: { code: "retrieval_unavailable", testData: TEST_DATA } }, false, 503))).getRuntime(),
      () => createDemoApi("http://demo", jest.fn().mockRejectedValue(new Error("private transport detail"))).getRuntime(),
      () => createDemoApi("http://demo", jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => { throw new Error("malformed") } } as unknown as Response)).getRuntime(),
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
    const api = createDemoApi("http://demo", jest.fn().mockResolvedValue(response({ detail: { code, testData: TEST_DATA } }, false, 422)))
    const pending = api.getRuntime()
    await expect(pending).rejects.toMatchObject({ code, status: 422 })
    await expect(pending).rejects.not.toHaveProperty("testData")
  })

  it("falls back for unknown error codes without exposing the body", async () => {
    const api = createDemoApi("http://demo", jest.fn().mockResolvedValue(response({ code: "unknown_internal_code", testData: TEST_DATA }, false, 500)))
    const pending = api.getRuntime()
    await expect(pending).rejects.toMatchObject({ code: "demo_api_error", status: 500 })
    await expect(pending).rejects.not.toHaveProperty("testData")
  })
})
