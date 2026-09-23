# RagTest Demo M4 — Laboratório Experimental de Retrieval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the opt-in Expo Laboratório tab into an explicit, retrieval-only comparison surface for Dense, Dense + rerank, and Hybrid using the existing `POST /v1/demo/retrieval` contract.

**Architecture:** Keep all laboratory controls and run state local to `LaboratoryScreen`; pass the already-created `DemoApi` instance from `DemoApp` without mutating runtime settings or Chat state. Use pure model helpers for strategy metadata, result normalization, source-overlap/rank-delta metrics, and historical benchmark data. A single run sends one retrieval request; comparison sends exactly three sequential requests and retains partial failures for explicit retry.

**Tech Stack:** Expo/React Native 0.86, React 19, TypeScript 5.9, Jest/RNTL, existing typed `DemoApi.retrieve`, existing closed demo DTOs and theme tokens.

**Spec:** User-provided M4 specification attached as `pasted-text.txt` (M3 fully validated for LOCAL/CONTROLADO and M4 implementation authorized).

## Global Constraints

- Work only on `sidequest/ragtest-demo`; do not push, merge, alter `main`, or modify agent configuration.
- Do not add `/v1/demo/run`, replay, LLM calls, provider calls, corpus/embedding/Qdrant changes, or persistent cache.
- Use only the three backend-supported modes: `dense`, `dense-rerank`, and `hybrid`; send `limit` (not `top_k`) in the closed range 1–10.
- Execute only on the explicit button; selecting examples fills the input and never runs a request.
- Comparison mode performs exactly three retrieval requests, one per supported strategy; sequence requests unless a later review proves safe parallelism without losing partial-error semantics.
- Never mutate `Settings.retrieval_mode`, global profiles, Chat state, or `DemoRunState` from the Lab.
- Treat nullable scores/timings as `Não disponível`; never coerce null to zero or invent pre/post-rerank or multi-query diagnostics.
- Multi-query/decomposition is displayed as unavailable/future because `/v1/demo/retrieval` exposes no decomposition contract; no fake fields or hidden LLM call.
- Current-run scores are not directly comparable and must not produce a numeric winner or universal superiority claim.
- Historical DEV/HOLDOUT metrics are versioned, labeled as benchmark evidence, and separated from current-run observations.
- Preserve the backend source allowlist; never expose CHATSCM/private sources or raw provider/path/error content.
- Runtime validation remains local/controlled and uses a public health question; no external/prod authorization is implied.

## Review Focus

- A compare run must issue exactly three retrieval calls and retain a failed strategy for explicit retry — test call count and partial state.
- Changing strategy, mode, or Top K must not issue a request or overwrite Chat state — test controls before explicit execution.
- A source with null page or nullable scores must render `Não disponível` without numeric fallback — test parser/rendering.
- Backend errors and malformed/sensitive DTOs must remain sanitized through the existing API boundary — test error card and no raw detail.
- Scores, benchmark values, overlap, and rank deltas must be labeled descriptively without a current-run winner — test warning and metric labels.

---

### Task 1: Laboratory domain model and historical evidence data

**Files:**
- Create: `frontend/src/demo/laboratory/laboratory-model.ts`
- Create: `frontend/src/demo/data/laboratory-benchmarks.ts`
- Test: `frontend/src/demo/laboratory/laboratory-model.test.ts`

**Interfaces:**
- Consumes: `DemoRetrievalMode`, `DemoRetrievalResponse`, and `DemoSource` from `frontend/src/demo/types/api.ts`.
- Produces: `LAB_STRATEGIES`, `LabStrategy`, `LabExecution`, `LabExecutionStatus`, `sourceKey`, `deriveComparisonMetrics`, and immutable benchmark/rationale data used by the screen.

