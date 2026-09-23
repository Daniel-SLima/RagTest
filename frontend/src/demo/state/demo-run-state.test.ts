import { demoRunReducer, initialDemoRunState } from "./demo-run-state"

const runtime = { version: "M1", provider: "TEST DATA", model: "TEST DATA", embedding: "TEST DATA", retrieval: "dense" as const, collection: "public", demo_enabled: true, policy_id: "local", policy_status: "configured" as const }
const response = { answer: "TEST DATA", model: "TEST DATA", grounded: true, citation_ids: [1], sources: [], timings: { retrieval_ms: 1, generation_ms: null, total_ms: 1 } }
const apiError = { code: "demo_api_error", status: null, message: "Mensagem pública" }

describe("demoRunReducer", () => {
  it("keeps idle state empty", () => expect(initialDemoRunState).toMatchObject({ question: null, response: null, runtime: null, status: "idle" }))
  it("projects a successful run and runtime", () => {
    const withRuntime = demoRunReducer(initialDemoRunState, { type: "runtime-success", runtime })
    const loading = demoRunReducer(withRuntime, { type: "run-loading", question: "TEST DATA" })
    const success = demoRunReducer(loading, { type: "run-success", response })
    expect(success).toMatchObject({ question: "TEST DATA", response, runtime, status: "success" })
    expect(success.diagnostics).toMatchObject({ answer: "TEST DATA", runtime })
    expect(success.diagnostics?.timings.generation_ms).toBeNull()
  })
  it("preserves the completed run when runtime later fails", () => {
    const success = demoRunReducer(demoRunReducer(initialDemoRunState, { type: "run-loading", question: "TEST DATA" }), { type: "run-success", response })
    const failed = demoRunReducer(success, { type: "runtime-error", error: apiError })
    expect(failed.response).toBe(response)
    expect(failed.diagnostics).toBeTruthy()
    expect(failed.runtimeStatus).toBe("error")
    expect(failed.runtimeError).toMatchObject({ code: apiError.code, status: apiError.status })
    expect(failed.runtimeError?.message).not.toBe(apiError.message)
  })
  it("does not accept raw response or errors in state", () => {
    const errorState = demoRunReducer(initialDemoRunState, { type: "run-error", error: { ...apiError, message: "secret/path/traceback" } })
    expect(errorState.error).toMatchObject({ code: apiError.code, status: apiError.status })
    expect(errorState.error?.message).not.toMatch(/secret|path|traceback/i)
    expect(JSON.stringify(errorState)).not.toContain("traceback")
  })
})
