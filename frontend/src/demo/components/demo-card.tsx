import type { PropsWithChildren } from "react"
import { Pressable, StyleSheet, Text, View } from "react-native"
import { useDemoTheme } from "./demo-shell-theme"

type DemoCardProps = PropsWithChildren<{
  title: string
  accessibilityLabel?: string
  expanded?: boolean
  disabled?: boolean
  onPress?: () => void
}>

export function DemoCard({
  title,
  children,
  accessibilityLabel,
  expanded,
  disabled,
  onPress,
}: DemoCardProps) {
  const theme = useDemoTheme()
  const content = (
    <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <Text style={[styles.title, { color: theme.text }]}>{title}</Text>
      {children}
    </View>
  )
  if (!onPress) return content
  return (
    <Pressable
      accessibilityLabel={accessibilityLabel ?? title}
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled ?? false, expanded }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [pressed && styles.pressed, disabled && styles.disabled]}
    >
      {content}
    </Pressable>
  )
}

const styles = StyleSheet.create({
  card: { borderWidth: 1, borderRadius: 14, padding: 16, gap: 10 },
  title: { fontSize: 17, fontWeight: "700", lineHeight: 24 },
  pressed: { opacity: 0.78 },
  disabled: { opacity: 0.55 },
})
