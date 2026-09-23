import { createContext, useContext } from "react"
import { useColorScheme } from "react-native"
import { getDemoTheme, type DemoTheme } from "./demo-tokens"

const DemoThemeContext = createContext<DemoTheme>(getDemoTheme("light"))

export function DemoThemeProvider({ children }: { children: React.ReactNode }) {
  const scheme = useColorScheme()
  return <DemoThemeContext.Provider value={getDemoTheme(scheme)}>{children}</DemoThemeContext.Provider>
}

export function useDemoTheme() {
  return useContext(DemoThemeContext)
}
