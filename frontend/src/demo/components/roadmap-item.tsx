import { useState } from "react"
import { Pressable, StyleSheet, Text, View } from "react-native"

import type { RoadmapItem as RoadmapItemType } from "../types/roadmap"
import { useDemoTheme } from "./demo-shell-theme"
import { getDemoFocusOutline } from "./demo-tokens"
import { DemoStatusBadge, type DemoStatusTone } from "./demo-status-badge"

export const roadmapStatusLabels: Record<RoadmapItemType["status"], { label: string; tone: DemoStatusTone }> = {
  implemented: { label: "Implementado", tone: "success" },
  partial: { label: "Parcial / em desenvolvimento", tone: "warning" },
  planned: { label: "Planejado", tone: "neutral" },
  research: { label: "Em estudo", tone: "disabled" },
}

type RoadmapItemProps = {
  item: RoadmapItemType
  allItems: readonly RoadmapItemType[]
}

export function RoadmapItem({ item, allItems }: RoadmapItemProps) {
  const theme = useDemoTheme()
  const [expanded, setExpanded] = useState(false)
  const [focused, setFocused] = useState(false)
  const status = roadmapStatusLabels[item.status]
  const dependencies = item.dependencies
    .map((dependency) => allItems.find((candidate) => candidate.id === dependency)?.title)
    .filter((title): title is string => Boolean(title))

  return (
    <Pressable
      accessibilityHint="Expande ou recolhe os detalhes do item"
      accessibilityLabel={item.title}
      accessibilityRole="button"
      accessibilityState={{ expanded }}
      onBlur={() => setFocused(false)}
      onFocus={() => setFocused(true)}
      onPress={() => setExpanded((value) => !value)}
      style={({ pressed }) => [
        styles.item,
        { backgroundColor: theme.surface, borderColor: theme.border },
        pressed && styles.pressed,
        getDemoFocusOutline(theme, focused),
      ]}
    >
      <View style={styles.heading}>
        <Text style={[styles.title, { color: theme.text }]}>{item.title}</Text>
        <DemoStatusBadge label={status.label} tone={status.tone} />
      </View>
      <Text style={{ color: theme.textMuted }}>{item.simpleExplanation}</Text>
      {expanded ? (
        <View style={[styles.details, { borderTopColor: theme.border }]}>
          <Text style={[styles.sectionLabel, { color: theme.text }]}>Detalhes técnicos</Text>
          <Text style={{ color: theme.text }}>{item.technicalExplanation}</Text>
          <Text style={[styles.sectionLabel, { color: theme.text }]}>Por que importa?</Text>
          <Text style={{ color: theme.textMuted }}>{item.whyItMatters}</Text>
          <Text style={[styles.sectionLabel, { color: theme.text }]}>Limitações</Text>
          <Text style={{ color: theme.textMuted }}>
            {item.whyMissing ?? "Nenhuma limitação adicional registrada para este item."}
          </Text>
          {item.whyMissing ? (
            <View style={styles.subsection}>
              <Text style={[styles.sectionLabel, { color: theme.text }]}>Por que ainda falta?</Text>
              <Text style={{ color: theme.textMuted }}>{item.whyMissing}</Text>
            </View>
          ) : null}
          {dependencies.length > 0 ? (
            <View style={styles.subsection}>
              <Text style={[styles.sectionLabel, { color: theme.text }]}>Dependências</Text>
              <Text style={{ color: theme.textMuted }}>Depende de: {dependencies.join(", ")}</Text>
            </View>
          ) : null}
          <View style={styles.subsection}>
            <Text style={[styles.sectionLabel, { color: theme.text }]}>Evidências</Text>
            {item.evidence.map((evidence) => (
              <Text key={`${evidence.kind}-${evidence.reference}`} style={{ color: theme.textMuted }}>
                {evidence.label} — {evidence.reference}
              </Text>
            ))}
            <Text style={{ color: theme.textMuted }}>Origem: {item.origin}</Text>
          </View>
        </View>
      ) : null}
    </Pressable>
  )
}

const styles = StyleSheet.create({
  item: { borderWidth: 1, borderRadius: 12, padding: 15, gap: 8, minHeight: 48 },
  heading: { gap: 6 },
  title: { fontSize: 16, fontWeight: "700", lineHeight: 22 },
  details: { borderTopWidth: 1, paddingTop: 10, gap: 7 },
  sectionLabel: { fontSize: 13, fontWeight: "800" },
  subsection: { gap: 5 },
  pressed: { opacity: 0.82 },
})
