import { Pressable, StyleSheet, Text, View } from "react-native"
import { DEMO_TABS, type DemoTabId } from "../types/navigation"
import { useDemoTheme } from "./demo-shell-theme"

export function DemoTabs({ activeTab, onTabChange }: { activeTab: DemoTabId; onTabChange: (tab: DemoTabId) => void }) {
  const theme = useDemoTheme()
  return <View accessibilityRole="tablist" testID="demo-tablist" style={styles.tabs}>{DEMO_TABS.map((tab) => {
    const selected = tab.id === activeTab
    return <Pressable key={tab.id} accessibilityHint={`Abre a seção ${tab.label}`} accessibilityLabel={tab.label} accessibilityRole="tab" accessibilityState={{ selected }} onPress={() => onTabChange(tab.id)} style={({ pressed }) => [styles.tab, { borderColor: selected ? theme.action : theme.border, backgroundColor: selected ? theme.surfaceMuted : theme.surface }, pressed && styles.pressed]}><Text style={[styles.tabText, { color: selected ? theme.action : theme.textMuted }]}>{tab.label}</Text></Pressable>
  })}</View>
}

const styles = StyleSheet.create({ tabs: { flexDirection: "row", flexWrap: "wrap", gap: 8, paddingBottom: 14 }, tab: { minHeight: 48, flexGrow: 1, flexBasis: 150, alignItems: "center", justifyContent: "center", borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10 }, tabText: { fontSize: 14, fontWeight: "700", textAlign: "center" }, pressed: { opacity: 0.75 } })
