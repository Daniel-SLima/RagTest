import type { DemoRetrievalResponse } from "../types/api"
import {
  LAB_BENCHMARKS,
  LAB_STRATEGIES,
  deriveComparisonMetrics,
  sourceKey,
} from "./laboratory-model"

function response(mode: DemoRetrievalResponse["retrieval_mode"], sources: DemoRetrievalResponse["sources"]): DemoRetrievalResponse {
  return { query: "pergunta pública", retrieval_mode: mode, sources, timings: null }
}

const source = (publicId: string, document: string, page: number | null, order: number, denseScore: number | null = 0.8) => ({
  public_id: publicId,
  document,
  page,
  order,
  excerpt: `Trecho ${publicId}`,
  scores: { dense_score: denseScore, sparse_score: null, rank_score: null, fusion_score: null },
})

describe("laboratory model", () => {
  it("keeps the three backend strategies in a stable order", () => {
    expect(LAB_STRATEGIES.map((strategy) => strategy.id)).toEqual(["dense", "dense-rerank", "hybrid"])
    expect(LAB_STRATEGIES.map((strategy) => strategy.label)).toEqual(["Dense", "Dense + rerank", "Hybrid"])
  })

  it("uses public id, document, and page as source identity", () => {
    const first = source("public-1", "public/a.pdf", 2, 1)
    expect(sourceKey(first)).toBe("public-1|public/a.pdf|2")
    expect(sourceKey({ ...first, page: null })).toBe("public-1|public/a.pdf|null")
    expect(sourceKey({ ...first, public_id: "public-2" })).not.toBe(sourceKey(first))
  })

  it("derives descriptive overlap, exclusivity, document counts, and rank deltas", () => {
    const shared = source("shared", "public/shared.pdf", 1, 1)
    const denseOnly = source("dense-only", "public/dense.pdf", 3, 2)
    const rerankOnly = source("rerank-only", "public/rerank.pdf", 4, 2)
    const hybridOnly = source("hybrid-only", "public/hybrid.pdf", 5, 2)
    const metrics = deriveComparisonMetrics([
      { strategy: "dense", response: response("dense", [shared, denseOnly]) },
      { strategy: "dense-rerank", response: response("dense-rerank", [denseOnly, shared, rerankOnly]) },
      { strategy: "hybrid", response: response("hybrid", [shared, hybridOnly]) },
    ])

    expect(metrics.byStrategy.dense).toMatchObject({ resultCount: 2, uniqueDocuments: 2 })
    expect(metrics.byStrategy["dense-rerank"]).toMatchObject({ resultCount: 3, uniqueDocuments: 3 })
    expect(metrics.allThree.count).toBe(1)
    expect(metrics.allThree.keys).toEqual([sourceKey(shared)])
    expect(metrics.pairOverlap.find((item) => item.left === "dense" && item.right === "dense-rerank")).toMatchObject({ count: 2 })
    expect(metrics.exclusive.find((item) => item.strategy === "dense")?.keys).toEqual([])
    expect(metrics.exclusive.find((item) => item.strategy === "dense-rerank")?.keys).toEqual([sourceKey(rerankOnly)])
    expect(metrics.exclusive.find((item) => item.strategy === "hybrid")?.keys).toEqual([sourceKey(hybridOnly)])
    expect(metrics.rankDeltas.find((item) => item.key === sourceKey(shared))).toMatchObject({ ranks: { dense: 1, "dense-rerank": 2, hybrid: 1 } })
  })

  it("retains null pages and scores rather than coercing them", () => {
    const item = source("nullable", "public/nullable.pdf", null, 1, null)
    const metrics = deriveComparisonMetrics([{ strategy: "dense", response: response("dense", [item]) }])
    expect(metrics.byStrategy.dense.sourceDetails[0]).toMatchObject({ page: null, denseScore: null })
  })

  it("exposes versioned DEV and HOLDOUT historical metrics", () => {
    expect(new Set(LAB_BENCHMARKS.map((row) => row.datasetVersion))).toEqual(new Set(["2026-09-20-v1"]))
    expect(new Set(LAB_BENCHMARKS.map((row) => row.split))).toEqual(new Set(["DEV", "HOLDOUT"]))
    expect(new Set(LAB_BENCHMARKS.flatMap((row) => Object.keys(row.metrics)))).toEqual(new Set(["HitRate@5", "MRR@5", "SourceRecall@5", "SourceNDCG@5"]))
  })
})
