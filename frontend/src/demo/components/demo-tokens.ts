import type { ColorSchemeName } from "react-native"

export const demoTokens = {
  light: {
    background: "#F4F6F8",
    surface: "#FFFFFF",
    surfaceMuted: "#E9EEF2",
    text: "#17212B",
    textMuted: "#43515D",
    border: "#AAB7C2",
    action: "#0B4F71",
    actionText: "#FFFFFF",
    focusOutline: "#C2410C",
    success: "#166534",
    warning: "#854D0E",
    disabled: "#4B5563",
  },
  dark: {
    background: "#111820",
    surface: "#1C2730",
    surfaceMuted: "#293640",
    text: "#F3F7FA",
    textMuted: "#C5D1D9",
    border: "#8EA2B0",
    action: "#8DD5FF",
    actionText: "#07263A",
    focusOutline: "#FDBA74",
    success: "#86EFAC",
    warning: "#FDE68A",
    disabled: "#9AAAB5",
  },
} as const

export type DemoTheme = {
  [Key in keyof (typeof demoTokens)["light"]]: string
}

export function getDemoTheme(scheme: ColorSchemeName): DemoTheme {
  return scheme === "dark" ? demoTokens.dark : demoTokens.light
}

export function getDemoFocusOutline(theme: DemoTheme, focused: boolean) {
  return focused ? { borderColor: theme.focusOutline, borderWidth: 3 } : null
}

export function getDemoLayout(
  viewportWidth: number,
  viewportHeight: number,
  platform: "web" | "native",
) {
  const isCompact = viewportWidth < 640
  const gutter = isCompact ? 16 : 24
  const containerWidth = Math.max(0, Math.min(1120, viewportWidth - gutter * 2))
  return {
    containerWidth,
    gutter,
    isCompact,
    tabsWrap: isCompact,
    cardsDirection: isCompact ? ("column" as const) : ("row" as const),
    hasHorizontalOverflow: false as const,
    isLandscapeWeb: platform === "web" && viewportWidth > viewportHeight,
  }
}
