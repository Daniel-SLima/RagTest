import { useEffect, useRef, useState } from "react"
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native"

import { AssistantAnswer } from "./src/components/assistant-answer"
import {
  ChatApiError,
  type ChatApiResponse,
  sendChatMessage,
} from "./src/lib/chat-api"

type SendChat = typeof sendChatMessage

type AppProps = {
  apiBaseUrl?: string
  sendChat?: SendChat
}

const DEFAULT_API_BASE_URL =
  process.env.EXPO_PUBLIC_RAG_API_BASE_URL ?? "http://localhost:8000"

export default function App({
  apiBaseUrl = DEFAULT_API_BASE_URL,
  sendChat = sendChatMessage,
}: AppProps) {
  const conversationRef = useRef<ScrollView>(null)
  const [draft, setDraft] = useState("")
  const [question, setQuestion] = useState<string | null>(null)
  const [response, setResponse] = useState<ChatApiResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSend = draft.trim().length >= 2 && !isLoading

  useEffect(() => {
    conversationRef.current?.scrollToEnd({ animated: false })
  }, [error, isLoading, response])

  async function requestAnswer(message: string) {
    if (isLoading) {
      return
    }

    setQuestion(message)
    setResponse(null)
    setError(null)
    setIsLoading(true)

    try {
      const result = await sendChat(
        { message },
        { baseUrl: apiBaseUrl },
      )
      setResponse(result)
    } catch (requestError) {
      setError(
        requestError instanceof ChatApiError && requestError.status === 503
          ? "O serviço de geração está temporariamente indisponível. Tente novamente em alguns instantes."
          : "Não foi possível obter uma resposta agora. Verifique a conexão e tente novamente.",
      )
    } finally {
      setIsLoading(false)
    }
  }

  async function handleSend() {
    const message = draft.trim()
    if (message.length < 2 || isLoading) {
      return
    }

    setDraft("")
    await requestAnswer(message)
  }

  async function handleRetry() {
    if (!question || isLoading) {
      return
    }

    await requestAnswer(question)
  }

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>RagTest</Text>
        <Text style={styles.title}>Assistente de Saúde</Text>
        <Text style={styles.subtitle}>
          Informações baseadas em fontes oficiais de saúde.
        </Text>
      </View>

      <ScrollView
        contentContainerStyle={[
          styles.content,
          question ? styles.contentConversation : styles.contentWelcome,
        ]}
        ref={conversationRef}
      >
        {!question ? (
          <View style={styles.welcomeCard}>
            <Text style={styles.welcomeTitle}>Olá! Como posso ajudar?</Text>
            <Text style={styles.welcomeText}>
              Faça uma pergunta sobre saúde e consulte respostas fundamentadas
              nos documentos disponíveis no módulo RAG.
            </Text>
          </View>
        ) : (
          <View style={styles.conversation}>
            <View style={styles.userMessage}>
              <Text style={styles.messageLabel}>Você</Text>
              <Text style={styles.messageText}>{question}</Text>
            </View>

            {isLoading ? (
              <View style={styles.assistantMessage}>
                <ActivityIndicator accessibilityLabel="Carregando resposta" />
                <Text style={styles.loadingText}>Buscando resposta...</Text>
              </View>
            ) : null}

            {response ? (
              <View style={styles.assistantMessage}>
                <Text style={styles.messageLabel}>Assistente</Text>
                <AssistantAnswer response={response} />
              </View>
            ) : null}

            {error ? (
              <View style={styles.errorCard}>
                <Text style={styles.errorText}>{error}</Text>
                <Pressable
                  accessibilityLabel="Tentar novamente"
                  accessibilityRole="button"
                  accessibilityState={{ disabled: isLoading }}
                  disabled={isLoading}
                  onPress={handleRetry}
                  style={styles.retryButton}
                >
                  <Text style={styles.retryButtonText}>Tentar novamente</Text>
                </Pressable>
              </View>
            ) : null}
          </View>
        )}
      </ScrollView>

      <View style={styles.composer}>
        <TextInput
          accessibilityLabel="Pergunta"
          multiline
          onChangeText={setDraft}
          placeholder="Digite sua pergunta..."
          style={styles.input}
          value={draft}
        />
        <Pressable
          accessibilityLabel="Enviar"
          accessibilityRole="button"
          accessibilityState={{ disabled: !canSend }}
          disabled={!canSend}
          onPress={handleSend}
          style={[styles.sendButton, !canSend && styles.sendButtonDisabled]}
        >
          <Text style={styles.sendButtonText}>
            {isLoading ? "Enviando..." : "Enviar"}
          </Text>
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
    flexGrow: 1,
    paddingVertical: 28,
  },
  contentWelcome: {
    justifyContent: "center",
  },
  contentConversation: {
    justifyContent: "flex-end",
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
  conversation: {
    gap: 14,
  },
  userMessage: {
    alignSelf: "flex-end",
    maxWidth: "88%",
    borderRadius: 18,
    backgroundColor: "#E8EBEF",
    padding: 16,
    gap: 4,
  },
  assistantMessage: {
    alignSelf: "flex-start",
    maxWidth: "92%",
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    padding: 16,
    gap: 8,
  },
  messageLabel: {
    fontSize: 12,
    fontWeight: "700",
  },
  messageText: {
    fontSize: 16,
    lineHeight: 24,
  },
  loadingText: {
    fontSize: 14,
  },
  errorCard: {
    borderRadius: 16,
    backgroundColor: "#FFF1F1",
    padding: 16,
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    lineHeight: 20,
  },
  retryButton: {
    alignSelf: "flex-start",
    borderRadius: 12,
    backgroundColor: "#7A2020",
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
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
  sendButtonDisabled: {
    opacity: 0.45,
  },
  sendButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
})
