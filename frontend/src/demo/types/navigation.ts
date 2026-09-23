export type DemoTabId = "chat" | "how-it-works" | "laboratory" | "roadmap"

export const DEMO_TABS: ReadonlyArray<{ id: DemoTabId; label: string }> = [
  { id: "chat", label: "Chat" },
  { id: "how-it-works", label: "Como funciona" },
  { id: "laboratory", label: "Laboratório" },
  { id: "roadmap", label: "O que ainda falta" },
]
