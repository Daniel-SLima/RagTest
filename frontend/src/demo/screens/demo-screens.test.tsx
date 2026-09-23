import { fireEvent, render, screen } from "@testing-library/react-native"
import { DemoChatScreen, demoExamples } from "./demo-chat-screen"
import { HowItWorksScreen } from "./how-it-works-screen"
import { LaboratoryScreen } from "./laboratory-screen"
import { RoadmapScreen } from "./roadmap-screen"
import { DemoThemeProvider } from "../components/demo-shell-theme"
import { roadmap } from "../data/roadmap"

const renderDemo = (element: React.ReactElement) => render(<DemoThemeProvider>{element}</DemoThemeProvider>)

describe("M2 screens", () => {
  it("fills only the question when a public example is selected", async () => {
    const onExamplePress = jest.fn()
    await renderDemo(<DemoChatScreen value="" onChange={jest.fn()} onExamplePress={onExamplePress} />)
    await fireEvent.press(screen.getAllByRole("button", { name: /Usar exemplo/ })[0])
    expect(onExamplePress).toHaveBeenCalledWith(demoExamples[0])
    expect(screen.queryByText(/resposta é gerada/)).toBeTruthy()
  })
  it("shows all four neutral screen areas without fabricated results", async () => {
    await renderDemo(<HowItWorksScreen />); expect(screen.getAllByText("awaiting-execution")).toHaveLength(4)
    await renderDemo(<LaboratoryScreen />); expect(screen.getAllByText("Disponível no M3")).toHaveLength(3)
    await renderDemo(<RoadmapScreen />); expect(roadmap.length).toBeGreaterThan(0)
    expect(screen.getByText("O que ainda falta")).toBeTruthy()
  })
  it("keeps catalog statuses and evidence references closed", () => {
    for (const item of roadmap) { expect(["implemented", "partial", "planned", "research"]).toContain(item.status); expect(item.evidence.length).toBeGreaterThan(0); expect(item.snapshotVersion).toMatch(/^M[12]$/) }
    expect(JSON.stringify(roadmap)).not.toMatch(/CHATSCM|\.env|[A-Za-z]:\\|\/Users\//)
  })
})
