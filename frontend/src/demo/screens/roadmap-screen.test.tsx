import { fireEvent, render, screen } from "@testing-library/react-native"

import { DemoThemeProvider } from "../components/demo-shell-theme"
import { ROADMAP_AREAS, ROADMAP_ITEMS, ROADMAP_SNAPSHOT, getRoadmapCounts } from "../data/roadmap"
import { RoadmapScreen } from "./roadmap-screen"

const renderRoadmap = async () => render(<DemoThemeProvider><RoadmapScreen /></DemoThemeProvider>)

describe("RoadmapScreen", () => {
  it("renders the project overview, snapshot and separated architecture views", async () => {
    await renderRoadmap()

    expect(screen.getByText("VISÃO GERAL")).toBeTruthy()
    expect(screen.getByText("Fotografia do projeto")).toBeTruthy()
    expect(screen.getByText("RagTest")).toBeTruthy()
    expect(screen.getByText(`Branch: ${ROADMAP_SNAPSHOT.branch}`)).toBeTruthy()
    expect(screen.getByText(`Commit-base: ${ROADMAP_SNAPSHOT.commit}`)).toBeTruthy()
    expect(screen.getByText(`Versão do snapshot: ${ROADMAP_SNAPSHOT.version}`)).toBeTruthy()
    expect(screen.getByText(`Data: ${ROADMAP_SNAPSHOT.date}`)).toBeTruthy()
    expect(screen.getByText("Arquitetura atual")).toBeTruthy()
    expect(screen.getByText(/Demo\/Expo → FastAPI → RAG/)).toBeTruthy()
    expect(screen.getByText("Visão planejada")).toBeTruthy()
    expect(screen.getAllByText(/Se Cuida Mulher/).length).toBeGreaterThan(0)
  })

  it("derives one area card and counts from the catalog", async () => {
    await renderRoadmap()
    const counts = getRoadmapCounts(ROADMAP_ITEMS)

    for (const area of ROADMAP_AREAS) {
      expect(screen.getAllByText(area).length).toBeGreaterThan(0)
      expect(screen.getAllByText(`${counts.byArea[area]} ${counts.byArea[area] === 1 ? "item" : "itens"}`).length).toBeGreaterThan(0)
    }

    expect(screen.getByText(`${counts.byStatus.implemented} implementados`)).toBeTruthy()
    expect(screen.getByText(`${counts.byStatus.partial} parciais`)).toBeTruthy()
    expect(screen.getByText(`${counts.byStatus.planned} planejados`)).toBeTruthy()
    expect(screen.getByText(`${counts.byStatus.research} em estudo`)).toBeTruthy()
    expect(screen.queryByText(/%/)).toBeNull()
  })

  it.each([
    ["Implementado", "implemented", "Núcleo RAG e API"],
    ["Parcial / em desenvolvimento", "partial", "Sessões e contexto"],
    ["Planejado", "planned", "Integração Se Cuida Mulher"],
    ["Em estudo", "research", "Privacidade e LGPD"],
  ] as const)("filters by status %s without requests", async (label, status, expectedArea) => {
    await renderRoadmap()
    await fireEvent.press(screen.getByRole("button", { name: `Status: ${label}` }))

    expect(screen.getAllByText(expectedArea).length).toBeGreaterThan(0)
    expect(screen.getAllByText(label).length).toBeGreaterThan(0)
    expect(screen.queryByText(/não há itens para este filtro/i)).toBeNull()

    if (status === "implemented") {
      expect(screen.queryByText("Sessões conversacionais no backend")).toBeNull()
    }
  })

  it("filters by area, supports Todos and reports an empty result", async () => {
    await renderRoadmap()
    await fireEvent.press(screen.getByRole("button", { name: "Área: Sessões e contexto" }))
    expect(screen.getByText("Sessões conversacionais no backend")).toBeTruthy()
    expect(screen.queryByText("Núcleo RAG e API REST")).toBeNull()

    await fireEvent.press(screen.getByRole("button", { name: "Todos" }))
    expect(screen.getByText("Núcleo RAG e API REST")).toBeTruthy()

    await fireEvent.press(screen.getByRole("button", { name: "Status: Em estudo" }))
    await fireEvent.press(screen.getByRole("button", { name: "Área: Núcleo RAG e API" }))
    expect(screen.getByText("Não há itens para este filtro.")).toBeTruthy()
  })

  it("opens an accessible item accordion with conditional details and evidence", async () => {
    await renderRoadmap()
    const item = screen.getByRole("button", { name: "Laboratório de comparação de retrieval" })
    expect(item.props.accessibilityState).toEqual({ expanded: false })
    expect(screen.queryByText(/Por que ainda falta\?/)).toBeNull()

    await fireEvent.press(item)
    expect(item.props.accessibilityState).toEqual({ expanded: true })
    expect(screen.getByText(/A demo compara estratégias de retrieval/)).toBeTruthy()
    expect(screen.getByText(/O Laboratório usa Dense/)).toBeTruthy()
    expect(screen.getByText(/Por que ainda falta\?/)).toBeTruthy()
    expect(screen.getAllByText(/A validação é somente local/).length).toBeGreaterThan(0)
    expect(screen.getByText(/Depende de: Retrieval e avaliação/)).toBeTruthy()
    expect(screen.getByText(/Origem: docs\/CONTEXTO_CONTINUIDADE\.md/)).toBeTruthy()
    expect(screen.getAllByText(/docs\/demo-m1\.md/).length).toBeGreaterThan(0)

    await fireEvent.press(item)
    expect(item.props.accessibilityState).toEqual({ expanded: false })
    expect(screen.queryByText(/O Laboratório usa Dense/)).toBeNull()
  })

  it("keeps the rendered catalog free of personal paths, secrets and replay claims", async () => {
    await renderRoadmap()
    const rendered = JSON.stringify(screen.toJSON())
    expect(rendered).not.toMatch(/[A-Za-z]:\\|\/Users\/|\.env|CHATSCM|replay/i)
  })
})
