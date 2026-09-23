# RagTest Demo M2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Construir a fundação visual opt-in da Demo Técnica no Expo existente, com quatro abas, contratos tipados, catálogo versionado e cliente seguro para os endpoints M1, sem executar RAG real.

**Architecture:** O frontend normal atual permanece intacto quando `EXPO_PUBLIC_RAG_DEMO_ENABLED` não é explicitamente `true`. Quando habilitado, `App.tsx` monta um shell demo controlado por estado, sem biblioteca de navegação adicional. O namespace `frontend/src/demo/` contém configuração, tipos/API, componentes, telas e dados versionados; as telas M2 são shells sem resultados fictícios.

**Tech Stack:** Expo SDK 57, React Native 0.86, React 19, TypeScript strict, Jest/Jest Expo, React Native Testing Library; nenhum pacote novo de navegação.

**Spec:** Especificação aprovada do M2 enviada em 2026-09-23, complementada por `docs/demo-m1.md` e pelo contrato M1 no backend.

## Global Constraints

- A demo frontend é opt-in via `EXPO_PUBLIC_RAG_DEMO_ENABLED=true`; qualquer outro valor preserva o app normal.
- As quatro abas são Chat, Como funciona, Laboratório e O que ainda falta.
- M2 não executa Gemini, Groq, Ollama, Qdrant nem `/v1/demo/run`/`retrieval`; o cliente apenas define contratos e chamadas futuras seguras.
- Não inventar versão, commit, ranking, resposta, timing, fonte ou roadmap sem evidência.
- Nenhuma resposta bruta, segredo, path, `.env`, CHATSCM ou metadata arbitrária pode ser logada ou exibida.
- Touch targets devem ter pelo menos 44pt/48dp, labels acessíveis, foco visível na Web e layout sem overflow em 1366x768, 1024x600, 390x844 e 360x800.
- Não adicionar biblioteca pesada de navegação ou dependência sem autorização.

## Review Focus

- **Flag ausente ou diferente de `true`:** App deve renderizar exatamente o frontend normal atual; coberto por teste de gating.
- **Troca de abas em viewport estreita:** todas as abas devem continuar alcançáveis sem depender de largura fixa; coberto por teste de navegação e layout lógico.
- **Exemplo de pergunta:** pressionar só preenche o input e não chama `sendChat` nem provider; coberto por teste de Chat.
- **Dados incompletos/null da API demo:** tipos e normalização devem preservar null, não inventar valores; coberto por testes do cliente.
- **Fixtures e catálogo:** somente dados sintéticos marcados como teste e itens com fonte verificável; coberto por teste sem secrets/paths/CHATSCM.

### Task 1: Contratos frontend e ativação opt-in

**Files:**
- Create: `frontend/src/demo/config.ts`
- Create: `frontend/src/demo/types/api.ts`
- Create: `frontend/src/demo/api/demo-api.ts`
- Create: `frontend/src/demo/api/demo-api.test.ts`
- Modify: `frontend/.env.example`

**Interfaces:**
- `isDemoEnabled(value?: string): boolean` accepts only case-insensitive `true` after trimming.
- `DemoRuntime`, `DemoScore`, `DemoSource`, `DemoTimings`, `DemoRetrievalRequest`, `DemoRetrievalResponse`, `DemoRunRequest`, `DemoRunResponse`, `DemoApiError` mirror M1 schemas and nullable fields.
- `createDemoApi(baseUrl: string, fetcher?: DemoFetcher)` exposes `getRuntime()`, `run()`, and `retrieve()`; errors are typed and never log/return raw response bodies.

- [ ] Write failing Jest tests for strict opt-in, URL normalization, typed success payloads, nullable timings/scores, stable error messages, and absent secret/raw-body fields.
- [ ] Run `npm test -- --runTestsByPath src/demo/api/demo-api.test.ts` and observe RED.
- [ ] Implement the config, types, fetcher, and safe error parser with no console logging.
- [ ] Run the focused test and then `npm test`; observe GREEN.
- [ ] Commit `feat: add typed opt-in demo frontend client`.

### Task 2: Design tokens, shell navigation, and shared structural components

**Files:**
- Create: `frontend/src/demo/components/demo-shell.tsx`
- Create: `frontend/src/demo/components/demo-tabs.tsx`
- Create: `frontend/src/demo/components/demo-header.tsx`
- Create: `frontend/src/demo/components/demo-card.tsx`
- Create: `frontend/src/demo/components/demo-status-badge.tsx`
- Create: `frontend/src/demo/components/demo-tokens.ts`
- Create: `frontend/src/demo/types/navigation.ts`
- Create: `frontend/src/demo/components/demo-shell.test.tsx`

