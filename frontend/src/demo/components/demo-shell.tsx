import type { PropsWithChildren } from "react"
import { Platform, SafeAreaView, ScrollView, StyleSheet, Text, View, useWindowDimensions } from "react-native"
import type { DemoTabId } from "../types/navigation"
import { getDemoLayout } from "./demo-tokens"
import { DemoHeader } from "./demo-header"
import { DemoTabs } from "./demo-tabs"
import { DemoThemeProvider, useDemoTheme } from "./demo-shell-theme"

type DemoShellProps = PropsWithChildren<{ activeTab: DemoTabId; onTabChange: (tab: DemoTabId) => void; runtimeState?: string }>

function DemoShellContent({ activeTab, onTabChange, runtimeState, children }: DemoShellProps) {
  const { width, height } = useWindowDimensions()
  const layout = getDemoLayout(width, height, Platform.OS === "web" ? "web" : "native")
  const theme = useDemoTheme()
  return <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}><ScrollView contentContainerStyle={[styles.scroll, { paddingHorizontal: layout.gutter }]} contentInsetAdjustmentBehavior="automatic" automaticallyAdjustKeyboardInsets keyboardShouldPersistTaps="handled"><View style={[styles.container, { width: layout.containerWidth, maxWidth: "100%" }]}><DemoHeader /><Text accessibilityRole="text" style={[styles.notice, { color: theme.textMuted, borderColor: theme.border, backgroundColor: theme.surface }]}>Modo local de desenvolvimento. Esta não é a versão final do produto Se Cuida Mulher.</Text><DemoTabs activeTab={activeTab} onTabChange={onTabChange} /><View accessibilityRole="text" style={[styles.runtime, { borderColor: theme.border }]}><Text style={{ color: theme.textMuted }}>{runtimeState ?? "Runtime aguardando validação"}</Text></View>{children}</View></ScrollView></SafeAreaView>
}

export function DemoShell(props: DemoShellProps) { return <DemoThemeProvider><DemoShellContent {...props} /></DemoThemeProvider> }

const styles = StyleSheet.create({ safe: { flex: 1 }, scroll: { flexGrow: 1, paddingVertical: 24 }, container: { alignSelf: "center", gap: 12 }, notice: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, fontSize: 13 }, runtime: { minHeight: 40, borderBottomWidth: 1, justifyContent: "center" }, })
