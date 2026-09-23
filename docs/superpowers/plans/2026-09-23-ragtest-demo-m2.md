# RagTest Demo M2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir a fundação visual opt-in da Demo Técnica no Expo existente, com quatro abas, contratos TypeScript alinhados ao M1, catálogo de roadmap com evidências rastreáveis e cliente preparado para chamadas futuras, sem executar RAG real no M2.

**Architecture:** `App` será um gate sem cache de flag que escolhe entre `NormalApp` e `DemoApp`, dois componentes separados para que hooks e `sendChat` do frontend normal não sejam condicionais. O namespace `frontend/src/demo/` conterá configuração, tipos/API, tokens, layout responsivo, shell, telas e dados versionados; nenhuma tela M2 fará request. A interface continuará desacoplada do backend: o backend mantém `DEMO_ENABLED` e sua allowlist, enquanto o frontend usa `EXPO_PUBLIC_RAG_DEMO_ENABLED` e `EXPO_PUBLIC_RAG_API_BASE_URL` de forma independente.

**Tech Stack:** Expo SDK 57, React Native 0.86, React 19, TypeScript strict, Jest/Jest Expo e React Native Testing Library; nenhum pacote novo de navegação, ícones ou safe-area.

**Spec:** Especificação aprovada do M2 na conversa de 2026-09-23; contrato autoritativo em `app/schemas/demo.py`, restrições de segurança em `docs/demo-m1.md` e contexto em `docs/CONTEXTO_CONTINUIDADE.md`.

## Global Constraints

- A flag frontend só habilita a demo quando `EXPO_PUBLIC_RAG_DEMO_ENABLED` é exatamente `true` após `trim().toLowerCase()`; `undefined`, vazio, `false`, `1`, `yes` e qualquer outro valor preservam o app normal.
- `isDemoEnabled` será chamada em tempo de renderização e não será substituída por uma constante de módulo derivada de `process.env`; os testes poderão alterar o ambiente entre renders.
- `NormalApp` preserva as props `apiBaseUrl?: string` e `sendChat?: SendChat`, o comportamento de envio, retry, grounding, fontes e hooks atuais. `DemoApp` não chama `sendChat`, `fetch`, provider, Qdrant, `/v1/demo/run` ou `/v1/demo/retrieval` durante construção, renderização ou troca de aba.
- Os tipos de resposta copiam exatamente os campos de `app/schemas/demo.py`: `DemoScore`, `DemoSource`, `DemoTimings`, `DemoRetrievalResponse`, `DemoRunResponse` e `DemoRuntimeResponse`; valores nullable continuam nullable e não ganham defaults fabricados.
- `createDemoApi` não tem efeitos colaterais na construção. O parser de erro expõe somente `{ code, status, message }`, nunca corpo bruto, headers, prompt, path, segredo ou exceção.
- As quatro abas são Chat, Como funciona, Laboratório e O que ainda falta. M2 mostra estados vazios/neutros e controles futuros desabilitados; nenhum ranking, resposta, timing, fonte, versão ou status será inventado.
- Layout usa container com `maxWidth: 1120`, largura `min(1120, viewportWidth - 2 * gutter)`, `gutter=24` em desktop e `gutter=16` em telas compactas. Deve ser verificável em 1366x768, 1024x600, 390x844 e 360x800, sem overflow horizontal.
- Em 390x844 e 360x800 as tabs refluem para mais de uma linha ou modo compacto, os cards ficam empilhados e o espaçamento mínimo entre controles é 8. Cada alvo interativo mede pelo menos 48dp (cobrindo o mínimo de 44pt), com `hitSlop` somente como complemento.
- `SafeAreaView`/insets e `ScrollView` content insets protegem notch, status bar, teclado e a área inferior. `frontend/app.json` continua `orientation: "portrait"` para Android/iOS; Expo Web desktop não herda essa restrição e será validado em viewports landscape.
- Acessibilidade deve usar `accessibilityRole` `tab`, `tablist`, `button` e `text` conforme o elemento; `accessibilityState` informa `selected`, `disabled`, `expanded` e `busy`; labels e hints descrevem a ação. O foco Web é ordenado e visível, controles desabilitados não têm ação, e `pressed` produz feedback visível.
- Textos mantêm `allowFontScaling`/Dynamic Type. Estado não pode depender apenas de cor: cada badge/estado tem texto, contraste testado e, se houver símbolo decorativo, ele não é a única informação. Não usar emoji como ícone estrutural.
- Tokens definem explicitamente superfícies, texto, borda, foco, ação, sucesso, alerta e estado desabilitado para temas claro e escuro. Um teste calcula contraste mínimo 4.5:1 para texto normal e 3:1 para texto grande/controles.
- Fixtures e catálogo não podem conter `CHATSCM`, `.env`, API keys, tokens, segredos, caminhos absolutos Windows/Unix, corpos de resposta, excerpts privados ou metadata arbitrária. Evidências precisam ser referências concretas a paths e IDs existentes.
- M2 não altera corpus, embeddings, Qdrant, providers, backend, `app.json` além da verificação de orientação, nem adiciona dependência.

