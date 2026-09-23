import { createDemoApi } from "./demo-api"
import { isDemoEnabled } from "../config"

const runtime = { version: "M1", provider: "none", model: "none", embedding: "none", retrieval: "dense", collection: "public", demo_enabled: true, policy_id: "local", policy_status: "configured" as const }
const source = { public_id: "public-1", document: "public/doc.pdf", page: null, order: 1, excerpt: "public", scores: { dense_score: null, sparse_score: null, rank_score: null, fusion_score: null } }
const timings = { retrieval_ms: 1, generation_ms: null, total_ms: 1 }
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
      () => createDemoApi("http://demo", jest.fn().mockResolvedValue(response({ code: "retrieval_unavailable", secret: "never" }, false, 503))).getRuntime(),
      () => createDemoApi("http://demo", jest.fn().mockRejectedValue(new Error("secret body"))).getRuntime(),
      () => createDemoApi("http://demo", jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => { throw new Error("raw") } } as unknown as Response)).getRuntime(),
    ]
    for (const makePending of cases) {
      const pending = makePending()
      await expect(pending).rejects.toMatchObject({ code: expect.any(String), message: expect.any(String) })
    }
  })
})
