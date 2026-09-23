import {
  ROADMAP_AREAS,
  ROADMAP_ITEMS,
  ROADMAP_SNAPSHOT,
  ROADMAP_STATUSES,
  filterRoadmapItems,
  getRoadmapCounts,
  validateRoadmapItems,
} from "./roadmap"
import type { RoadmapStatus } from "../types/roadmap"

describe("M5 roadmap catalog", () => {
  it("freezes a traceable, sanitized snapshot", () => {
    expect(ROADMAP_SNAPSHOT).toEqual({
      branch: "sidequest/ragtest-demo",
      commit: "75c924c",
      version: "M5",
      date: "2026-09-23",
      notes: "O item obsoleto do catálogo M2 foi removido por falta de requisito aprovado para a versão M5.",
    })

    const serialized = JSON.stringify({ snapshot: ROADMAP_SNAPSHOT, items: ROADMAP_ITEMS })
    expect(serialized).not.toMatch(/replay|CHATSCM|\.env|[A-Za-z]:\\|\/Users\/|https?:\/\//i)
  })

  it("keeps the four public statuses and evidence-backed items", () => {
    expect(ROADMAP_STATUSES).toEqual(["implemented", "partial", "planned", "research"])
    expect(new Set(ROADMAP_ITEMS.map((item) => item.status))).toEqual(new Set(ROADMAP_STATUSES))
    expect(ROADMAP_ITEMS.map((item) => item.id)).toEqual(expect.arrayContaining([
      "rag-api",
      "retrieval-evaluation",
      "structural-grounding",
      "demo-chat",
      "laboratory-m4",
      "backend-sessions",
      "document-base",
      "production-security",
      "privacy-lgpd",
      "specialized-evaluation",
      "se-cuida-integration",
    ]))

    const ids = new Set(ROADMAP_ITEMS.map((item) => item.id))
    for (const item of ROADMAP_ITEMS) {
      expect(item.evidence.length).toBeGreaterThan(0)
      expect(item.origin.length).toBeGreaterThan(0)
      expect(item.snapshotVersion).toMatch(/^M[1-5]$/)
      expect(item.snapshotCommit).toBe(ROADMAP_SNAPSHOT.commit)
      expect(item.dependencies.every((dependency) => ids.has(dependency))).toBe(true)
    }
    expect(ROADMAP_ITEMS.find((item) => item.id === "laboratory-m4")?.snapshotVersion).toBe("M4")
  })

  it("calculates status and area counts from the supplied list", () => {
    const counts = getRoadmapCounts(ROADMAP_ITEMS)
    const expectedStatuses = Object.fromEntries(ROADMAP_STATUSES.map((status) => [
      status,
      ROADMAP_ITEMS.filter((item) => item.status === status).length,
    ])) as Record<RoadmapStatus, number>
    const expectedAreas = Object.fromEntries(ROADMAP_AREAS.map((area) => [
      area,
      ROADMAP_ITEMS.filter((item) => item.area === area).length,
    ]))

    expect(counts.byStatus).toEqual(expectedStatuses)
    expect(counts.byArea).toEqual(expectedAreas)
    expect(Object.values(counts.byStatus).reduce((total, value) => total + value, 0)).toBe(ROADMAP_ITEMS.length)
  })

  it("keeps item evidence versions distinct from the global M5 snapshot commit", () => {
    const laboratory = ROADMAP_ITEMS.find((item) => item.id === "laboratory-m4")
    expect(laboratory?.snapshotVersion).toBe("M4")
    expect(laboratory?.snapshotCommit).toBe(ROADMAP_SNAPSHOT.commit)
    expect(ROADMAP_SNAPSHOT.version).toBe("M5")
  })

  it("filters by status and area without mutating the catalog", () => {
    const original = [...ROADMAP_ITEMS]
    expect(filterRoadmapItems(ROADMAP_ITEMS, { status: "all", area: "all" })).toEqual(ROADMAP_ITEMS)
    expect(filterRoadmapItems(ROADMAP_ITEMS, { status: "implemented", area: "all" }).every((item) => item.status === "implemented")).toBe(true)
    expect(filterRoadmapItems(ROADMAP_ITEMS, { status: "all", area: ROADMAP_AREAS[0] }).every((item) => item.area === ROADMAP_AREAS[0])).toBe(true)
    expect(filterRoadmapItems(ROADMAP_ITEMS, { status: "planned", area: ROADMAP_AREAS[0] }).every((item) => item.status === "planned" && item.area === ROADMAP_AREAS[0])).toBe(true)
    expect(filterRoadmapItems(ROADMAP_ITEMS, { status: "all", area: "missing-area" })).toEqual([])
    expect(ROADMAP_ITEMS).toEqual(original)
  })

  it("rejects duplicate IDs, orphan dependencies, empty evidence, and missing required text", () => {
    const valid = ROADMAP_ITEMS[0]
    expect(() => validateRoadmapItems([valid, { ...valid }])).toThrow(/duplicated/)
    expect(() => validateRoadmapItems([{ ...valid, id: "orphan-owner", dependencies: ["missing"] }])).toThrow(/not found/)
    expect(() => validateRoadmapItems([{ ...valid, id: "empty-evidence", evidence: [] }])).toThrow(/no evidence/)
    expect(() => validateRoadmapItems([{ ...valid, id: "empty-title", title: "" }])).toThrow(/required/)
    expect(() => validateRoadmapItems([{ ...valid, id: "empty-evidence-text", evidence: [{ ...valid.evidence[0], reference: "" }] }])).toThrow(/evidence field/)
  })
})
