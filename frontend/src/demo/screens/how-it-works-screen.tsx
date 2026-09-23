import { useState } from "react"
import { StyleSheet, Text, View } from "react-native"
import { PipelineStage } from "../components/pipeline-stage"
import { useDemoTheme } from "../components/demo-shell-theme"

export const stages = [
  ["question", "Pergunta", "A pergunta orienta a futura consulta.", "No M3, o texto será validado antes de entrar no contrato de execução."],
  ["analysis", "Análise e decomposição", "A intenção pode ser organizada em partes verificáveis.", "A decomposição, quando aplicável, continua limitada ao contrato de consulta."],
  ["embedding", "Embedding", "A pergunta pode ser representada para busca semântica.", "O embedding usa o modelo configurado no pipeline, sem execução nesta tela."],
  ["qdrant", "Qdrant", "A coleção vetorial armazena os pontos documentais.", "A coleção e seus parâmetros permanecem somente leitura durante o M2."],
  ["retrieval", "Retrieval", "Documentos públicos relevantes serão recuperados.", "O modo e os filtros seguirão os schemas fechados do M1."],
  ["reranking", "Reranking", "Os candidatos podem ser reordenados por relevância.", "A reordenação será medida no replay futuro, sem fabricar ranking agora."],
  ["context", "Contexto", "Trechos selecionados formam o contexto da resposta.", "O contexto deverá respeitar limites de fonte e privacidade."],
  ["llm", "LLM", "Uma resposta poderá ser produzida por provider configurado.", "A geração permanece fora do M2 e exigirá revisão de privacidade."],
  ["citations", "Validação de citações", "As referências precisam corresponder aos trechos usados.", "A cobertura estrutural de citações não equivale a prova clínica."],
  ["grounding", "Grounding", "O estado indica se há base documental citável.", "Grounded é cobertura estrutural, não garantia de verdade clínica."],
  ["answer", "Resposta", "A resposta final apresenta a informação e suas fontes.", "A resposta só será exibida após uma execução controlada e auditável."],
] as const

export function HowItWorksScreen() {
  const theme = useDemoTheme()
  const [expanded, setExpanded] = useState<string | null>(null)
  return <View style={styles.screen}><Text style={[styles.title, { color: theme.text }]}>Como funciona</Text><Text style={{ color: theme.textMuted }}>A sequência abaixo explica a intenção do pipeline sem simular uma execução.</Text>{stages.map(([id, title, simpleExplanation, technicalDetails]) => <PipelineStage key={id} id={id} title={title} simpleExplanation={simpleExplanation} technicalDetails={technicalDetails} state="awaiting-execution" expanded={expanded === id} onToggle={() => setExpanded((current) => current === id ? null : id)} />)}</View>
}
const styles = StyleSheet.create({ screen: { gap: 12 }, title: { fontSize: 24, fontWeight: "800" } })