## Review Focus

- **Gate sem cache:** a matriz `undefined`/`""`/`"false"`/`"1"`/`"yes"`/`"TRUE"`/`" true "` deve ser coberta, inclusive após mudar `process.env` entre renders; teste em `demo-api.test.ts` e `app.test.tsx`.
- **Separação normal/demo:** `NormalApp` deve continuar recebendo `sendChat`; em demo, um `sendChat` espião nunca é chamado, nem por render, exemplo, troca de aba ou controle desabilitado; teste em `app.test.tsx`.
- **Responsividade e orientação:** testes de layout verificam os quatro viewports, `maxWidth=1120`, gutters, tabs refluídas, cards empilhados, ausência de overflow e targets; teste Web usa landscape, enquanto teste nativo confirma portrait conforme `app.json`.
- **Acessibilidade e tema:** testes verificam roles/states/labels/hints, foco visível Web, feedback pressed, Dynamic Type, contraste claro/escuro e status que não depende só de cor; teste em `demo-shell.test.tsx` e `demo-tokens.test.ts`.
- **Cliente sem rede:** um fetcher espião confirma zero request na construção de `createDemoApi`, no render de `DemoApp` e na troca de abas; parser retorna somente `code/status/message`; teste em `demo-api.test.ts` e `app.test.tsx`.
- **Dados verificáveis:** exemplos vêm de IDs de `tests/evaluation/retrieval_cases.json`; roadmap usa poucos itens com referências concretas e nunca diz “confirmado” sem evidência; fixture scan falha para secrets, paths absolutos, `CHATSCM` e emoji estrutural.
- **Flags/documentação:** frontend e backend são habilitados independentemente; docs registram comando local, quatro viewports, status M2 com evidências e limite M3, sem marcar M3/M4/M5 como implementados.

### Task 1: Contratos frontend, parser seguro e ativação opt-in

**Files:**
- Create: `frontend/src/demo/config.ts`
- Create: `frontend/src/demo/types/api.ts`
- Create: `frontend/src/demo/api/demo-api.ts`
- Create: `frontend/src/demo/api/demo-api.test.ts`
- Modify: `frontend/.env.example`

