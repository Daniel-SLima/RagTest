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

function SourceCard({ source }: { source: ChatSource }) {
  return (
    <View style={styles.sourceCard}>
      <View style={styles.sourceHeader}>
        <Text style={styles.citationBadge}>[{source.citation_id}]</Text>
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

export function AssistantAnswer({ response }: AssistantAnswerProps) {
  return (
    <View style={styles.wrapper}>
      <Markdown style={markdownStyles}>{response.answer}</Markdown>

      {response.sources.length > 0 ? (
        <View style={styles.sourcesSection}>
          <Text style={styles.sourcesTitle}>Fontes consultadas</Text>
          <View style={styles.sourcesList}>
            {response.sources.map((source) => (
              <SourceCard
                key={`${source.citation_id}-${source.source}-${source.page ?? "na"}`}
                source={source}
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
