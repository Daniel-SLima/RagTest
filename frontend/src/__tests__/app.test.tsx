import { fireEvent, render, screen, waitFor } from "@testing-library/react-native"

import App from "../../App"
import { ChatApiError } from "../lib/chat-api"

describe("RagTest demo app", () => {
  const previousDemoFlag = process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED

  afterEach(() => {
    if (previousDemoFlag === undefined) delete process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED
    else process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED = previousDemoFlag
  })

  it.each([undefined, "", "false", "1", "yes"]) (
    "preserves the normal app when demo flag is %p",
    async (flag) => {
      if (flag === undefined) delete process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED
      else process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED = flag
      await render(<App />)
      expect(screen.getByText("Assistente de Saúde")).toBeTruthy()
      expect(screen.queryByText("Fundação visual do módulo RAG")).toBeNull()
    },
  )

  it("renders the demo only for an explicit true flag and never sends normal chat", async () => {
    process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED = " true "
    const sendChat = jest.fn()
    const demoApi = {
      getRuntime: jest.fn(),
      run: jest.fn(),
      retrieve: jest.fn(),
    }
    await render(<App sendChat={sendChat} demoApi={demoApi as never} />)
    expect(screen.getByText("Fundação visual do módulo RAG")).toBeTruthy()
    expect(screen.getAllByRole("tab")).toHaveLength(4)
    await fireEvent.press(screen.getByRole("tab", { name: "Laboratório" }))
    await fireEvent.press(screen.getByRole("tab", { name: "O que ainda falta" }))
    expect(sendChat).not.toHaveBeenCalled()
    expect(demoApi.getRuntime).not.toHaveBeenCalled()
    expect(demoApi.run).not.toHaveBeenCalled()
    expect(demoApi.retrieve).not.toHaveBeenCalled()
  })

  it("renders the initial chat surface", async () => {
    await render(<App />)

    expect(screen.getByText("Assistente de Saúde")).toBeTruthy()
    expect(screen.getByPlaceholderText("Digite sua pergunta...")).toBeTruthy()
    expect(screen.getByRole("button", { name: "Enviar" })).toBeTruthy()
  })

  it("sends the question and renders the API answer", async () => {
    const sendChat = jest.fn().mockResolvedValue({
      answer: "A vacinação deve seguir o calendário oficial [1].",
      model: "openai/gpt-oss-120b",
      grounded: true,
      citation_ids: [1],
      citation_retry_count: 0,
      multi_query_used: false,
      retrieval_queries: ["Quais vacinas são recomendadas?"],
      decomposition_status: "disabled",
      sources: [],
    })

    await render(
      <App
        apiBaseUrl="http://localhost:8000"
        sendChat={sendChat}
      />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Quais vacinas são recomendadas?",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    expect(screen.getByText("Quais vacinas são recomendadas?")).toBeTruthy()

    await waitFor(() => {
      expect(sendChat).toHaveBeenCalledWith(
        { message: "Quais vacinas são recomendadas?" },
        { baseUrl: "http://localhost:8000" },
      )
      expect(
        screen.getByText("A vacinação deve seguir o calendário oficial [1]."),
      ).toBeTruthy()
    })
  })


  it("renders a user-facing error when the API request fails", async () => {
    const sendChat = jest.fn().mockRejectedValue(new Error("offline"))

    await render(
      <App
        apiBaseUrl="http://localhost:8000"
        sendChat={sendChat}
      />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Quais vacinas?",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    await waitFor(() => {
      expect(
        screen.getByText(
          "Não foi possível obter uma resposta agora. Verifique a conexão e tente novamente.",
        ),
      ).toBeTruthy()
    })
  })

  it("explains temporary provider unavailability when the API returns 503", async () => {
    const sendChat = jest.fn().mockRejectedValue(
      new ChatApiError(503, "Provider quota detail that must not reach the user."),
    )

    await render(
      <App apiBaseUrl="http://localhost:8000" sendChat={sendChat} />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Quais vacinas?",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    await waitFor(() => {
      expect(
        screen.getByText(
          "O serviço de geração está temporariamente indisponível. Tente novamente em alguns instantes.",
        ),
      ).toBeTruthy()
      expect(
        screen.queryByText("Provider quota detail that must not reach the user."),
      ).toBeNull()
    })
  })

  it("retries the last question manually after a request failure", async () => {
    const successfulResponse = {
      answer: "A vacinação deve seguir o calendário oficial [1].",
      model: "openai/gpt-oss-120b",
      grounded: true,
      citation_ids: [1],
      citation_retry_count: 0,
      multi_query_used: false,
      retrieval_queries: ["Quais vacinas?"],
      decomposition_status: "not-needed",
      sources: [
        {
          citation_id: 1,
          score: 0.91,
          source: "vacinacao/calendario_nacional_vacinacao_idoso.pdf",
          category: "vacinacao",
          audience: "idoso",
          page: 1,
          chunk_count: 1,
          excerpt: "Vacinação da pessoa idosa.",
        },
      ],
    }
    const sendChat = jest
      .fn()
      .mockRejectedValueOnce(new ChatApiError(503, "Provider unavailable."))
      .mockResolvedValueOnce(successfulResponse)

    await render(
      <App apiBaseUrl="http://localhost:8000" sendChat={sendChat} />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Quais vacinas?",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    const retryButton = await screen.findByRole("button", {
      name: "Tentar novamente",
    })
    await fireEvent.press(retryButton)

    await waitFor(() => {
      expect(sendChat).toHaveBeenCalledTimes(2)
      expect(sendChat).toHaveBeenLastCalledWith(
        { message: "Quais vacinas?" },
        { baseUrl: "http://localhost:8000" },
      )
      expect(
        screen.getByText("A vacinação deve seguir o calendário oficial [1]."),
      ).toBeTruthy()
      expect(
        screen.queryByRole("button", { name: "Tentar novamente" }),
      ).toBeNull()
    })
  })

  it("renders markdown formatting and source cards for a grounded answer", async () => {
    const sendChat = jest.fn().mockResolvedValue({
      answer:
        "1. **Vacina contra Influenza** — deve ser tomada anualmente [1].",
      model: "openai/gpt-oss-120b",
      grounded: true,
      citation_ids: [1],
      citation_retry_count: 0,
      multi_query_used: false,
      retrieval_queries: ["Quais vacinas são recomendadas?"],
      decomposition_status: "disabled",
      sources: [
        {
          citation_id: 1,
          score: 0.91,
          source: "vacinacao/calendario_nacional_vacinacao_idoso.pdf",
          category: "vacinacao",
          audience: "idoso",
          page: 1,
          chunk_count: 1,
          excerpt: "Vacinação da pessoa idosa.",
        },
      ],
    })

    await render(
      <App
        apiBaseUrl="http://localhost:8000"
        sendChat={sendChat}
      />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Quais vacinas são recomendadas?",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    await waitFor(() => {
      expect(screen.getByText("Vacina contra Influenza")).toBeTruthy()
      expect(screen.queryByText(/\*\*Vacina contra Influenza\*\*/)).toBeNull()
      expect(screen.getByText("Fontes consultadas")).toBeTruthy()
      expect(
        screen.getByText("calendario_nacional_vacinacao_idoso.pdf"),
      ).toBeTruthy()
      expect(screen.getByText("Página 1")).toBeTruthy()
      expect(screen.getByText("[1]")).toBeTruthy()
    })
  })


  it("shows only sources actually cited by the answer", async () => {
    const sendChat = jest.fn().mockResolvedValue({
      answer: "**Direito citado** [1].",
      model: "openai/gpt-oss-120b",
      grounded: true,
      citation_ids: [1],
      citation_retry_count: 0,
      multi_query_used: false,
      retrieval_queries: ["Quais são meus direitos?"],
      decomposition_status: "disabled",
      sources: [
        {
          citation_id: 1,
          score: 0.9,
          source: "direitos_saude/fonte_citada.pdf",
          category: "direitos_saude",
          audience: null,
          page: 4,
          chunk_count: 1,
          excerpt: "Fonte usada na resposta.",
        },
        {
          citation_id: 2,
          score: 0.8,
          source: "direitos_saude/fonte_nao_citada.pdf",
          category: "direitos_saude",
          audience: null,
          page: 10,
          chunk_count: 1,
          excerpt: "Fonte recuperada, mas não citada.",
        },
      ],
    })

    await render(
      <App
        apiBaseUrl="http://localhost:8000"
        sendChat={sendChat}
      />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Quais são meus direitos?",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    await waitFor(() => {
      expect(screen.getByText("fonte_citada.pdf")).toBeTruthy()
      expect(screen.queryByText("fonte_nao_citada.pdf")).toBeNull()
    })
  })


  it("shows a verified-citations status for grounded answers", async () => {
    const sendChat = jest.fn().mockResolvedValue({
      answer: "A vacinação deve seguir o calendário oficial [1].",
      model: "openai/gpt-oss-120b",
      grounded: true,
      citation_ids: [1],
      citation_retry_count: 0,
      multi_query_used: false,
      retrieval_queries: ["Quais vacinas são recomendadas?"],
      decomposition_status: "not-needed",
      sources: [
        {
          citation_id: 1,
          score: 0.91,
          source: "vacinacao/calendario_nacional_vacinacao_idoso.pdf",
          category: "vacinacao",
          audience: "idoso",
          page: 1,
          chunk_count: 1,
          excerpt: "Vacinação da pessoa idosa.",
        },
      ],
    })

    await render(
      <App apiBaseUrl="http://localhost:8000" sendChat={sendChat} />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Quais vacinas são recomendadas?",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    await waitFor(() => {
      expect(screen.getByText("Citações verificadas")).toBeTruthy()
      expect(
        screen.getByText(
          "As afirmações informativas estão acompanhadas de referências do corpus.",
        ),
      ).toBeTruthy()
    })
  })

  it("shows retrieved sources separately when citation grounding fails", async () => {
    const sendChat = jest.fn().mockResolvedValue({
      answer:
        "Não foi possível gerar uma resposta com citações verificáveis a partir dos trechos recuperados. Consulte as fontes retornadas antes de usar a informação.",
      model: "openai/gpt-oss-120b",
      grounded: false,
      citation_ids: [],
      citation_retry_count: 1,
      multi_query_used: false,
      retrieval_queries: ["Quais vacinas são recomendadas?"],
      decomposition_status: "not-needed",
      sources: [
        {
          citation_id: 1,
          score: 0.84,
          source: "vacinacao/calendario_nacional_vacinacao_idoso.pdf",
          category: "vacinacao",
          audience: "idoso",
          page: 1,
          chunk_count: 1,
          excerpt: "Vacinação da pessoa idosa.",
        },
      ],
    })

    await render(
      <App apiBaseUrl="http://localhost:8000" sendChat={sendChat} />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Quais vacinas são recomendadas?",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    await waitFor(() => {
      expect(screen.getByText("Citações não verificadas")).toBeTruthy()
      expect(
        screen.getByText(
          "Não foi possível validar as citações desta resposta. Consulte as fontes recuperadas abaixo.",
        ),
      ).toBeTruthy()
      expect(screen.getByText("Fontes recuperadas para consulta")).toBeTruthy()
      expect(
        screen.getByText("calendario_nacional_vacinacao_idoso.pdf"),
      ).toBeTruthy()
      expect(screen.queryByText("[1]")).toBeNull()
    })
  })

  it("shows insufficient-document-basis status when no sources were retrieved", async () => {
    const sendChat = jest.fn().mockResolvedValue({
      answer:
        "Não encontrei trechos com relevância suficiente na base documental para responder a essa pergunta.",
      model: "openai/gpt-oss-120b",
      grounded: false,
      citation_ids: [],
      citation_retry_count: 0,
      multi_query_used: false,
      retrieval_queries: ["Pergunta sem cobertura"],
      decomposition_status: "not-needed",
      sources: [],
    })

    await render(
      <App apiBaseUrl="http://localhost:8000" sendChat={sendChat} />,
    )

    await fireEvent.changeText(
      screen.getByPlaceholderText("Digite sua pergunta..."),
      "Pergunta sem cobertura",
    )
    await fireEvent.press(screen.getByRole("button", { name: "Enviar" }))

    await waitFor(() => {
      expect(screen.getByText("Sem base documental suficiente")).toBeTruthy()
      expect(
        screen.getByText(
          "Não foram encontrados trechos relevantes o bastante para fundamentar uma resposta.",
        ),
      ).toBeTruthy()
      expect(screen.queryByText("Fontes recuperadas para consulta")).toBeNull()
    })
  })

})
