import { Pressable, StyleSheet, Text, TextInput, View } from "react-native"

export default function App() {
  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>RagTest</Text>
        <Text style={styles.title}>Assistente de Saúde</Text>
        <Text style={styles.subtitle}>
          Informações baseadas em fontes oficiais de saúde.
        </Text>
      </View>

      <View style={styles.content}>
        <View style={styles.welcomeCard}>
          <Text style={styles.welcomeTitle}>Olá! Como posso ajudar?</Text>
          <Text style={styles.welcomeText}>
            Faça uma pergunta sobre saúde e consulte respostas fundamentadas
            nos documentos disponíveis no módulo RAG.
          </Text>
        </View>
      </View>

      <View style={styles.composer}>
        <TextInput
          accessibilityLabel="Pergunta"
          multiline
          placeholder="Digite sua pergunta..."
          style={styles.input}
        />
        <Pressable
          accessibilityLabel="Enviar"
          accessibilityRole="button"
          style={styles.sendButton}
        >
          <Text style={styles.sendButtonText}>Enviar</Text>
        </Pressable>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#F7F8FA",
    paddingHorizontal: 20,
    paddingTop: 56,
    paddingBottom: 24,
  },
  header: {
    gap: 6,
  },
  eyebrow: {
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  content: {
    flex: 1,
    justifyContent: "center",
    paddingVertical: 28,
  },
  welcomeCard: {
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    padding: 20,
    gap: 8,
  },
  welcomeTitle: {
    fontSize: 20,
    fontWeight: "700",
  },
  welcomeText: {
    fontSize: 15,
    lineHeight: 22,
  },
  composer: {
    gap: 12,
  },
  input: {
    minHeight: 56,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: "#D8DCE3",
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
  },
  sendButton: {
    minHeight: 50,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 14,
    backgroundColor: "#17191C",
  },
  sendButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
})