**Interfaces:**
- `isDemoEnabled(value?: string): boolean` retorna verdadeiro somente para `value?.trim().toLowerCase() === "true"`; quando chamado sem argumento lê `process.env.EXPO_PUBLIC_RAG_DEMO_ENABLED` naquele momento, sem cache de módulo.
- `DemoRetrievalMode = "dense" | "dense-rerank" | "hybrid"`.
- `DemoScore` tem exatamente `dense_score: number | null`, `sparse_score: number | null`, `rank_score: number | null` e `fusion_score: number | null`.
- `DemoSource` tem exatamente `public_id: string`, `document: string`, `page: number | null`, `order: number`, `excerpt: string` e `scores: DemoScore`.
- `DemoTimings` tem `retrieval_ms: number`, `generation_ms: number | null` e `total_ms: number`.
- `DemoRetrievalRequest` tem `query: string`, `limit?: number`, `category?: string | null`, `audience?: string | null`, `min_score?: number | null` e `retrieval_mode?: DemoRetrievalMode | null`; `DemoRunRequest` é o mesmo contrato, sem campos extras.
- `DemoRetrievalResponse` tem `query`, `retrieval_mode`, `sources: DemoSource[]` e `timings: DemoTimings | null`; `DemoRunResponse` tem `answer`, `model`, `grounded`, `citation_ids: number[]`, `sources` e `timings: DemoTimings`; `DemoRuntimeResponse` tem exatamente `version`, `provider`, `model`, `embedding`, `retrieval`, `collection`, `demo_enabled`, `policy_id` e `policy_status: "configured" | "blocked"`; exporte `type DemoRuntime = DemoRuntimeResponse` apenas como alias de conveniência.
- `DemoApiError = { code: string; status: number | null; message: string }`; `code` preserva somente o código sanitizado do contrato M1 (por exemplo `retrieval_unavailable` ou `generation_unavailable`) ou um fallback estável do cliente. Nenhum tipo público do cliente expõe o corpo HTTP.
- `DemoFetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>` e `DemoApi = ReturnType<typeof createDemoApi>` são os únicos pontos de injeção/teste; nenhum método é executado ao construir o cliente.
- `createDemoApi(baseUrl: string, fetcher?: DemoFetcher)` normaliza somente a barra final e retorna `getRuntime(): Promise<DemoRuntime>`, `run(request: DemoRunRequest): Promise<DemoRunResponse>` e `retrieve(request: DemoRetrievalRequest): Promise<DemoRetrievalResponse>`.

- [ ] **Step 1: Write the failing test.** Em `demo-api.test.ts`, escreva testes para a matriz de sete valores da flag, incluindo mutação de `process.env` entre duas chamadas após o módulo já estar importado; teste que URL com barra final gera `/v1/demo/runtime` uma única vez e que payloads preservam `null` em scores/timings; teste os três métodos com respostas mínimas válidas alinhadas ao schema; teste HTTP, rede e JSON inválido para confirmar que o erro público contém somente `code`, `status` e `message`, sem segredo/corpo bruto.
- [ ] **Step 2: Run the focused test to verify RED.** Execute `cd frontend; npm test -- --runTestsByPath src/demo/api/demo-api.test.ts`; espere falha por módulos/contratos ainda inexistentes, não ajuste o teste para passar.
- [ ] **Step 3: Write the minimal implementation.** Implemente os tipos fechados, `isDemoEnabled`, `createDemoApi` e um parser que converta erro HTTP/rede/resposta inválida para `{ code, status, message }`. O `fetcher` só será invocado dentro dos métodos; construção, import e normalização da URL não fazem request nem `console.log`.
- [ ] **Step 4: Run focused tests to verify GREEN.** Execute novamente o teste focado e confirme que nenhum campo fora dos contratos aparece no resultado. Depois rode `cd frontend; npm run typecheck`.
- [ ] **Step 5: Commit.** Faça `git add frontend/src/demo frontend/.env.example` e commit local `feat: add typed opt-in demo frontend client`.

### Task 2: Tokens, layout responsivo, shell e navegação acessível

