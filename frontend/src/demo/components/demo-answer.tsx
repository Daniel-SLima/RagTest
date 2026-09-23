import { AnswerPresentation } from "../../components/answer-presentation"
import type { DemoRunResponse } from "../types/api"
import { useDemoTheme } from "./demo-shell-theme"

export function DemoAnswer({ response }: { response: DemoRunResponse }) {
  const theme = useDemoTheme()
  const cited = new Set(response.citation_ids)
  const sources = response.grounded ? response.sources.filter((source) => cited.has(source.order)) : response.sources
  return <AnswerPresentation model={{ answer: response.answer, grounded: response.grounded, sourcesTitle: response.grounded ? "Fontes consultadas" : "Fontes recuperadas para consulta", showCitationId: response.grounded, palette: { ...theme, accent: theme.action }, sources: sources.map((source) => ({ key: `${source.public_id}-${source.order}`, citationLabel: `[${source.order}]`, document: source.document, page: source.page, excerpt: source.excerpt, scores: { Dense: source.scores.dense_score, Sparse: source.scores.sparse_score, Ranking: source.scores.rank_score, Fusão: source.scores.fusion_score } })) }} />
}
