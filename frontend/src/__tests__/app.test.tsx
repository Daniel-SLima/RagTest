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

})
