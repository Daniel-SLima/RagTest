import { StyleSheet, Text, View } from "react-native"
import type { RoadmapItem as RoadmapItemType } from "../types/roadmap"
import { useDemoTheme } from "./demo-shell-theme"

export function RoadmapItem({ item }: { item: RoadmapItemType }) {
  const theme = useDemoTheme()
  return <View style={[styles.item, { backgroundColor: theme.surface, borderColor: theme.border }]}><View style={styles.heading}><Text style={[styles.title, { color: theme.text }]}>{item.title}</Text><Text style={[styles.status, { color: theme.action }]}>{item.status}</Text></View><Text style={{ color: theme.textMuted }}>{item.simpleExplanation}</Text><Text style={[styles.technical, { color: theme.text }]}>{item.technicalExplanation}</Text><Text style={{ color: theme.textMuted }}>Evidência: {item.evidence.map((evidence) => evidence.label).join("; ")}</Text></View>
}
const styles = StyleSheet.create({ item: { borderWidth: 1, borderRadius: 12, padding: 15, gap: 8 }, heading: { gap: 4 }, title: { fontSize: 16, fontWeight: "700" }, status: { fontSize: 12, fontWeight: "700", textTransform: "uppercase" }, technical: { lineHeight: 21 } })
