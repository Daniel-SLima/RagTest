import type { DemoApiError, DemoRuntime, DemoRunResponse } from "./api"

export type DemoRunStatus = "idle" | "loading" | "success" | "error"
export type DemoRuntimeStatus = "idle" | "loading" | "success" | "error"

export type DemoRunDiagnostics = Pick<DemoRunResponse, "answer" | "model" | "grounded" | "citation_ids" | "sources" | "timings"> & {
  runtime: DemoRuntime | null
}

export type DemoRunState = {
  question: string | null
  response: DemoRunResponse | null
  diagnostics: DemoRunDiagnostics | null
  runtime: DemoRuntime | null
  runtimeStatus: DemoRuntimeStatus
  runtimeError: DemoApiError | null
  status: DemoRunStatus
  error: DemoApiError | null
}

export type DemoRunAction =
  | { type: "runtime-loading" }
  | { type: "runtime-success"; runtime: DemoRuntime }
  | { type: "runtime-error"; error: DemoApiError }
  | { type: "run-loading"; question: string }
  | { type: "run-success"; response: DemoRunResponse }
  | { type: "run-error"; error: DemoApiError }
