import { demoTokens, getDemoLayout, getDemoTheme } from "./demo-tokens"

function contrastRatio(foreground: string, background: string) {
  const luminance = (value: string) => {
    const hex = Number.parseInt(value.slice(1), 16)
    return [hex >> 16, (hex >> 8) & 255, hex & 255]
      .map((channel) => channel / 255)
      .map((channel) => (channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4))
      .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0)
  }
  const light = luminance(foreground)
  const dark = luminance(background)
  return (Math.max(light, dark) + 0.05) / (Math.min(light, dark) + 0.05)
}

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

  it("keeps disabled status text at normal-text contrast in both themes", () => {
    expect(contrastRatio(demoTokens.light.disabled, demoTokens.light.surface)).toBeGreaterThanOrEqual(4.5)
    expect(contrastRatio(demoTokens.light.disabled, demoTokens.light.surfaceMuted)).toBeGreaterThanOrEqual(4.5)
    expect(contrastRatio(demoTokens.dark.disabled, demoTokens.dark.surface)).toBeGreaterThanOrEqual(4.5)
  })
})
