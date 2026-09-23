import type { DemoApiError, DemoRuntime, DemoRunResponse } from "../types/api"
import type { DemoRunAction, DemoRunDiagnostics, DemoRunState } from "../types/run-state"
import { sanitizeDemoApiError } from "../api/demo-api"

export const initialDemoRunState: DemoRunState = {
  question: null, response: null, diagnostics: null, runtime: null,
  runtimeStatus: "idle", runtimeError: null, status: "idle", error: null,
}

export function toDemoDiagnostics(response: DemoRunResponse | null, runtime: DemoRuntime | null): DemoRunDiagnostics | null {
  if (!response) return null
  return { answer: response.answer, model: response.model, grounded: response.grounded, citation_ids: response.citation_ids, sources: response.sources, timings: response.timings, runtime }
}

function projection(state: DemoRunState, response = state.response, runtime = state.runtime): DemoRunState {
  return { ...state, response, runtime, diagnostics: toDemoDiagnostics(response, runtime) }
}

export function demoRunReducer(state: DemoRunState, action: DemoRunAction): DemoRunState {
  switch (action.type) {
    case "runtime-loading": return { ...state, runtimeStatus: "loading", runtimeError: null }
    case "runtime-success": return projection({ ...state, runtimeStatus: "success", runtimeError: null }, state.response, action.runtime)
    case "runtime-error": return { ...state, runtimeStatus: "error", runtimeError: sanitizeDemoError(action.error) }
    case "run-loading": return { ...state, question: action.question, response: null, diagnostics: null, status: "loading", error: null }
    case "run-invalid": return { ...state, question: action.question, response: null, diagnostics: null, status: "error", error: sanitizeDemoError(action.error) }
    case "run-success": return projection({ ...state, response: action.response, status: "success", error: null }, action.response, state.runtime)
    case "run-error": return { ...state, status: "error", error: sanitizeDemoError(action.error) }
    default: return state
  }
}

export function sanitizeDemoError(error: unknown): DemoApiError {
  return sanitizeDemoApiError(error)
}