**Interfaces:**
- `DemoTabId = "chat" | "how-it-works" | "laboratory" | "roadmap"`.
- `DemoShell({ activeTab, onTabChange, children, runtimeState })` renders a labeled tablist, header, local/development notice, neutral runtime slot, and responsive content container.
- `DemoCard` and `DemoStatusBadge` accept visible text plus accessible labels; icons are decorative text companions, not the only labels.

- [ ] Write RED tests for four tab labels, selected state, accessible names, tab changes, neutral runtime copy, and disabled/pressed semantics.
- [ ] Run the focused tests and observe RED.
- [ ] Implement the shell with `useWindowDimensions`, semantic spacing tokens, high-contrast light surfaces, safe padding, and no new dependency.
- [ ] Run focused tests, full Jest, and typecheck.
- [ ] Commit `feat: add responsive demo shell and tab navigation`.

### Task 3: Four M2 screens and versioned roadmap catalog

**Files:**
- Create: `frontend/src/demo/screens/demo-chat-screen.tsx`
- Create: `frontend/src/demo/screens/how-it-works-screen.tsx`
- Create: `frontend/src/demo/screens/laboratory-screen.tsx`
- Create: `frontend/src/demo/screens/roadmap-screen.tsx`
- Create: `frontend/src/demo/components/pipeline-stage.tsx`
- Create: `frontend/src/demo/components/lab-mode-card.tsx`
- Create: `frontend/src/demo/components/roadmap-item.tsx`
- Create: `frontend/src/demo/data/roadmap.ts`
- Create: `frontend/src/demo/types/roadmap.ts`
- Create: `frontend/src/demo/screens/demo-screens.test.tsx`

**Interfaces:**
- `DemoChatScreen({ value, onChange, onExamplePress })` renders title, short narrative, labeled input, confirmed examples, empty conversation/source/grounding slots, and disabled future live-action copy; examples only call `onExamplePress`.
- `PipelineStage` accepts `{ id, title, simpleExplanation, technicalDetails, state: "awaiting-execution", expanded, onToggle }`.
- `RoadmapItem` fields: `id`, `area`, `title`, `status: "implemented" | "partial" | "planned" | "research"`, `simpleExplanation`, `technicalExplanation`, `dependencies`, `evidence`, `snapshotVersion`.
- `roadmap.ts` exports a small evidence-backed catalog only; test-only fixtures live in test files and are marked `TEST DATA`.

- [ ] Write RED tests for examples filling input without network calls, empty M2 states, all pipeline stages, simple/technical expansion, lab disabled controls, allowed roadmap statuses, and fixture secret/path scans.
- [ ] Run focused tests and observe RED.
- [ ] Implement the four screens and catalog with no fake response/ranking/timing.
- [ ] Run focused tests and typecheck; observe GREEN.
- [ ] Commit `feat: add M2 demo narrative screens and roadmap catalog`.

### Task 4: App gating, preservation of normal frontend, and documentation

**Files:**
- Modify: `frontend/App.tsx`
- Modify: `frontend/src/__tests__/app.test.tsx`
- Modify: `frontend/.env.example`
- Modify: `docs/demo-m1.md`
- Modify: `docs/CONTEXTO_CONTINUIDADE.md`

**Interfaces:**
- `App` keeps existing `apiBaseUrl`/`sendChat` props for normal mode and adds no provider call in demo mode.
- `DemoApp` receives the same base URL and optional `demoApi`; M2 may leave live actions disabled.

- [ ] Write RED tests for default normal mode, explicit demo mode, tab switching, preservation of normal chat injection, and no demo request during M2 render.
- [ ] Run `npm test -- --runTestsByPath src/__tests__/app.test.tsx` and observe RED.
- [ ] Add the smallest gate in `App.tsx`, keep the current normal tree unchanged behind it, and mount `DemoShell` only when the flag is true.
- [ ] Run frontend Jest and typecheck; observe GREEN.
- [ ] Run backend tests only if shared contracts changed; otherwise do not call backend/runtime.
- [ ] Update sidequest docs with M2 implemented/verified/limited states, exact flag, local command, responsive targets, and M3 boundary; do not mark M3/M4/M5 implemented.
- [ ] Commit `feat: enable opt-in M2 demo shell`.

### Task 5: Final validation and local handoff

**Files:**
- Modify only files already listed above if a test-driven correction is required.

- [ ] Run `npm test`.
- [ ] Run `npm run typecheck`.
- [ ] Run `git diff --check` and inspect `git status --short --branch`.
- [ ] Perform safe Expo Web visual validation without backend requests, checking 1366x768, 1024x600, 390x844, and 360x800; do not capture secrets or raw payloads.
- [ ] Report branch, commits, files, four-tab behavior, flag, API types/integration status, fixtures, RED/GREEN evidence, Jest/typecheck, QA/security/reviewer results, limitations, clean status, and a detailed M3 proposal.
- [ ] Stop; do not implement M3.
