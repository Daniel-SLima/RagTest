export function isDemoEnabled(value?: string): boolean {
  const candidate = value ?? process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED ?? ""
  return candidate.trim().toLowerCase() === "true"
}
