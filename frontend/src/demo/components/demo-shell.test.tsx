import { fireEvent, render, screen } from "@testing-library/react-native"
import { DemoShell } from "./demo-shell"

describe("demo shell", () => {
  it("renders the exact accessible tab set and changes tabs", async () => {
    const onTabChange = jest.fn()
    await render(<DemoShell activeTab="chat" onTabChange={onTabChange}><></></DemoShell>)
    expect(screen.getByTestId("demo-tablist")).toHaveProp("accessibilityRole", "tablist")
    expect(screen.getAllByRole("tab")).toHaveLength(4)
    expect(screen.getByRole("tab", { name: "Chat" })).toHaveProp("accessibilityState", { selected: true })
    await fireEvent.press(screen.getByRole("tab", { name: "Laboratório" }))
    expect(onTabChange).toHaveBeenCalledWith("laboratory")
    expect(screen.getByText(/Modo local/)).toBeTruthy()
  })
})
