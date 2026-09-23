import { useState } from "react"
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native"
import { DemoCard } from "../components/demo-card"
import { useDemoTheme } from "../components/demo-shell-theme"
import { getDemoFocusOutline } from "../components/demo-tokens"

export const demoExamples = [
  { caseId: 0, query: "Quais vacinas são recomendadas para idosos?" },
  { caseId: 3, query: "Quais informações existem sobre o DIU de cobre?" },
] as const

function DemoExampleButton({ example, onPress }: { example: (typeof demoExamples)[number]; onPress: () => void }) {
  const theme = useDemoTheme()
  const [focused, setFocused] = useState(false)
  return <Pressable accessibilityRole="button" accessibilityLabel={`Usar exemplo: ${example.query}`} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} onPress={onPress} style={({ pressed }) => [styles.example, { borderColor: theme.border, backgroundColor: theme.surface }, pressed && styles.pressed, getDemoFocusOutline(theme, focused)]}><Text style={{ color: theme.action }}>{example.query}</Text></Pressable>
}

export function DemoChatScreen({ value, onChange, onExamplePress }: { value: string; onChange: (value: string) => void; onExamplePress: (example: (typeof demoExamples)[number]) => void }) {
  const theme = useDemoTheme()
  const [focused, setFocused] = useState(false)
  return <View style={styles.screen}><Text style={[styles.title, { color: theme.text }]}>Chat</Text><Text style={{ color: theme.textMuted }}>Explore a pergunta e observe como a futura execução será apresentada. Nesta etapa, nenhuma resposta é gerada.</Text><TextInput accessibilityHint="Digite uma pergunta para a futura demonstração" accessibilityLabel="Pergunta da demonstração" multiline value={value} onChangeText={onChange} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} placeholder="Escreva uma pergunta" placeholderTextColor={theme.textMuted} style={[styles.input, { color: theme.text, borderColor: focused ? theme.focusOutline : theme.border, backgroundColor: theme.surface, borderWidth: focused ? 3 : 1 }]} /><Text style={[styles.label, { color: theme.text }]}>Exemplos públicos de avaliação</Text><View style={styles.examples}>{demoExamples.map((example) => <DemoExampleButton key={example.caseId} example={example} onPress={() => onExamplePress(example)} />)}</View><DemoCard title="Conversa futura"><Text style={{ color: theme.textMuted }}>Ainda não há resposta, fontes, rankings ou tempos para exibir.</Text></DemoCard><DemoCard title="Fontes e grounding"><Text style={{ color: theme.textMuted }}>Os estados serão preenchidos somente após validação da execução M3.</Text></DemoCard><Pressable accessibilityLabel="Executar demonstração, disponível no M3" accessibilityRole="button" accessibilityState={{ disabled: true }} disabled style={[styles.future, { backgroundColor: theme.surfaceMuted }]}><Text style={{ color: theme.disabled }}>Executar demonstração · M3</Text></Pressable></View>
}
const styles = StyleSheet.create({ screen: { gap: 14 }, title: { fontSize: 24, fontWeight: "800" }, input: { minHeight: 96, borderWidth: 1, borderRadius: 12, padding: 14, fontSize: 16, textAlignVertical: "top" }, label: { fontWeight: "700" }, examples: { gap: 8 }, example: { minHeight: 48, justifyContent: "center", borderWidth: 1, borderRadius: 10, padding: 12 }, future: { minHeight: 48, justifyContent: "center", alignItems: "center", borderRadius: 10, padding: 12 }, pressed: { opacity: 0.78 } })
