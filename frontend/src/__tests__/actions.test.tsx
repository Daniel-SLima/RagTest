import { fireEvent, render, screen, waitFor } from "@testing-library/react-native"

import App from "../../App"
import type { ChatApiResponse } from "../lib/chat-api"

function response(overrides: Partial<ChatApiResponse>): ChatApiResponse {
  return {
    answer: "Resposta [1].",
    model: "fake",
    grounded: true,
    citation_ids: [1],
    citation_retry_count: 0,
    multi_query_used: false,
    retrieval_queries: ["q"],
    decomposition_status: "disabled",
    sources: [],
    safety: { triaged: false, rule_id: null, out_of_scope: false },
    actions: [],
    ...overrides,
  }
}

async function ask(question: string) {
  await fireEvent.changeText(screen.getByPlaceholderText("Digite sua pergunta..."), question)
  await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))
}

describe("structured actions", () => {
  it("highlights triaged answers and calls the emergency number", async () => {
    const openUrl = jest.fn().mockResolvedValue(undefined)
    const sendChat = jest.fn().mockResolvedValue(
      response({
        answer: "Procure agora a maternidade.",
        grounded: false,
        citation_ids: [],
        model: "triagem-deterministica",
        safety: { triaged: true, rule_id: "sangramento", out_of_scope: false },
        actions: [{ type: "call_emergency", label: "Ligar para o SAMU (192)", url: "tel:192", service_id: null, suggested_in_days: null }],
      }),
    )

    await render(<App sendChat={sendChat} openUrl={openUrl} />)
    await ask("estou grávida e sangrando")

    await waitFor(() => expect(screen.getByText("Sinal de alerta")).toBeTruthy())
    await fireEvent.press(screen.getByRole("button", { name: "Ligar para o SAMU (192)" }))

    expect(openUrl).toHaveBeenCalledWith("tel:192")
  })

  it("schedules a reminder and lists it with the due date", async () => {
    const sendChat = jest.fn().mockResolvedValue(
      response({
        actions: [
          { type: "open_link", label: "Ver unidades de saúde", url: "seucuida://unidades", service_id: "mamografia", suggested_in_days: null },
          { type: "schedule_reminder", label: "Mamografia de rastreamento: a cada 2 anos", url: null, service_id: "mamografia", suggested_in_days: 730 },
        ],
      }),
    )

    await render(<App sendChat={sendChat} now={() => new Date(2026, 8, 28)} />)
    await ask("como agendo a mamografia")

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Lembrar: Mamografia de rastreamento: a cada 2 anos" })).toBeTruthy(),
    )
    await fireEvent.press(
      screen.getByRole("button", { name: "Lembrar: Mamografia de rastreamento: a cada 2 anos" }),
    )

    expect(screen.getByText("Meus lembretes")).toBeTruthy()
    expect(screen.getByText("Mamografia de rastreamento: a cada 2 anos — 27/09/2028")).toBeTruthy()
  })

  it("explains app-only links instead of opening them", async () => {
    const openUrl = jest.fn()
    const sendChat = jest.fn().mockResolvedValue(
      response({
        actions: [
          { type: "open_link", label: "Ver unidades de saúde", url: "seucuida://unidades", service_id: "preventivo", suggested_in_days: null },
        ],
      }),
    )

    await render(<App sendChat={sendChat} openUrl={openUrl} />)
    await ask("onde marco o preventivo")

    await waitFor(() => expect(screen.getByRole("button", { name: "Ver unidades de saúde" })).toBeTruthy())
    await fireEvent.press(screen.getByRole("button", { name: "Ver unidades de saúde" }))

    expect(openUrl).not.toHaveBeenCalled()
    expect(screen.getByText("Este atalho abre a tela correspondente no app Se Cuida Mulher.")).toBeTruthy()
  })

  it("sends a suggested question from the welcome screen", async () => {
    const sendChat = jest.fn().mockResolvedValue(response({}))

    await render(<App sendChat={sendChat} />)
    await fireEvent.press(screen.getByRole("button", { name: "Quando devo fazer o preventivo?" }))

    await waitFor(() =>
      expect(sendChat).toHaveBeenCalledWith(
        { message: "Quando devo fazer o preventivo?" },
        { baseUrl: "http://localhost:8000" },
      ),
    )
  })

  it("keeps working with older responses without safety or actions", async () => {
    const legacy = response({})
    delete (legacy as Partial<ChatApiResponse>).safety
    delete (legacy as Partial<ChatApiResponse>).actions
    const sendChat = jest.fn().mockResolvedValue(legacy)

    await render(<App sendChat={sendChat} />)
    await ask("pergunta antiga")

    await waitFor(() => expect(screen.getByText("Resposta [1].")).toBeTruthy())
    expect(screen.queryByText("Sinal de alerta")).toBeNull()
  })
})
