import { useState } from "react"
import { Pressable, StyleSheet, Text, View } from "react-native"
import { useDemoTheme } from "./demo-shell-theme"
import { getDemoFocusOutline } from "./demo-tokens"

export type PipelineStageProps = { id: string; title: string; simpleExplanation: string; technicalDetails: string; state: "awaiting-execution"; expanded: boolean; onToggle: () => void }

export function PipelineStage({ title, simpleExplanation, technicalDetails, state, expanded, onToggle }: PipelineStageProps) {
  const theme = useDemoTheme()
  const [focused, setFocused] = useState(false)
  const stateLabel = state === "awaiting-execution" ? "aguardando execução" : state
  return <Pressable accessibilityHint="Expande ou recolhe os detalhes técnicos" accessibilityLabel={title} accessibilityRole="button" accessibilityState={{ expanded }} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} onPress={onToggle} style={({ pressed }) => [styles.stage, { borderColor: theme.border, backgroundColor: theme.surface }, pressed && styles.pressed, getDemoFocusOutline(theme, focused)]}><View style={styles.heading}><Text style={[styles.title, { color: theme.text }]}>{title}</Text><Text accessibilityLabel={stateLabel} style={[styles.state, { color: theme.warning }]}>{stateLabel}</Text></View><Text style={{ color: theme.textMuted }}>{simpleExplanation}</Text>{expanded ? <Text style={[styles.details, { color: theme.text }]}>{technicalDetails}</Text> : null}</Pressable>
}
const styles = StyleSheet.create({ stage: { borderWidth: 1, borderRadius: 12, padding: 14, gap: 8, minHeight: 48 }, heading: { gap: 4 }, title: { fontSize: 16, fontWeight: "700" }, state: { fontSize: 12, fontWeight: "700" }, details: { lineHeight: 21 }, pressed: { opacity: 0.8 } })
