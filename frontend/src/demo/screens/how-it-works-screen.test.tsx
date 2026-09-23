import { fireEvent, render, screen } from "@testing-library/react-native"
import { DemoThemeProvider } from "../components/demo-shell-theme"
import { HowItWorksScreen } from "./how-it-works-screen"

describe("HowItWorksScreen live presentation", () => {
  it("shows empty guidance without fabricated execution", async () => {
    await render(<DemoThemeProvider><HowItWorksScreen /></DemoThemeProvider>)
    expect(screen.getByText("Execute uma pergunta no Chat para visualizar o pipeline")).toBeTruthy()
  })
  it("changes presentation controls without an API", async () => {
    const onModeChange = jest.fn(); const onIndex = jest.fn()
    await render(<DemoThemeProvider><HowItWorksScreen mode="presentation" onModeChange={onModeChange} onPresentationIndexChange={onIndex} /></DemoThemeProvider>)
    expect(screen.getAllByRole("button", { name: /Anterior|Próximo|Ver tudo|Apresentação/ }).length).toBeGreaterThan(0)
    await fireEvent.press(screen.getByRole("button", { name: "Automático" })); expect(onModeChange).toHaveBeenCalledWith("auto")
  })
})
