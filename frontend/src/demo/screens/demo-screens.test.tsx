import { fireEvent, render, screen } from "@testing-library/react-native"
import { DemoChatScreen, demoExamples } from "./demo-chat-screen"
import { HowItWorksScreen, stages } from "./how-it-works-screen"
import { LaboratoryScreen } from "./laboratory-screen"
import { RoadmapScreen } from "./roadmap-screen"
import { DemoThemeProvider } from "../components/demo-shell-theme"
import { roadmap } from "../data/roadmap"
import type { DemoRunState } from "../types/run-state"

const renderDemo = (element: React.ReactElement) => render(<DemoThemeProvider>{element}</DemoThemeProvider>)
const liveState: DemoRunState = { question: "TEST DATA", response: { answer: "Resposta TEST DATA **segura**.", model: "TEST DATA", grounded: true, citation_ids: [1], sources: [{ public_id: "public-1", document: "public/doc.pdf", page: 2, order: 1, excerpt: "Trecho TEST DATA", scores: { dense_score: 0.9, sparse_score: null, rank_score: null, fusion_score: null } }], timings: { retrieval_ms: 2, generation_ms: null, total_ms: 3 } }, diagnostics: null, runtime: null, runtimeStatus: "success", runtimeError: null, status: "success", error: null }

describe("M2 screens", () => {
  it("fills only the question when a public example is selected", async () => {
    const onExamplePress = jest.fn()
    await renderDemo(<DemoChatScreen value="" onChange={jest.fn()} onExamplePress={onExamplePress} />)
    await fireEvent.press(screen.getAllByRole("button", { name: /Usar exemplo/ })[0])
    expect(onExamplePress).toHaveBeenCalledWith(demoExamples[0])
    expect(screen.queryByText(/resposta é gerada/)).toBeTruthy()
    expect(screen.getByRole("button", { name: /Ver como essa resposta foi construída/ }).props.accessibilityState).toEqual({ disabled: true })
  })

  it("applies the visible focus outline to public example controls", async () => {
    await renderDemo(<DemoChatScreen value="" onChange={jest.fn()} onExamplePress={jest.fn()} />)
    const example = screen.getAllByRole("button", { name: /Usar exemplo/ })[0]
    await fireEvent(example, "focus")
    const style = example.props.style
    expect(JSON.stringify(style)).toContain("#C2410C")
  })
  it("shows all four neutral screen areas without fabricated results", async () => {
    await renderDemo(<HowItWorksScreen />)
    expect(screen.getAllByText("aguardando execução")).toHaveLength(11)
    for (const [index, [, title, , technicalDetails]] of stages.entries()) {
      const stage = screen.getByRole("button", { name: title })
      expect(stage.props.accessibilityState).toEqual({ expanded: false })
      await fireEvent.press(stage)
      expect(screen.getByText(technicalDetails)).toBeTruthy()
      expect(screen.getByRole("button", { name: title }).props.accessibilityState).toEqual({ expanded: true })
      if (index < stages.length - 1) await fireEvent.press(stage)
    }
    await renderDemo(<LaboratoryScreen />); expect(screen.getAllByText("Disponível no M4")).toHaveLength(8)
    expect(screen.getAllByRole("button")).toHaveLength(8)
    for (const control of screen.getAllByRole("button")) expect(control.props.accessibilityState).toEqual({ disabled: true })
    await renderDemo(<RoadmapScreen />); expect(roadmap.length).toBeGreaterThan(0)
    expect(screen.getByText("O que ainda falta")).toBeTruthy()
    expect(screen.getAllByText("Implementado").length).toBeGreaterThan(0)
    expect(screen.getByText("Planejado")).toBeTruthy()
    expect(screen.queryByText("implemented")).toBeNull()
  })
  it("keeps catalog statuses and evidence references closed", () => {
    for (const item of roadmap) { expect(["implemented", "partial", "planned", "research"]).toContain(item.status); expect(item.evidence.length).toBeGreaterThan(0); expect(item.snapshotVersion).toMatch(/^M[12]$/) }
    expect(JSON.stringify(roadmap)).not.toMatch(/CHATSCM|\.env|[A-Za-z]:\\|\/Users\//)
  })

  it("renders live success with structural grounding and nullable scores", async () => {
    const onViewPipeline = jest.fn()
    await renderDemo(<DemoChatScreen value="TEST DATA" onChange={jest.fn()} onExamplePress={jest.fn()} state={liveState} onSubmit={jest.fn()} onRetry={jest.fn()} onViewPipeline={onViewPipeline} />)
    expect(screen.getByText("Resposta TEST DATA segura.")).toBeTruthy()
    expect(screen.getByText("Citações verificadas")).toBeTruthy()
    expect(screen.getByText("Trecho TEST DATA")).toBeTruthy()
    expect(screen.getByText("Página 2")).toBeTruthy()
    expect(screen.getByText("Sparse: Não disponível")).toBeTruthy()
    await fireEvent.press(screen.getByRole("button", { name: "Ver como essa resposta foi construída" }))
    expect(onViewPipeline).toHaveBeenCalledTimes(1)
  })

  it("keeps examples as fill-only actions and shows honest loading", async () => {
    const onSubmit = jest.fn()
    const loading = { ...liveState, question: null, response: null, status: "loading" as const }
    await renderDemo(<DemoChatScreen value="TEST DATA" onChange={jest.fn()} onExamplePress={jest.fn()} state={loading} onSubmit={onSubmit} onRetry={jest.fn()} />)
    expect(screen.getByText("Executando o RagTest...")).toBeTruthy()
    expect(screen.queryByText("Resposta TEST DATA segura.")).toBeNull()
    expect(screen.getByRole("button", { name: "Enviar pergunta" }).props.accessibilityState).toEqual({ disabled: true })
  })
})
