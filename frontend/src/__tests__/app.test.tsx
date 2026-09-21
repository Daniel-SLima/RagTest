import { fireEvent, render, screen, waitFor } from "@testing-library/react-native"

import App from "../../App"

describe("RagTest demo app", () => {
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

})
