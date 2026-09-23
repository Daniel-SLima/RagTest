export type RoadmapEvidence = { kind: "test" | "source" | "document"; reference: string; label: string }
export type RoadmapStatus = "implemented" | "partial" | "planned" | "research"
export type RoadmapItem = { id: string; area: string; title: string; status: RoadmapStatus; simpleExplanation: string; technicalExplanation: string; dependencies: string[]; evidence: RoadmapEvidence[]; snapshotVersion: string }
