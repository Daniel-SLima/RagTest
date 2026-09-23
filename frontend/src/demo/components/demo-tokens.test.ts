import { getDemoLayout, getDemoTheme } from "./demo-tokens"

describe("demo tokens and layout", () => {
  it.each([[1366, 768, 1120, 24], [1024, 600, 976, 24], [390, 844, 358, 16], [360, 800, 328, 16]])("keeps the shell inside the viewport", (width, height, containerWidth, gutter) => {
    const layout = getDemoLayout(width, height, "web")
    expect(layout.containerWidth).toBe(containerWidth)
    expect(layout.gutter).toBe(gutter)
    expect(layout.hasHorizontalOverflow).toBe(false)
    expect(layout.isCompact).toBe(width < 640)
  })
  it("has readable light and dark foregrounds", () => {
    expect(getDemoTheme("light").text).not.toBe(getDemoTheme("light").background)
    expect(getDemoTheme("dark").text).not.toBe(getDemoTheme("dark").background)
  })
})
