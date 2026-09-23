import type { ChatApiResponse } from "../lib/chat-api"
import { AnswerPresentation } from "./answer-presentation"

export function AssistantAnswer({ response }: { response: ChatApiResponse }) {
  const citedIds = new Set(response.citation_ids)
  const citedSources = response.sources.filter((source) => citedIds.has(source.citation_id))
  const showRetrievedSources = !response.grounded && response.sources.length > 0
  const visibleSources = response.grounded ? citedSources : response.sources
  return <AnswerPresentation model={{ answer: response.answer, grounded: response.grounded, sources: visibleSources.map((source) => ({ key: `${source.citation_id}-${source.source}-${source.page ?? "na"}`, citationLabel: `[${source.citation_id}]`, document: source.source, page: source.page, excerpt: source.excerpt })), sourcesTitle: response.grounded ? "Fontes consultadas" : "Fontes recuperadas para consulta", showCitationId: !showRetrievedSources }} />
}