- [x] **Step 1: Write failing model tests**

  Cover stable strategy order/labels, source identity by public id/document/page, counts of unique documents, all-three and exclusive sources, pair overlap, and rank deltas. Assert that null page/scores remain null. Add a benchmark fixture assertion for dataset `2026-09-20-v1` with distinct DEV and HOLDOUT rows and metric names `HitRate`, `MRR`, `SourceRecall`, and `SourceNDCG`.

- [x] **Step 2: Run model tests to verify RED**

  Run `npm test -- --runInBand frontend/src/demo/laboratory/laboratory-model.test.ts`; expect module/function-not-found failures.

- [x] **Step 3: Implement pure model helpers**

  Define the exact mode tuple `[{id:"dense", label:"Dense"}, {id:"dense-rerank", label:"Dense + rerank"}, {id:"hybrid", label:"Hybrid"}]`. Derive metrics only from returned ordered sources: result count, unique documents, pair/all-three overlap, exclusive keys, and rank delta for shared keys. Keep benchmark constants descriptive and source-labeled; include D006/D007 rationale text and a no-universal-superiority disclaimer.

- [x] **Step 4: Run model tests to verify GREEN**

  Run the same Jest command; all model tests must pass.

- [x] **Step 5: Commit**

  `git add frontend/src/demo/laboratory frontend/src/demo/data/laboratory-benchmarks.ts frontend/src/demo/laboratory/laboratory-model.test.ts && git commit -m "feat: add laboratory retrieval comparison model"`

### Task 2: Retrieval-only laboratory state and responsive screen

**Files:**
- Create: `frontend/src/demo/screens/laboratory-screen.tsx` (replace the M2 placeholder)
- Modify: `frontend/App.tsx` (pass the existing API/config error to the Lab)
- Test: `frontend/src/demo/screens/laboratory-screen.test.tsx`

**Interfaces:**
- Consumes: `DemoApi`, `DemoApiError`, `DemoSource`, model helpers from Task 1, `useDemoTheme`, and existing `demoExamples`.
- Produces: `LaboratoryScreen({ api, apiError })`; one explicit retrieval request in single mode; exactly one request per strategy in compare mode; accessible controls/cards suitable for desktop and mobile.

- [x] **Step 1: Write failing screen tests**

  Use a mocked `DemoApi.retrieve` returning deterministic public-shaped responses. Assert initial empty state, example press only calls the parent fill callback/no API call, mode/strategy/Top K controls do not call the API, single execution sends `{query, limit, retrieval_mode}` once, compare sends the three modes exactly once, results show rank/document/page/nullable scores, timing and score-comparability warning, multi-query unavailable copy, historical benchmark separation, and no winner label. Add a rejected second strategy test asserting the first/third cards remain visible and only the failed card’s retry makes one additional call.

- [x] **Step 2: Run screen tests to verify RED**

  Run `npm test -- --runInBand frontend/src/demo/screens/laboratory-screen.test.tsx`; expect failures because the placeholder has no controls or live retrieval.

- [x] **Step 3: Implement isolated state and explicit execution**

  Add local state for `query`, `selectedStrategy`, `compareAll`, `limit` (default 5), and a map of `LabExecution` objects. On execute, validate with `validateDemoRequest`; single mode clears only the selected Lab slot and calls `api.retrieve` once. Compare mode clears the three Lab slots then iterates `LAB_STRATEGIES` sequentially, storing each success or sanitized error. Retry calls only the failed strategy. Do not call `getRuntime`, `run`, or any request from control changes or tab navigation.

- [x] **Step 4: Implement rendering and accessibility**

  Render question input, public examples as fill-only controls, strategy segmented controls, single/compare mode, Top K options `[3,5,10]` (within backend 1–10), explicit execute/retry buttons, loading/partial/error states, source rows with array rank, document/page/excerpt/scores, per-retrieval timings, and local-machine variability warning. Render compare metrics and rank changes descriptively; show score comparability warning in every result comparison and no winner. Render the unavailable multi-query panel, the historical DEV/HOLDOUT benchmark card with dataset/source labels, and the D006/D007 rationale panel. Use `useWindowDimensions`/flex wrap so columns stack below 640 px; avoid fixed-width overflow and preserve the existing theme tokens.