**Files:**
- Create: `frontend/src/demo/components/demo-shell.tsx`
- Create: `frontend/src/demo/components/demo-tabs.tsx`
- Create: `frontend/src/demo/components/demo-header.tsx`
- Create: `frontend/src/demo/components/demo-card.tsx`
- Create: `frontend/src/demo/components/demo-status-badge.tsx`
- Create: `frontend/src/demo/components/demo-tokens.ts`
- Create: `frontend/src/demo/components/demo-tokens.test.ts`
- Create: `frontend/src/demo/types/navigation.ts`
- Create: `frontend/src/demo/components/demo-shell.test.tsx`

**Interfaces:**
- `DemoTabId = "chat" | "how-it-works" | "laboratory" | "roadmap"`.
- `DemoShell({ activeTab, onTabChange, children, runtimeState })` renderiza `SafeAreaView`, header, aviso local/desenvolvimento, slot neutro de runtime e container responsivo; `runtimeState` é texto/estado já sanitizado, nunca uma resposta da API.
- `DemoCard({ title, children, accessibilityLabel, expanded?, disabled?, onPress? })` e `DemoStatusBadge({ label, tone })` mostram texto visível; `DemoCard` usa `accessibilityState.expanded/disabled` e o badge não comunica status só por cor.
- `getDemoLayout(viewportWidth, viewportHeight, platform)` retorna `containerWidth`, `gutter`, `isCompact`, `tabsWrap`, `cardsDirection` e `hasHorizontalOverflow: false`; `platform` distingue `"web"` de `"native"` para que portrait nativo não seja confundido com Web landscape.

- [ ] **Step 1: Write the failing tests.** Em `demo-shell.test.tsx`, cubra as quatro labels e IDs, `role=tablist`, `role=tab`, `selected`, tab order, labels/hints, aviso neutro, `disabled`, `expanded`, pressed feedback e foco Web visível. Em teste de layout, avalie 1366x768 e 1024x600 com container 1120/gutters 24, e 390x844 e 360x800 com tabs refluídas, cards em coluna, gap mínimo 8 e overflow falso; inclua target mínimo 48.
- [ ] **Step 2: Run focused tests to verify RED.** Execute `cd frontend; npm test -- --runTestsByPath src/demo/components/demo-shell.test.tsx`; espere falhas por componentes/layout ausentes.
- [ ] **Step 3: Write the minimal implementation.** Defina tokens `light` e `dark` com pares de cores contrastantes, `focusOutline`, espaçamento 8/16/24, container 1120 e tipografia escalável. Use `useWindowDimensions`, `SafeAreaView`, `ScrollView` e content insets; no Web aplique foco visível e permita landscape, no nativo preserve o portrait de `app.json`. Use tabs com `role=tablist`/`tab`, `selected` e `onTabChange`; use `Pressable` com estilo dependente de `{ pressed }`, sem emoji estrutural.
- [ ] **Step 4: Run focused tests to verify GREEN.** Execute o teste focado, `cd frontend; npm run typecheck` e o teste de contraste (razão mínima 4.5:1 para texto normal e 3:1 para texto grande/controles) para ambos os temas.
- [ ] **Step 5: Commit.** Faça `git add frontend/src/demo/components frontend/src/demo/types` e commit local `feat: add responsive demo shell and tab navigation`.

