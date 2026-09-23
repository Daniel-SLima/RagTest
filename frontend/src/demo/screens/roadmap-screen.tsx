import { StyleSheet, Text, View } from "react-native"
import { roadmap } from "../data/roadmap"
import { RoadmapItem } from "../components/roadmap-item"
import { useDemoTheme } from "../components/demo-shell-theme"

export function RoadmapScreen() {
  const theme = useDemoTheme()
  return <View style={styles.screen}><Text style={[styles.title, { color: theme.text }]}>O que ainda falta</Text><Text style={{ color: theme.textMuted }}>Um catálogo curto separa o que tem evidência local do que ainda depende de validação.</Text>{roadmap.map((item) => <RoadmapItem key={item.id} item={item} />)}</View>
}
const styles = StyleSheet.create({ screen: { gap: 12 }, title: { fontSize: 24, fontWeight: "800" } })
