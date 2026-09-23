import { StyleSheet, Text, View } from "react-native"
import { useDemoTheme } from "./demo-shell-theme"

export function DemoHeader() {
  const theme = useDemoTheme()
  return <View style={styles.header}><Text style={[styles.eyebrow, { color: theme.action }]}>RagTest — Demo Técnica</Text><Text style={[styles.title, { color: theme.text }]}>Fundação visual do módulo RAG</Text><Text style={[styles.subtitle, { color: theme.textMuted }]}>Uma leitura transparente do pipeline, dos limites atuais e das próximas validações.</Text></View>
}

const styles = StyleSheet.create({ header: { gap: 6, paddingBottom: 18 }, eyebrow: { fontSize: 13, fontWeight: "800", letterSpacing: 1, textTransform: "uppercase" }, title: { fontSize: 28, fontWeight: "800", lineHeight: 34 }, subtitle: { fontSize: 16, lineHeight: 24 } })