### Task 3: Quatro telas M2 e catálogo de roadmap com evidências

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
- `DemoChatScreen({ value, onChange, onExamplePress })` mostra narrativa, input rotulado, exemplos derivados de `tests/evaluation/retrieval_cases.json` por `caseId`, slots vazios de conversa/fontes/grounding e ação futura desabilitada; exemplo chama somente `onExamplePress(example)`.
- `PipelineStage` aceita `{ id, title, simpleExplanation, technicalDetails, state: "awaiting-execution", expanded, onToggle }`; a expansão informa `expanded` e usa `accessibilityState` sem fabricar execução.
- `LabModeCard` expõe modo e explicação, mas seus controles são `disabled`, não têm `onPress` efetivo e indicam que chamadas pertencem ao M4. **Alinhamento pós-review:** o Laboratório/controles futuros não fazem parte da fronteira M3.
- `RoadmapEvidence = { kind: "test" | "source" | "document"; reference: string; label: string }`; `RoadmapItem` tem `id`, `area`, `title`, `status: "implemented" | "partial" | "planned" | "research"`, `simpleExplanation`, `technicalExplanation`, `dependencies: string[]`, `evidence: RoadmapEvidence[]` não vazia e `snapshotVersion` copiada de uma versão existente no repositório.
- `roadmap.ts` exporta poucos itens com referências concretas, como `tests/evaluation/retrieval_cases.json#0`, `tests/test_demo.py::test_demo_dtos_forbid_extra_fields_and_retrieval_mode_is_closed`, `tests/test_demo.py::test_demo_runtime_is_sanitized_and_retrieval_has_no_provider_dependency` e `docs/demo-m1.md:5-27`; não usa texto “confirmado” sem essa evidência. Cada exemplo e status deve poder ser conferido sem provider, Qdrant ou fonte privada.
- Fixtures exclusivamente de teste ficam nos arquivos de teste e são marcadas literalmente como `TEST DATA`; o catálogo de produção não reutiliza respostas ou excerpts de fixture.

- [ ] **Step 1: Write the failing tests.** Em `demo-screens.test.tsx`, teste os exemplos preenchendo o input sem `fetch`/`sendChat`, estados vazios sem respostas/timings/rankings, todos os stages com expansão simples/técnica, controles de laboratório desabilitados sem callback, statuses permitidos, `evidence` com referências concretas e o scan de fixtures/catalog para secrets, `.env`, paths absolutos, `CHATSCM` e emojis estruturais.
- [ ] **Step 2: Run focused tests to verify RED.** Execute `cd frontend; npm test -- --runTestsByPath src/demo/screens/demo-screens.test.tsx`; espere falhas por telas, catálogo e tipos inexistentes.
- [ ] **Step 3: Write the minimal implementation.** Renderize as quatro telas e componentes com cópia neutra; empilhe cards no modo compacto e preserve Dynamic Type. Copie somente perguntas/IDs existentes em `retrieval_cases.json`; não copie excerpts, respostas, scores, tempos ou fontes como se fossem resultados M2. No catálogo, use somente referências concretas no formato `caminho:linha` ou `caminho#id`, verificadas no workspace antes de incluí-las.
- [ ] **Step 4: Run focused tests to verify GREEN.** Execute o teste focado, `cd frontend; npm run typecheck` e confirme que os scans permanecem verdes após qualquer ajuste de fixture.
- [ ] **Step 5: Commit.** Faça `git add frontend/src/demo/screens frontend/src/demo/components frontend/src/demo/data frontend/src/demo/types` e commit local `feat: add M2 demo narrative screens and roadmap catalog`.

### Task 4: Gate do App, preservação do frontend normal e documentação

**Files:**
- Modify: `frontend/App.tsx`
- Modify: `frontend/src/__tests__/app.test.tsx`
- Modify: `frontend/.env.example`
- Modify: `docs/demo-m1.md`
- Modify: `docs/CONTEXTO_CONTINUIDADE.md`

**Interfaces:**
- `App(props: AppProps)` chama `isDemoEnabled()` em cada render e retorna `DemoApp` ou `NormalApp`; não contém hooks condicionais. `NormalApp` mantém o corpo atual e as props `apiBaseUrl?: string`/`sendChat?: SendChat` sem alterar o contrato.
- `DemoApp({ apiBaseUrl?: string, demoApi?: DemoApi })` monta o shell e estado de aba sem executar métodos da API; aceitar `demoApi` injetado permite testar que nenhum request ocorre.

