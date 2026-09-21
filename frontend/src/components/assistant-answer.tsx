import Markdown from "@ronradtke/react-native-markdown-display"
import { StyleSheet, Text, View } from "react-native"

import type { ChatApiResponse, ChatSource } from "../lib/chat-api"

type AssistantAnswerProps = {
  response: ChatApiResponse
}

function sourceFilename(source: string): string {
  const normalized = source.replaceAll("\\", "/")
  return normalized.split("/").filter(Boolean).at(-1) ?? source
}

function SourceCard({
  source,
  showCitationId = true,
}: {
  source: ChatSource
  showCitationId?: boolean
}) {
  return (
    <View style={styles.sourceCard}>
      <View style={styles.sourceHeader}>
        {showCitationId ? (
          <Text style={styles.citationBadge}>[{source.citation_id}]</Text>
        ) : null}
        <Text style={styles.sourceTitle}>{sourceFilename(source.source)}</Text>
      </View>
      <Text style={styles.sourceMeta}>
        {source.page === null ? "Página não informada" : `Página ${source.page}`}
      </Text>
      {source.excerpt ? (
        <Text numberOfLines={3} style={styles.sourceExcerpt}>
          {source.excerpt}
        </Text>
      ) : null}
    </View>
  )
}

function GroundingStatus({
  grounded,
  hasSources,
}: {
  grounded: boolean
  hasSources: boolean
}) {
  if (grounded) {
    return (
      <View style={[styles.groundingCard, styles.groundingVerified]}>
        <Text style={styles.groundingTitle}>Citações verificadas</Text>
        <Text style={styles.groundingText}>
          As afirmações informativas estão acompanhadas de referências do corpus.
        </Text>
      </View>
    )
  }

  if (hasSources) {
    return (
      <View style={[styles.groundingCard, styles.groundingWarning]}>
        <Text style={styles.groundingTitle}>Citações não verificadas</Text>
        <Text style={styles.groundingText}>
          Não foi possível validar as citações desta resposta. Consulte as fontes
          recuperadas abaixo.
        </Text>
      </View>
    )
  }

  return (
    <View style={[styles.groundingCard, styles.groundingWarning]}>
      <Text style={styles.groundingTitle}>Sem base documental suficiente</Text>
      <Text style={styles.groundingText}>
        Não foram encontrados trechos relevantes o bastante para fundamentar uma
        resposta.
      </Text>
    </View>
  )
}

export function AssistantAnswer({ response }: AssistantAnswerProps) {
  const citedIds = new Set(response.citation_ids)
  const citedSources = response.sources.filter((source) =>
    citedIds.has(source.citation_id),
  )
  const showRetrievedSources = !response.grounded && response.sources.length > 0
  const visibleSources = response.grounded ? citedSources : response.sources
  const sourcesTitle = response.grounded
    ? "Fontes consultadas"
    : "Fontes recuperadas para consulta"

  return (
    <View style={styles.wrapper}>
      <Markdown style={markdownStyles}>{response.answer}</Markdown>

      <GroundingStatus
        grounded={response.grounded}
        hasSources={response.sources.length > 0}
      />

      {visibleSources.length > 0 ? (
        <View style={styles.sourcesSection}>
          <Text style={styles.sourcesTitle}>{sourcesTitle}</Text>
          <View style={styles.sourcesList}>
            {visibleSources.map((source) => (
              <SourceCard
                key={`${source.citation_id}-${source.source}-${source.page ?? "na"}`}
                source={source}
                showCitationId={!showRetrievedSources}
              />
            ))}
          </View>
        </View>
      ) : null}
    </View>
  )
}

const markdownStyles = StyleSheet.create({
  body: {
    color: "#17191C",
    fontSize: 16,
    lineHeight: 24,
  },
  paragraph: {
    marginTop: 0,
    marginBottom: 10,
  },
  strong: {
    fontWeight: "700",
  },
  bullet_list: {
    marginVertical: 4,
  },
  ordered_list: {
    marginVertical: 4,
  },
  list_item: {
    marginVertical: 3,
  },
  link: {
    textDecorationLine: "underline",
  },
})

const styles = StyleSheet.create({
  wrapper: {
    gap: 16,
  },
  groundingCard: {
    gap: 4,
    borderRadius: 12,
    padding: 12,
  },
  groundingVerified: {
    backgroundColor: "#F3F5F7",
  },
  groundingWarning: {
    backgroundColor: "#FFF7E6",
  },
  groundingTitle: {
    fontSize: 13,
    fontWeight: "700",
  },
  groundingText: {
    fontSize: 13,
    lineHeight: 18,
  },
  sourcesSection: {
    gap: 10,
    borderTopWidth: 1,
    borderTopColor: "#E1E4E8",
    paddingTop: 14,
  },
  sourcesTitle: {
    fontSize: 14,
    fontWeight: "700",
  },
  sourcesList: {
    gap: 10,
  },
  sourceCard: {
    gap: 6,
    borderWidth: 1,
    borderColor: "#E1E4E8",
    borderRadius: 14,
    padding: 12,
    backgroundColor: "#FAFBFC",
  },
  sourceHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
  },
  citationBadge: {
    fontSize: 13,
    fontWeight: "700",
  },
  sourceTitle: {
    flex: 1,
    fontSize: 14,
    fontWeight: "600",
  },
  sourceMeta: {
    fontSize: 12,
  },
  sourceExcerpt: {
    fontSize: 13,
    lineHeight: 18,
  },
})
