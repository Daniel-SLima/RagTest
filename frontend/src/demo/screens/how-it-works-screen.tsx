import { useState } from "react"
import { StyleSheet, Text, View } from "react-native"
import { PipelineStage } from "../components/pipeline-stage"
import { useDemoTheme } from "../components/demo-shell-theme"

const stages = [
  ["question", "Pergunta", "A pergunta orienta a futura consulta.", "No M3, o texto será validado antes de entrar no contrato de execução."],
  ["retrieval", "Retrieval", "Documentos públicos relevantes serão recuperados.", "O modo e os filtros seguirão os schemas fechados do M1."],
  ["generation", "Geração", "Uma resposta poderá ser produzida por provider configurado.", "A geração permanece fora do M2 e exigirá revisão de privacidade."],
  ["citations", "Citações", "Fontes e grounding tornarão a resposta auditável.", "A cobertura estrutural de citações não equivale a prova clínica."],
] as const

export function HowItWorksScreen() {
  const theme = useDemoTheme()
  const [expanded, setExpanded] = useState<string | null>(null)
  return <View style={styles.screen}><Text style={[styles.title, { color: theme.text }]}>Como funciona</Text><Text style={{ color: theme.textMuted }}>A sequência abaixo explica a intenção do pipeline sem simular uma execução.</Text>{stages.map(([id, title, simpleExplanation, technicalDetails]) => <PipelineStage key={id} id={id} title={title} simpleExplanation={simpleExplanation} technicalDetails={technicalDetails} state="awaiting-execution" expanded={expanded === id} onToggle={() => setExpanded((current) => current === id ? null : id)} />)}</View>
}
const styles = StyleSheet.create({ screen: { gap: 12 }, title: { fontSize: 24, fontWeight: "800" } })