- [ ] **Step 1: Write the failing tests.** Em `app.test.tsx`, isole `process.env` por teste e cubra flag ausente/diferente de `true`, demo explícita, troca de todas as abas, preservação do envio normal, `sendChat` espião nunca chamado no demo e `fetcher`/métodos `demoApi` nunca chamados na construção, render, exemplo ou troca de aba. Verifique também que props do app normal continuam aceitas.
- [ ] **Step 2: Run the focused test to verify RED.** Execute `cd frontend; npm test -- --runTestsByPath src/__tests__/app.test.tsx`; espere falha porque o gate e `DemoApp` ainda não existem.
- [ ] **Step 3: Write the minimal implementation.** Extraia o JSX/hook tree atual para `NormalApp` sem mudar sua lógica. Adicione `DemoApp` separado, injete ou construa `createDemoApi` sem efeitos e monte somente `DemoShell`; não instancie request em `useEffect`, render ou troca de tab. O frontend `.env.example` documenta `EXPO_PUBLIC_RAG_DEMO_ENABLED` separadamente das flags backend `DEMO_ENABLED`/`DEMO_ALLOWED_SOURCE_PREFIXES`.
- [ ] **Step 4: Run focused tests to verify GREEN.** Execute `cd frontend; npm test -- --runTestsByPath src/__tests__/app.test.tsx`, depois `npm test` e `npm run typecheck`. Não execute backend/runtime: M2 não mudou contratos backend.
- [ ] **Step 5: Update documentation with evidence.** Em `docs/demo-m1.md` e `docs/CONTEXTO_CONTINUIDADE.md`, registre o estado de M1, o estado real de M2 (`implementado`, `aguardando validação` ou `verificado` somente conforme testes/visualização executados), os flags independentes, o comando local `cd frontend; $env:EXPO_PUBLIC_RAG_DEMO_ENABLED="true"; npm run web`, os quatro viewports e a orientação portrait nativa/Web landscape. Declare M3 como fronteira futura para requests/replay/execução demo; não marque M3, M4 ou M5 como implementados.
- [ ] **Step 6: Commit.** Faça `git add frontend/App.tsx frontend/src/__tests__/app.test.tsx frontend/.env.example docs/demo-m1.md docs/CONTEXTO_CONTINUIDADE.md` e commit local `feat: enable opt-in M2 demo shell`.

### Task 5: Validação final e handoff local

**Files:**
- Modify only files already listed above if a test-driven correction is required; não alterar backend, corpus, Qdrant, providers, secrets ou `app.json`.

- [ ] **Step 1: Run automated validation.** Em `frontend`, execute `npm test` e `npm run typecheck`; na raiz execute `git diff --check`. Registre a contagem e a saída, sem declarar sucesso por inferência.
- [ ] **Step 2: Validate orientation and layout safely.** Confirme em `frontend/app.json` que Android/iOS continuam `orientation: "portrait"`; abra Expo Web com a flag frontend e verifique 1366x768, 1024x600, 390x844 e 360x800. Em desktop Web use landscape; em nativo use portrait. Confirme container/gutters, tabs refluídas, cards empilhados, safe area, foco, targets e ausência de overflow horizontal.
- [ ] **Step 3: Validate no network and no sensitive output.** Mantenha backend desligado ou observe a aba Network sem requests a `8000`/`/v1/demo/*`; não capture secrets, payloads, respostas, paths pessoais ou conteúdo CHATSCM. O resultado esperado é a demo M2 renderizar apenas estados neutros.
- [ ] **Step 4: Inspect workspace.** Execute `git status --short --branch` e `git diff --stat`; confirme que somente os arquivos previstos foram alterados e que nenhum `.env`, fixture privado ou artefato Expo entrou no diff.
- [ ] **Step 5: Report handoff.** Informe branch, commits, arquivos, comportamento das quatro abas, matriz da flag, contratos/API sem integração de rede, evidências do catálogo, RED/GREEN, Jest/typecheck, validação dos quatro viewports, riscos restantes e M3 boundary. O próximo agente deve começar pelo gate/contratos e não implementar M3 neste plano.
