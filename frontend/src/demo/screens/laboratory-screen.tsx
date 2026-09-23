import { StyleSheet, Text, View } from "react-native"
import { LabModeCard } from "../components/lab-mode-card"
import { useDemoTheme } from "../components/demo-shell-theme"

export function LaboratoryScreen() {
  const theme = useDemoTheme()
  return <View style={styles.screen}><Text style={[styles.title, { color: theme.text }]}>Laboratório</Text><Text style={{ color: theme.textMuted }}>Os modos abaixo documentam opções futuras. Eles permanecem inativos no M2.</Text><LabModeCard title="Dense" description="Busca semântica densa sobre a coleção validada." /><LabModeCard title="Dense + rerank" description="Busca densa com reordenação lexical." /><LabModeCard title="Hybrid" description="Combinação densa e esparsa com fusão." /><LabModeCard title="Estratégia" description="Escolha da estratégia de consulta será habilitada no M4." /><LabModeCard title="Top K" description="O limite de resultados será habilitado no M4." /><LabModeCard title="Multi-query" description="A decomposição de consultas será habilitada no M4." /><LabModeCard title="Pergunta" description="A execução de uma pergunta será habilitada no M4." /><LabModeCard title="Comparação" description="A comparação entre modos será habilitada no M4." /></View>
}
const styles = StyleSheet.create({ screen: { gap: 12 }, title: { fontSize: 24, fontWeight: "800" } })
