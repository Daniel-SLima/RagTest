import { fireEvent, render, screen, waitFor } from "@testing-library/react-native"
import { DemoThemeProvider } from "../components/demo-shell-theme"
import { demoExamples } from "./demo-chat-screen"
import { LaboratoryScreen } from "./laboratory-screen"
import type { DemoApi } from "../api/demo-api"
import type { DemoRetrievalMode, DemoRetrievalResponse } from "../types/api"

const source = (mode: DemoRetrievalMode, order: number, page: number | null = order) => ({
  public_id: `${mode}-${order}`,
  document: `public/${mode}.pdf`,
  page,
  order,
  excerpt: `Trecho ${mode} ${order}`,
  scores: { dense_score: mode === "dense" ? 0.9 : null, sparse_score: mode === "hybrid" ? 0.7 : null, rank_score: null, fusion_score: null },
})

function result(mode: DemoRetrievalMode, query = "pergunta pública"): DemoRetrievalResponse {
  return { query, retrieval_mode: mode, sources: [source(mode, 1), source(mode, 2, null)], timings: { retrieval_ms: 8, generation_ms: null, total_ms: 9 } }
}

function renderLab(api: DemoApi, props: Partial<React.ComponentProps<typeof LaboratoryScreen>> = {}) {
  return render(<DemoThemeProvider><LaboratoryScreen api={api} {...props} /></DemoThemeProvider>)
}

describe("LaboratoryScreen", () => {
  it("starts empty and selecting an example only fills the question", async () => {
    const retrieve = jest.fn()
    const api = { retrieve } as unknown as DemoApi
    await renderLab(api)
    expect(screen.getByText("Laboratório")).toBeTruthy()
    await fireEvent.press(screen.getByRole("button", { name: `Usar exemplo: ${demoExamples[0].query}` }))
    expect(screen.getByDisplayValue(demoExamples[0].query)).toBeTruthy()
    expect(retrieve).not.toHaveBeenCalled()
  })

  it("does not execute when strategy, mode, or Top K controls change", async () => {
    const retrieve = jest.fn()
    await renderLab({ retrieve } as unknown as DemoApi)
    await fireEvent.press(screen.getByRole("button", { name: "Hybrid" }))
    await fireEvent.press(screen.getByRole("button", { name: "Comparar todas" }))
    await fireEvent.press(screen.getByRole("button", { name: "Top K 10" }))
    expect(retrieve).not.toHaveBeenCalled()
  })

  it("sends one retrieval request for a single strategy", async () => {
    const retrieve = jest.fn().mockResolvedValue(result("dense", "pergunta pública"))
    await renderLab({ retrieve } as unknown as DemoApi)
    await fireEvent.changeText(screen.getByLabelText("Pergunta do laboratório"), "pergunta pública")
    await fireEvent.press(screen.getByRole("button", { name: "Executar retrieval" }))
    await waitFor(() => expect(retrieve).toHaveBeenCalledTimes(1))
    expect(retrieve).toHaveBeenCalledWith({ query: "pergunta pública", limit: 5, retrieval_mode: "dense" })
    expect(screen.getByText("#1")).toBeTruthy()
    expect(screen.getByText("Página: 1")).toBeTruthy()
    expect(screen.getByText("Página: Não disponível")).toBeTruthy()
    expect(screen.getAllByText("Sparse: Não disponível").length).toBeGreaterThan(0)
    expect(screen.getByText(/Retrieval: 8 ms/)).toBeTruthy()
  })

  it("executes exactly the three supported modes in compare mode", async () => {
    const retrieve = jest.fn().mockImplementation(async (request: { retrieval_mode: DemoRetrievalMode; query: string }) => result(request.retrieval_mode, request.query))
    await renderLab({ retrieve } as unknown as DemoApi)
    await fireEvent.changeText(screen.getByLabelText("Pergunta do laboratório"), "pergunta pública")
    await fireEvent.press(screen.getByRole("button", { name: "Comparar todas" }))
    await fireEvent.press(screen.getByRole("button", { name: "Executar comparação" }))
    await waitFor(() => expect(retrieve).toHaveBeenCalledTimes(3))
    expect(retrieve.mock.calls.map(([request]) => request.retrieval_mode)).toEqual(["dense", "dense-rerank", "hybrid"])
    expect(screen.getByText("Scores não são diretamente comparáveis entre estratégias.")).toBeTruthy()
    expect(screen.getByText("Multi-query / decomposição")).toBeTruthy()
    expect(screen.getByText(/indisponível nesta versão/i)).toBeTruthy()
    expect(screen.getByText("DEV · 2026-09-20-v1")).toBeTruthy()
    expect(screen.getByText("HOLDOUT · 2026-09-20-v1")).toBeTruthy()
    expect(screen.queryByText(/vencedor/i)).toBeNull()
  })

  it("keeps successful cards when one comparison request fails and retries only that card", async () => {
    let calls = 0
    const retrieve = jest.fn().mockImplementation(async (request: { retrieval_mode: DemoRetrievalMode; query: string }) => {
      calls += 1
      if (request.retrieval_mode === "dense-rerank" && calls <= 3) throw { code: "retrieval_failed", status: 503, message: "internal provider detail" }
      return result(request.retrieval_mode, request.query)
    })
    await renderLab({ retrieve } as unknown as DemoApi)
    await fireEvent.changeText(screen.getByLabelText("Pergunta do laboratório"), "pergunta pública")
    await fireEvent.press(screen.getByRole("button", { name: "Comparar todas" }))
    await fireEvent.press(screen.getByRole("button", { name: "Executar comparação" }))
    await waitFor(() => expect(retrieve).toHaveBeenCalledTimes(3))
    expect(screen.getAllByText("Dense").length).toBeGreaterThan(0)
    expect(screen.getAllByText("Hybrid").length).toBeGreaterThan(0)
    expect(screen.getByText("Não foi possível concluir a busca documental.")).toBeTruthy()
    await fireEvent.changeText(screen.getByLabelText("Pergunta do laboratório"), "outra pergunta")
    await fireEvent.press(screen.getByRole("button", { name: "Top K 10" }))
    await fireEvent.press(screen.getByRole("button", { name: "Tentar Dense + rerank novamente" }))
    await waitFor(() => expect(retrieve).toHaveBeenCalledTimes(4))
    expect(retrieve.mock.calls[3][0]).toMatchObject({ retrieval_mode: "dense-rerank", query: "pergunta pública", limit: 5 })
    expect(screen.getAllByText("Dense").length).toBeGreaterThan(0)
    expect(screen.getAllByText("Hybrid").length).toBeGreaterThan(0)
  })

  it("rejects a response whose query, mode, or source order does not match the request", async () => {
    const retrieve = jest.fn().mockResolvedValue({ ...result("dense", "outra pergunta"), retrieval_mode: "hybrid" })
    await renderLab({ retrieve } as unknown as DemoApi)
    await fireEvent.changeText(screen.getByLabelText("Pergunta do laboratório"), "pergunta pública")
    await fireEvent.press(screen.getByRole("button", { name: "Executar retrieval" }))
    await waitFor(() => expect(screen.getByText("Resposta do serviço de demonstração inválida.")).toBeTruthy())
    expect(screen.queryByText("outra pergunta")).toBeNull()
  })
})
