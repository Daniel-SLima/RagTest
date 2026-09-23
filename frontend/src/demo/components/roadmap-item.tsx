import { StyleSheet, Text, View } from "react-native"
import type { RoadmapItem as RoadmapItemType } from "../types/roadmap"
import { useDemoTheme } from "./demo-shell-theme"
import { DemoStatusBadge, type DemoStatusTone } from "./demo-status-badge"

const statusLabels: Record<RoadmapItemType["status"], { label: string; tone: DemoStatusTone }> = {
  implemented: { label: "Implementado", tone: "success" },
  partial: { label: "Parcial / em desenvolvimento", tone: "warning" },
  planned: { label: "Planejado", tone: "neutral" },
  research: { label: "Em estudo", tone: "disabled" },
}

export function RoadmapItem({ item }: { item: RoadmapItemType }) {
  const theme = useDemoTheme()
  const status = statusLabels[item.status]
  return <View style={[styles.item, { backgroundColor: theme.surface, borderColor: theme.border }]}><View style={styles.heading}><Text style={[styles.title, { color: theme.text }]}>{item.title}</Text><DemoStatusBadge label={status.label} tone={status.tone} /></View><Text style={{ color: theme.textMuted }}>{item.simpleExplanation}</Text><Text style={[styles.technical, { color: theme.text }]}>{item.technicalExplanation}</Text><Text style={{ color: theme.textMuted }}>Evidência: {item.evidence.map((evidence) => evidence.label).join("; ")}</Text></View>
}
const styles = StyleSheet.create({ item: { borderWidth: 1, borderRadius: 12, padding: 15, gap: 8 }, heading: { gap: 4 }, title: { fontSize: 16, fontWeight: "700" }, status: { fontSize: 12, fontWeight: "700", textTransform: "uppercase" }, technical: { lineHeight: 21 } })
