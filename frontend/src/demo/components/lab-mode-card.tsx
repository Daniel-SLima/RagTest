import { Pressable, StyleSheet, Text } from "react-native"
import { useDemoTheme } from "./demo-shell-theme"

export function LabModeCard({ title, description }: { title: string; description: string }) {
  const theme = useDemoTheme()
  return <Pressable accessibilityHint="Disponível em uma etapa futura" accessibilityLabel={`${title}, indisponível na M2`} accessibilityRole="button" accessibilityState={{ disabled: true }} disabled style={[styles.card, { borderColor: theme.border, backgroundColor: theme.surface }]}><Text style={[styles.title, { color: theme.text }]}>{title}</Text><Text style={{ color: theme.textMuted }}>{description}</Text><Text style={[styles.status, { color: theme.disabled }]}>Disponível no M3</Text></Pressable>
}
const styles = StyleSheet.create({ card: { minHeight: 48, borderWidth: 1, borderRadius: 12, padding: 14, gap: 7 }, title: { fontWeight: "700", fontSize: 16 }, status: { fontSize: 12, fontWeight: "700" } })
