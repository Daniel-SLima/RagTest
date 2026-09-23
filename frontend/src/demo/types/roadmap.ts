export type RoadmapEvidence = {
  kind: "test" | "source" | "document"
  reference: string
  label: string
}

export type RoadmapStatus = "implemented" | "partial" | "planned" | "research"

export type RoadmapItem = {
  id: string
  area: string
  title: string
  status: RoadmapStatus
  simpleExplanation: string
  technicalExplanation: string
  whyItMatters: string
  whyMissing?: string
  dependencies: readonly string[]
  evidence: readonly RoadmapEvidence[]
  origin: string
  snapshotVersion: string
  snapshotCommit: string
  notes?: string
}

export type RoadmapSnapshot = {
  branch: string
  commit: string
  version: string
  date: string
  notes: string
}

export type RoadmapCounts = {
  byStatus: Record<RoadmapStatus, number>
  byArea: Record<string, number>
}

export type RoadmapFilter = {
  status?: RoadmapStatus | "all"
  area?: string | "all"
}
