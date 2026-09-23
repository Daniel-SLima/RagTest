import { StyleSheet, Text, View } from "react-native"
import { useDemoTheme } from "./demo-shell-theme"

export type DemoStatusTone = "neutral" | "success" | "warning" | "disabled"

export function DemoStatusBadge({ label, tone }: { label: string; tone: DemoStatusTone }) {
  const theme = useDemoTheme()
  const color = tone === "success" ? theme.success : tone === "warning" ? theme.warning : tone === "disabled" ? theme.disabled : theme.textMuted
  return <View accessibilityRole="text" style={[styles.badge, { borderColor: color }]}><Text style={[styles.label, { color }]}>{label}</Text></View>
}

const styles = StyleSheet.create({ badge: { alignSelf: "flex-start", borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 5 }, label: { fontSize: 12, fontWeight: "700" } })