- [x] **Step 5: Wire App without shared-state mutation**

  Change `DemoApp` only to render `<LaboratoryScreen api={api} apiError={configError} />`; keep Chat reducer, runtime loading, and `api.run` behavior unchanged. When `api` is null, show the sanitized configuration error and no request.

- [x] **Step 6: Run screen tests to verify GREEN**

  Run `npm test -- --runInBand frontend/src/demo/screens/laboratory-screen.test.tsx`; all new tests must pass.

- [x] **Step 7: Commit**

  `git add frontend/App.tsx frontend/src/demo/screens/laboratory-screen.tsx frontend/src/demo/screens/laboratory-screen.test.tsx && git commit -m "feat: implement retrieval laboratory screen"`

### Task 3: Regression gates, documentation, and controlled validation

**Files:**
- Modify: `docs/demo-m1.md` (M4 public demo contract/status and limitations)
- Modify: `docs/CONTEXTO_CONTINUIDADE.md` (M4 implementation/evidence handoff)
- Modify: `docs/decisoes-tecnicas.md` only if the implementation creates a new architectural decision beyond D006/D007; otherwise record no new decision.

**Interfaces:**
- Consumes: Tasks 1–2 implementation and automated evidence.
- Produces: documented distinction between implemented, awaiting validation, verified, and blocked; no M5/replay work.

- [x] **Step 1: Run the complete automated gates**

  Run `npm test -- --runInBand`, `npm run typecheck`, `.venv\\Scripts\\ruff.exe check app tests`, and `git diff --check`; expect all existing and new frontend tests, TypeScript, Ruff, and whitespace checks to pass. Backend tests are required only if backend files changed; this plan changes no backend file.

- [x] **Step 2: Run controlled runtime checks**

  With `DEMO_ENABLED=true`, the existing public allowlist, local Qdrant, and no `.env` edits, call only `POST /v1/demo/retrieval` through the Expo Lab using a public question. Verify one request for each single mode and exactly three for compare, no `/v1/demo/run`, public source paths only, no provider/LLM activity, timings present or honestly unavailable, and Qdrant remains at 767 points. Do not run ingestion, recreate collections, or `docker compose down -v`.

- [x] **Step 3: Validate responsive surfaces**

  Inspect `1366x768`, `1024x600`, `390x844`, and `360x800`; verify mobile stacking, no horizontal overflow, readable warnings/benchmark labels, and explicit retry/partial errors. Record direct Network/Console or viewport limitations honestly if the available browser surface cannot expose them.

- [x] **Step 4: Update continuity documentation**

  Record changed files, exact commit(s), automated outputs, controlled runtime evidence, strategy/Top K contract, unavailable multi-query status, historical benchmark source, privacy/security limitations, and the next M5 proposal. Do not state external/production readiness.

- [x] **Step 5: Final diff/status verification**

  Run `git status --short --branch`, `git log -1 --oneline`, `git diff --stat`, and `git diff --check`; preserve unrelated local artifacts and do not push/merge.

- [x] **Step 6: Commit documentation**

  `git add docs/demo-m1.md docs/CONTEXTO_CONTINUIDADE.md docs/decisoes-tecnicas.md && git commit -m "docs: record M4 retrieval laboratory validation"`

## Self-review coverage

- The plan intentionally makes no backend change: the existing closed retrieval DTO already supports all three strategies, per-request mode, limit 1–10, nullable scores, and retrieval timings; multi-query is unavailable in that contract and remains explicitly unavailable in the UI.
- Every current-run request is explicit and observable, while historical metrics are static, versioned, and separated from current runs.
- The five review-focus failures are pinned to Task 1 or Task 2 tests; Task 3 adds runtime and responsive evidence without changing production behavior.
- M5/replay, external deployment, auth/rate limiting, raw provider logs, corpus, embeddings, collection, and agent configuration remain outside this plan.
