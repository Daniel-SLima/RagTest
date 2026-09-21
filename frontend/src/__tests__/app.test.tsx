import { render, screen } from "@testing-library/react-native"

import App from "../../App"

describe("RagTest demo app", () => {
  it("renders the initial chat surface", async () => {
    await render(<App />)

    expect(screen.getByText("Assistente de Saúde")).toBeTruthy()
    expect(screen.getByPlaceholderText("Digite sua pergunta...")).toBeTruthy()
    expect(screen.getByRole("button", { name: "Enviar" })).toBeTruthy()
  })
})
