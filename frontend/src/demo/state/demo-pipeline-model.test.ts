import { buildDemoPipeline } from "./demo-pipeline-model"
import type { DemoRunState } from "../types/run-state"

const base: DemoRunState = { question: "TEST DATA", response: { answer: "TEST DATA", model: "TEST DATA", grounded: true, citation_ids: [1], sources: [{ public_id: "public-1", document: "public/doc.pdf", page: null, order: 1, excerpt: "TEST DATA", scores: { dense_score: null, sparse_score: null, rank_score: null, fusion_score: null } }], timings: { retrieval_ms: 1, generation_ms: null, total_ms: 1 } }, diagnostics: null, runtime: { version: "M1", provider: "TEST DATA", model: "TEST DATA", embedding: "TEST DATA", retrieval: "dense", collection: "public", demo_enabled: true, policy_id: "local", policy_status: "configured" }, runtimeStatus: "success", runtimeError: null, status: "success", error: null }

describe("buildDemoPipeline", () => {
  it("returns the fixed eleven stages with only DTO-backed values", () => {
    const pipeline = buildDemoPipeline(base)
    expect(pipeline).toHaveLength(11)
    expect(pipeline.map((stage) => stage.id)).toEqual(["question", "analysis", "embedding", "qdrant", "retrieval", "reranking", "context", "llm", "citations", "grounding", "answer"])
    expect(pipeline[1]).toMatchObject({ value: "single-query", source: "configuração estática da rota M1", technicalDetails: "O endpoint demo M1 está configurado para executar single-query nesta versão" })
    expect(pipeline[2].value).toBe("TEST DATA")
    expect(pipeline[2].technicalDetails).toContain("Não disponível")
    expect(pipeline[5].technicalDetails).toContain("Não disponível")
    expect(pipeline[6].value).toBe("Não disponível")
    expect(pipeline[8].technicalDetails).toContain("Retry count: Não disponível")
    expect(pipeline[9].technicalDetails).toContain("não é garantia clínica")
  })
  it("does not fabricate values before a run", () => {
    const pipeline = buildDemoPipeline({ ...base, question: null, response: null, runtime: null, status: "idle" })
    expect(pipeline.every((stage) => stage.id === "analysis" || stage.value === undefined || stage.value === "Não disponível")).toBe(true)
    expect(pipeline.find((stage) => stage.id === "question")?.technicalDetails).toContain("Execute uma pergunta")
  })
})
