import { useEffect, useMemo, useReducer, useRef, useState } from "react"
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
import { isDemoEnabled } from "./src/demo/config"
import { createDemoApi, type DemoApi } from "./src/demo/api/demo-api"
import { DemoShell } from "./src/demo/components/demo-shell"
import { DemoChatScreen } from "./src/demo/screens/demo-chat-screen"
import { HowItWorksScreen } from "./src/demo/screens/how-it-works-screen"
import { LaboratoryScreen } from "./src/demo/screens/laboratory-screen"
import { RoadmapScreen } from "./src/demo/screens/roadmap-screen"
import type { DemoTabId } from "./src/demo/types/navigation"
import { getAllowedHttpsOrigins, validateDemoRequest } from "./src/demo/api/demo-api-validation"
import { demoRunReducer, initialDemoRunState, sanitizeDemoError } from "./src/demo/state/demo-run-state"

type SendChat = typeof sendChatMessage

type AppProps = {
  apiBaseUrl?: string
  sendChat?: SendChat
  demoApi?: DemoApi
}

const DEFAULT_API_BASE_URL =
  process.env.EXPO_PUBLIC_RAG_API_BASE_URL ?? "http://localhost:8000"

export function NormalApp({
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

export function DemoApp({
  apiBaseUrl = DEFAULT_API_BASE_URL,
  demoApi,
}: Pick<AppProps, "apiBaseUrl"> & { demoApi?: DemoApi }) {
  const [activeTab, setActiveTab] = useState<DemoTabId>("chat")
  const [draft, setDraft] = useState("")
  const [pipelineMode, setPipelineMode] = useState<"auto" | "presentation">("auto")
  const [presentationIndex, setPresentationIndex] = useState(0)
  const [state, dispatch] = useReducer(demoRunReducer, initialDemoRunState)
  const apiResult = useMemo(() => {
    if (demoApi) return { api: demoApi, error: null }
    try { return { api: createDemoApi(apiBaseUrl, undefined, getAllowedHttpsOrigins(process.env.EXPO_PUBLIC_RAG_ALLOWED_HTTPS_ORIGINS)), error: null } }
    catch (error) { return { api: null, error: sanitizeDemoError(error) } }
  }, [apiBaseUrl, demoApi])
  const api = apiResult.api
  const configError = apiResult.error
  const runtimePromise = useRef<Promise<Awaited<ReturnType<DemoApi["getRuntime"]>>> | null>(null)
  const runtimeApi = useRef<DemoApi | null>(null)
  useEffect(() => {
    if (!api) return
    if (!runtimePromise.current || runtimeApi.current !== api) {
      runtimeApi.current = api
      dispatch({ type: "runtime-loading" })
      runtimePromise.current = Promise.resolve().then(() => api.getRuntime())
    }
    let active = true
    void runtimePromise.current.then((runtime) => { if (active) dispatch({ type: "runtime-success", runtime }) }).catch((error) => { if (active) dispatch({ type: "runtime-error", error: sanitizeDemoError(error) }) })
    return () => { active = false }
  }, [api])
  const submit = (question: string) => {
    const query = question.trim()
    if (!api || query.length < 2 || state.status === "loading") return
    let request: ReturnType<typeof validateDemoRequest>
    try { request = validateDemoRequest({ query }) } catch (error) { dispatch({ type: "run-invalid", question: query, error: sanitizeDemoError(error) }); return }
    dispatch({ type: "run-loading", question: request.query })
    void api.run(request).then((response) => dispatch({ type: "run-success", response })).catch((error) => dispatch({ type: "run-error", error: sanitizeDemoError(error) }))
  }
  const retry = () => { if (state.question && state.status !== "loading") submit(state.question) }
  const viewPipeline = () => { setActiveTab("how-it-works"); setPipelineMode("presentation"); setPresentationIndex(0) }
  const runtimeLabel = configError ? "Configuração da demo indisponível" : state.runtimeStatus === "loading" ? "Runtime consultando..." : state.runtimeStatus === "error" ? "Runtime indisponível" : state.runtime ? `Runtime ${state.runtime.provider} · ${state.runtime.model}` : "Runtime aguardando validação"

  return (
    <DemoShell activeTab={activeTab} onTabChange={setActiveTab} runtimeState={runtimeLabel}>
      {activeTab === "chat" ? (
        <DemoChatScreen
          value={draft}
          onChange={setDraft}
          onExamplePress={(example) => setDraft(example.query)}
          state={configError ? { ...state, status: "error", error: configError } : state}
          onSubmit={submit}
          onRetry={retry}
          onViewPipeline={viewPipeline}
        />
      ) : null}
      {activeTab === "how-it-works" ? <HowItWorksScreen state={state} mode={pipelineMode} presentationIndex={presentationIndex} onModeChange={setPipelineMode} onPresentationIndexChange={setPresentationIndex} /> : null}
      {activeTab === "laboratory" ? <LaboratoryScreen /> : null}
      {activeTab === "roadmap" ? <RoadmapScreen /> : null}
    </DemoShell>
  )
}

export default function App(props: AppProps) {
  return isDemoEnabled() ? <DemoApp {...props} /> : <NormalApp {...props} />
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
