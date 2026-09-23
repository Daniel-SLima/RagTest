# RagTest Demo M3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar a aba `Chat` da Demo Técnica à execução live controlada do M1, apresentar apenas os DTOs sanitizados recebidos e reutilizar a mesma execução na aba `Como funciona`, sem ampliar o backend, o contrato ou o Laboratório do M4.

**Architecture:** `App` continuará separando `NormalApp` e `DemoApp`. A demo criará o cliente REST de forma pura, fará exatamente um `GET /v1/demo/runtime` por montagem e executará `POST /v1/demo/run` somente após submissão explícita. Um `DemoRunState` único conservará pergunta, resposta, diagnósticos sanitizados, runtime, status e erro; `Chat` e `Como funciona` receberão esse mesmo estado, portanto trocar de aba ou avançar a apresentação nunca fará nova request. O cliente terá validadores fechados para runtime, resposta e campos aninhados, e adaptadores próprios para `DemoSource`, sem cast para `ChatSource`.

**Tech Stack:** Expo SDK 57, React Native 0.86, React 19, TypeScript strict, Jest/Jest Expo, React Native Testing Library e o cliente REST tipado já criado no M2. Nenhum pacote, rota, provider, corpus, collection ou dependência nova será adicionado.

**Spec:** Especificação aprovada da sidequest M3 na conversa de 2026-09-23; contrato autoritativo em `app/schemas/demo.py` e `app/api/routes/demo.py`; limites M1/M2 em `docs/demo-m1.md` e `docs/CONTEXTO_CONTINUIDADE.md`.

## Global Constraints

- O fluxo principal é `Chat -> POST /v1/demo/run -> resposta sanitizada -> DemoRunState -> Chat + Como funciona`; `GET /v1/demo/runtime` ocorre uma vez por montagem da `DemoApp` e não por troca de aba.
- Os únicos endpoints usados pelo M3 são `GET /v1/demo/runtime` e `POST /v1/demo/run`. O método tipado `retrieve` pode permanecer no cliente M1, mas não é chamado pelo M3 e não vira superfície do Laboratório.
- O contrato M1 permanece fechado e sem extensão backend. Os campos reais disponíveis são `answer`, `model`, `grounded`, `citation_ids`, `sources.public_id`, `sources.document`, `sources.page`, `sources.order`, `sources.excerpt`, `sources.scores` nullable, `timings` e `runtime`.
- Validadores em runtime devem rejeitar campos ausentes, extras, tipos incompatíveis, números não finitos ou fora das restrições do DTO e JSON inválido. O cliente nunca armazena ou expõe o corpo bruto, headers, traceback, prompt, path, URL interna, segredo ou mensagem crua de provider.
- `DemoApiError` permanece estável como `{ code: string; status: number | null; message: string }`. Mensagens exibidas são mapeadas pelo cliente; nenhum erro bruto entra no estado, na tela, em `console` ou em teste de snapshot.
- A validação de `baseUrl` permite `http` somente para loopback (`localhost`, `127.0.0.0/8`, `::1`) ou IPv4 privado RFC1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`); portas ausentes ou entre 1 e 65535 são aceitas e portas inválidas são rejeitadas. `https` não é aceito por ser HTTPS apenas: cada origem HTTPS precisa estar em uma allowlist explícita fornecida/documentada pelo operador, com origem exata (`scheme://host:port`), sem curingas; sem essa configuração, `https://example.com`, `https://192.168.1.20` e `https://localhost` são rejeitados. Rejeita credenciais, query string, hash, protocolo diferente de HTTP(S), host ausente e URL malformada. Não implementa autenticação completa.
- Não alterar CORS para `*`. A comunicação Web depende de origem local explicitamente permitida pelo backend já existente; fora de ambiente controlado, `DEMO_ENABLED` deve permanecer desativado.
- A rota M1 chama `answer_with_rag(..., auto_decompose=False)`: a UI deve exibir a frase de configuração **"O endpoint demo M1 está configurado para executar single-query nesta versão"**, separada de qualquer diagnóstico retornado. Multi-query, decomposição, retry count, ranking pré/pós, contexto final enviado ao LLM e dimensão do embedding ficam como `Não disponível`/indisponível; não podem ser inferidos de `sources`, scores, timings ou texto da resposta.
- Scores nullable permanecem nullable. `null` nunca vira `0`; quando a tela precisar de texto, usa `Não disponível` e informa a origem do score somente quando o campo real existir.
- Grounding é apresentado como cobertura estrutural de citações; `grounded=true` não é garantia clínica, entailment semântico nem verdade factual absoluta.
- O loading mostra somente estado honesto, como `Executando o RagTest...`; não anima etapas de embedding, Qdrant, reranking ou LLM enquanto o backend não transmite esses eventos.
- Exemplos continuam sendo atalhos de preenchimento. Clicar em um exemplo não submete, não chama `sendChat`, não chama `fetch` e não contém resposta hardcoded.
- Retry é manual e explícito, reutiliza a última pergunta e não mostra contagem de retry, pois esse campo não existe no DTO M1.
- `Como funciona` possui dois modos visuais sobre a mesma execução: automático/`Ver tudo`, com todas as etapas disponíveis, e apresentação, com `Anterior`, `Próximo` e uma etapa por vez. Nenhum controle desses modos faz request.
- O Laboratório e seus controles continuam visuais e desabilitados; dense, dense-rerank, hybrid, Top K e multi-query experimental pertencem ao M4. M3 não implementa replay, fixtures de execução real, gravação de respostas ou arquivos de replay.
- O backend, providers, parâmetros de retrieval, embeddings, corpus, Qdrant, Docker, `.env`, CORS, configuração de agentes e autenticação permanecem sem alteração. Se o contrato M1 não bastar, interromper e relatar em vez de ampliá-lo.
- Nenhuma validação live deve chamar provider externo automaticamente. Testes usam fetch mockado. A validação real depende de ambiente controlado previamente configurado, fonte permitida pela allowlist M1 e autorização operacional do usuário; sem isso, registrar o procedimento e marcar como aguardando validação.

## Review Focus

- **Contrato fechado e números:** runtime/resposta válida passa; missing, extra, `NaN`/`Infinity`, número negativo, score malformado, `order` não inteiro ou JSON inválido falham com erro sanitizado. Cobrir em `demo-api.test.ts`.
- **Allowlist de origem:** HTTP passa somente para loopback/RFC1918; HTTPS passa somente para uma origem exata explicitamente configurada pelo operador. `https://example.com`, `https://192.168.1.20` e `https://localhost` sem allowlist, credenciais, query/hash, `file:`, host público em HTTP, porta inválida e IPv6 não-loopback falham antes de qualquer request. Cobrir em `demo-api.test.ts`.
- **Request única:** `getRuntime` acontece uma vez por montagem; `run` só acontece no submit/retry explícito; render, construção, exemplos e troca de aba não fazem chamada. Cobrir em `app.test.tsx` e `demo-run-state.test.ts`.
- **Fonte única de estado:** resposta, fontes, scores, grounding, timings e runtime usados em `Chat` são os mesmos que `Como funciona` usa; clicar no botão de pipeline não reexecuta. Cobrir em `demo-screens.test.tsx` e `how-it-works-screen.test.tsx`.
- **Granularidade honesta:** a frase "O endpoint demo M1 está configurado para executar single-query nesta versão" é uma informação estática da rota (`auto_decompose=False`), não um diagnóstico do response; decomposition, multi-query, retry count, pré/pós-reranking, contexto final e dimensão de embedding aparecem como indisponíveis. Cobrir no modelo de pipeline.
- **Adapter de fontes:** `DemoSource.order`/`public_id` é interpretado sem cast para `ChatSource`; citações verificadas mostram apenas fontes cujo `order` está em `citation_ids`, enquanto `grounded=false` pode mostrar fontes recuperadas sem marcá-las como citações. Cobrir estados `grounded=true/false` e sources vazias.
- **Privacidade de erro:** corpo HTTP contendo token, path ou texto de provider nunca aparece em `DemoApiError`, tela, estado ou logs. Cobrir erro HTTP, rede, JSON inválido e resposta com campos extras.
- **Visual sem falsa conclusão:** executar o gate nos quatro viewports; se o navegador embutido não permitir controlar dimensões ou a captura não for observável, reportar cada viewport como `aguardando validação manual`, nunca como verificado.

## Files and Interfaces Map

### API e validação

- Modify `frontend/src/demo/types/api.ts`: preservar os DTOs M1 exatamente e adicionar somente aliases de validação/erro necessários; não adicionar campos ao `DemoRunResponse` ou `DemoRuntimeResponse`.
- Modify `frontend/src/demo/config.ts`: adicionar `getAllowedHttpsOrigins(value?: string): readonly string[]`, lendo somente a configuração pública `EXPO_PUBLIC_RAG_ALLOWED_HTTPS_ORIGINS`, separando origens por vírgula, descartando entradas vazias e rejeitando curingas, credenciais, query/hash e origens não HTTPS.
- Modify `frontend/src/demo/api/demo-api.ts`: manter `createDemoApi(baseUrl, fetcher?)`, `getRuntime`, `run` e `retrieve`; tornar normalização de URL, validação de request, parsing de resposta e erro estritos e sem efeitos colaterais.
- Create `frontend/src/demo/api/demo-api-validation.ts`: funções puras `validateDemoBaseUrl`, `parseDemoRuntime`, `parseDemoRunResponse`, `parseDemoRetrievalResponse`, `parseDemoSource`, `parseDemoScore` e `parseDemoTimings`, todas retornando DTOs fechados ou lançando `DemoApiError` sanitizado.
- Modify `frontend/src/demo/api/demo-api.test.ts`: ampliar testes de URL, validadores, campos nullable, extras/missing/números inválidos e corpo bruto.
- Modify `frontend/.env.example`: documentar `EXPO_PUBLIC_RAG_ALLOWED_HTTPS_ORIGINS` como lista pública de origens HTTPS exatas, vazia por padrão e sem `*`; não incluir credenciais.

### Estado da execução

- Create `frontend/src/demo/types/run-state.ts`: `DemoRunStatus`, `DemoRuntimeStatus`, `DemoRunDiagnostics`, `DemoRunState` e tipos dos callbacks. `DemoRunState` é a única fonte de runtime e execução; `diagnostics` é projeção somente leitura de `response`/`runtime`, não uma segunda fonte mutável.
- Create `frontend/src/demo/state/demo-run-state.ts`: reducer/funções puras para eventos `runtime-loading`, `runtime-success`, `runtime-error`, `run-loading`, `run-success` e `run-error`; `toDemoDiagnostics(response, runtime)` copia apenas campos dos DTOs sanitizados.
- Não criar `use-demo-runtime.ts` nem um hook separado que mantenha runtime duplicado. `DemoApp` usa diretamente `useReducer(demoRunReducer, initialDemoRunState)` e despacha tanto os eventos do `GET /runtime` quanto os eventos do `POST /run` no mesmo estado.
- Create `frontend/src/demo/state/demo-run-state.test.ts`: RED/GREEN de loading, sucesso, erro, retry, campos null, fontes vazias, sem raw body, sem chamada duplicada e preservação da execução concluída durante eventos de runtime.

### Apresentação

- Create `frontend/src/components/answer-presentation.tsx`: componente visual genérico para Markdown, grounding e cartões de fontes, consumindo um `AnswerPresentationModel` agnóstico do contrato.
- Modify `frontend/src/components/assistant-answer.tsx`: adaptar `ChatApiResponse` ao modelo genérico sem mudar o comportamento normal do app.
- Create `frontend/src/demo/components/demo-answer.tsx`: adaptador específico de `DemoRunResponse` que usa `public_id`, `document`, `page`, `order`, `excerpt` e scores nullable; nenhum `as ChatSource`.
- Modify `frontend/src/demo/screens/demo-chat-screen.tsx`: aceitar estado/callbacks live, submit/retry/pipeline e preservar exemplos como preenchimento.
- Modify `frontend/src/demo/screens/demo-screens.test.tsx`: estados live, grounding, fontes, scores e ação de pipeline sem rede.

### Runtime, app e pipeline

- Modify `frontend/App.tsx`: manter `NormalApp` intacto em contrato e hooks; tornar `DemoApp` responsável por cliente estável, runtime, `DemoRunState`, aba e modo de apresentação.
- Modify `frontend/src/__tests__/app.test.tsx`: flag, runtime once, submit explícito, retry, troca de aba sem request e preservação de `sendChat` normal.
- Create `frontend/src/demo/state/demo-pipeline-model.ts`: construir as 11 etapas a partir de `DemoRunState`; declarar single-query e estados `available`, `not-required`, `unavailable` e `not-measured` sem inferência.
- Modify `frontend/src/demo/components/pipeline-stage.tsx`: renderizar estados M3, detalhes reais e `Não disponível`, mantendo acessibilidade e modo sem execução.
- Modify `frontend/src/demo/screens/how-it-works-screen.tsx`: receber estado e modo, oferecer `Anterior`, `Próximo`, `Ver tudo`, destaque inicial e empty/error state sem API.
- Create `frontend/src/demo/state/demo-pipeline-model.test.ts` e `frontend/src/demo/screens/how-it-works-screen.test.tsx`: dados reais, campos indisponíveis e apresentação sem request.

## Task 0: Gate visual M2 antes de tocar no fluxo live

**Files:** nenhum arquivo deve ser modificado nesta tarefa.

- [ ] **Step 1: Confirmar a base local.** Executar `git status --short --branch`, `git log -1 --oneline` e confirmar que a branch é `sidequest/ragtest-demo`, sem descartar alterações. Ler `docs/demo-m1.md`, `docs/CONTEXTO_CONTINUIDADE.md`, `app/schemas/demo.py` e `app/api/routes/demo.py` antes da implementação.
- [ ] **Step 2: Abrir o M2 sem backend.** Em PowerShell, usar `cd frontend; $env:EXPO_PUBLIC_RAG_DEMO_ENABLED="true"; $env:EXPO_PUBLIC_RAG_API_BASE_URL="http://127.0.0.1:65534"; npm run web`. Não iniciar provider, Qdrant ou backend para este gate.
- [ ] **Step 3: Inspecionar quatro viewports.** Verificar `1366x768`, `1024x600`, `390x844` e `360x800`: header, quatro tabs, cards, pipeline, foco, targets, safe-area, ausência de overflow e textos sem corte. Expo Web usa landscape; o app nativo continua portrait conforme `frontend/app.json`.
- [ ] **Step 4: Registrar a limitação.** Se o IAB/navegador disponível não permitir fixar dimensões ou a captura não puder ser observada de modo confiável, não forçar workaround: anotar cada viewport como `aguardando validação manual` para o documenter. Nenhum defeito M2 deve ser silenciosamente atribuído ao M3; correção visual necessária deve ser reportada separadamente.

## Task 1: Fechar o cliente M1 e a validação de origem/DTO

**Files:**
- Modify: `frontend/src/demo/types/api.ts`
- Create: `frontend/src/demo/api/demo-api-validation.ts`
- Modify: `frontend/src/demo/api/demo-api.ts`
- Modify: `frontend/src/demo/api/demo-api.test.ts`

**Interfaces:**

- `getAllowedHttpsOrigins(value?: string): readonly string[]` transforma a configuração pública em origens HTTPS exatas; valor ausente/vazio produz lista vazia e, portanto, não libera nenhum HTTPS.
- `validateDemoBaseUrl(value: string, options?: { allowedHttpsOrigins?: readonly string[] }): string` aceita HTTP apenas em loopback/RFC1918 e HTTPS somente se a origem normalizada estiver exatamente em `allowedHttpsOrigins`; retorna a URL sem barra final, ou lança `{ code: "invalid_demo_base_url", status: null, message: "URL do serviço de demonstração inválida." }`. A lista HTTPS não aceita curinga e deve vir de configuração pública explicitamente documentada pelo operador.
- `parseDemoRuntime(value: unknown): DemoRuntime` exige exatamente as chaves `version`, `provider`, `model`, `embedding`, `retrieval`, `collection`, `demo_enabled`, `policy_id`, `policy_status`, strings não vazias, boolean real e enum fechado.
- `parseDemoRunResponse(value: unknown): DemoRunResponse` exige exatamente `answer`, `model`, `grounded`, `citation_ids`, `sources`, `timings`; cada fonte exige exatamente `public_id`, `document`, `page`, `order`, `excerpt`, `scores`; cada score aceita `null` ou número finito; `order` e `citation_ids` são inteiros positivos; timings são finitos e não negativos, com `generation_ms` nullable.
- `parseDemoRetrievalResponse(value: unknown): DemoRetrievalResponse` aplica o mesmo fechamento ao método M1 já existente, mas M3 não o chama.
- `DemoApi` executa `fetcher` somente dentro de `getRuntime`, `run` ou `retrieve`. Construção, import e normalização não fazem request nem log.
- `run` valida `query` trimada com comprimento 2–2000, `limit` 1–10, `category`/`audience` no máximo 100, `min_score` finito entre -1 e 1 e `retrieval_mode` no enum; erro local não chama a rede.

- [ ] **Step 1: Write the failing tests.** Em `demo-api.test.ts`, adicione testes para `http://localhost:8000/`, `http://127.0.0.1:8000`, `http://127.0.0.1:65535`, `http://192.168.1.20:8000` e `http://[::1]:8000`; rejeite `http://8.8.8.8`, `http://[2001:db8::1]:8000`, porta `0`/`65536` ou malformada, `file:`, usuário/senha, `?token=x`, `#fragment` e URLs malformadas. Com `allowedHttpsOrigins=[]`, rejeite `https://example.com`, `https://192.168.1.20` e `https://localhost`; com allowlist exata, aceite somente `https://localhost:8443`, `https://192.168.1.20:8443` ou a porta IPv6 explicitamente listada, rejeitando host/porta diferentes e `*`. Adicione fixtures `TEST DATA` mínimas para runtime/run/retrieval válidos, removendo campos extras e criando casos de missing, score string/`NaN`, timing negativo, order decimal, `citation_ids` inválido, `sources` extra e JSON não objeto. Verifique `Object.keys(error)` exatamente como `code/status/message` e que um corpo contendo `secret`, path ou traceback não aparece em mensagem, estado ou chamada de log.
- [ ] **Step 2: Run focused tests to verify RED.** Executar `cd frontend; npm test -- --runTestsByPath src/demo/api/demo-api.test.ts`; esperar falhas porque o cliente M2 ainda faz cast direto do JSON e não aplica allowlist/validadores fechados.
- [ ] **Step 3: Write the minimal implementation.** Implementar os type guards/pasers puros, a política de URL e a validação dos requests. Fazer `getJson` ler o JSON apenas para validação; em qualquer falha, descartar o valor e lançar apenas `DemoApiError`. Preservar somente códigos públicos M1 (`invalid_retrieval_mode`, `source_policy_blocked`, `retrieval_unavailable`, `generation_unavailable`, `retrieval_failed`, `generation_failed`, `invalid_demo_request`, `demo_disabled`) ou `invalid_demo_response`/`demo_api_error`.
- [ ] **Step 4: Run focused tests to verify GREEN.** Executar novamente o teste focado e `cd frontend; npm run typecheck`. Confirmar que normalizar barra final gera `/v1/demo/runtime` uma única vez quando `getRuntime()` é chamado, sem request na construção.
- [ ] **Step 5: Commit.** Fazer commit local somente do cliente/validadores: `feat: harden M3 demo client contracts`.

## Task 2: Criar estado único da execução e runtime once

**Files:**
- Create: `frontend/src/demo/types/run-state.ts`
- Create: `frontend/src/demo/state/demo-run-state.ts`
- Create: `frontend/src/demo/state/demo-run-state.test.ts`

**Interfaces:**

- `DemoRunState` expõe `question: string | null`, `response: DemoRunResponse | null`, `diagnostics: DemoRunDiagnostics | null`, `runtime: DemoRuntime | null`, `runtimeStatus: DemoRuntimeStatus`, `runtimeError: DemoApiError | null`, `status: DemoRunStatus` e `error: DemoApiError | null`. `DemoRunDiagnostics` contém somente `answer`, `model`, `grounded`, `citation_ids`, `sources`, `timings` e `runtime`; é calculado de forma pura de `response`/`runtime` pelo mesmo reducer.
- `demoRunReducer(state, action): DemoRunState` é a única transição autorizada. `runtime-loading`, `runtime-success` e `runtime-error` atualizam somente runtime/status/erro de runtime e recalculam a projeção, preservando question/response/status/error de uma execução já concluída. `run-loading`, `run-success` e `run-error` atualizam o run sem apagar runtime válido.
- `DemoApp` chama `getRuntime()` uma vez por montagem em um `useEffect` com cliente estável e despacha os eventos no reducer; `submit(question)` e `retry()` são callbacks de `DemoApp` que despacham run loading/success/error. Não existe hook runtime paralelo.

- [ ] **Step 1: Write the failing tests.** Crie reducer/App tests com `DemoApi` mockado: estado idle; pergunta inválida não chama API; submit emite loading e depois sucesso com runtime e diagnóstico; erro HTTP/rede preserva pergunta sem raw body; retry explícito produz exatamente uma segunda chamada; scores/timings nullable permanecem null; `getRuntime` é chamado uma vez no mount mesmo após rerender; evento `runtime-error` depois de run success preserva response/diagnostics e só atualiza runtime status/erro; evento `runtime-success` atualiza o runtime na mesma projeção sem apagar a resposta; unmount/aba não dispara run.
- [ ] **Step 2: Run focused tests to verify RED.** Executar `cd frontend; npm test -- --runTestsByPath src/demo/state/demo-run-state.test.ts src/__tests__/app.test.tsx`; esperar falha por reducer/integração inexistentes.
- [ ] **Step 3: Write the minimal implementation.** Implementar um único reducer no `DemoApp`, `useMemo` somente para cliente estável, `useRef` para impedir chamadas duplicadas da mesma montagem e `useEffect` somente para despachar eventos runtime. `submit` deve trimar a pergunta, limpar resposta/erro anterior, marcar run loading, chamar `api.run({ query })` e despachar somente o DTO validado; `retry` deve reutilizar `state.question` e retornar cedo durante loading ou sem pergunta. Eventos runtime nunca resetam a execução.
- [ ] **Step 4: Run focused tests to verify GREEN.** Executar os testes focados, `cd frontend; npm run typecheck` e confirmar que nenhuma transição aceita corpo HTTP, headers ou exceção como campo do estado.
- [ ] **Step 5: Commit.** Fazer commit local `feat: add sanitized demo run state`.

## Task 3: Integrar Chat live e adaptar resposta/fontes sem cast

**Files:**
- Create: `frontend/src/components/answer-presentation.tsx`
- Modify: `frontend/src/components/assistant-answer.tsx`
- Create: `frontend/src/demo/components/demo-answer.tsx`
- Modify: `frontend/src/demo/screens/demo-chat-screen.tsx`
- Modify: `frontend/src/demo/screens/demo-screens.test.tsx`

**Interfaces:**

- `AnswerPresentationModel` contém `answer`, `grounded`, `sources`, `sourcesTitle` e `showCitationId`; cada fonte de apresentação contém `key`, `citationLabel?`, `document`, `page: number | null`, `excerpt` e `scores` opcionais.
- `DemoAnswer({ response }: { response: DemoRunResponse })` mapeia diretamente `DemoSource` para o modelo genérico. Para `grounded=true`, filtra fontes por `citation_ids.includes(source.order)`; para `grounded=false`, mostra fontes recuperadas sem badge de citação; nunca converte `DemoSource` em `ChatSource`.
- `DemoChatScreen` recebe `state: DemoRunState`, `onChange`, `onSubmit`, `onRetry` e `onViewPipeline`. O botão de envio só fica habilitado para pergunta com pelo menos dois caracteres e estado que não seja loading.

- [ ] **Step 1: Write the failing tests.** Cubra no teste de telas: exemplo preenche input sem callback de submit; pergunta válida chama `onSubmit` somente no botão; loading mostra `Executando o RagTest...` e não etapas falsas; sucesso mostra pergunta, Markdown, model/timings, fontes, páginas, excerpts permitidos, scores disponíveis e `Não disponível` para null; `grounded=true` mostra `Citações verificadas` e somente fontes citadas; `grounded=false` mostra `Citações não verificadas` ou `Sem base documental suficiente`; botão `Ver como essa resposta foi construída` fica habilitado somente em sucesso e chama navegação sem rede; erro mostra mensagem sanitizada e `Tentar novamente`; string de segredo/path no erro não aparece.
- [ ] **Step 2: Run focused tests to verify RED.** Executar `cd frontend; npm test -- --runTestsByPath src/demo/screens/demo-screens.test.tsx`; esperar falhas porque a tela M2 ainda não aceita `DemoRunState` nem renderiza resposta live.
- [ ] **Step 3: Write the minimal implementation.** Extrair a apresentação genérica sem alterar o contrato normal, preservar o comportamento validado de Markdown/grounding e criar `DemoAnswer` com adapter específico. No Chat, exibir fonte `document`/`page`/`excerpt` e apenas scores não nulos; nunca substituir score null por zero. Mapear `DemoApiError.code` para textos estáveis de indisponibilidade, pergunta inválida, demo desabilitada ou falha genérica. O submit será callback do `DemoApp`; a tela não importará `fetch`, `sendChat` ou provider.
- [ ] **Step 4: Run focused tests to verify GREEN.** Executar teste focado, `cd frontend; npm test -- --runTestsByPath src/components/assistant-answer.test.tsx src/demo/screens/demo-screens.test.tsx` e `npm run typecheck`. Confirmar que a suíte normal continua usando seu adapter sem alteração de comportamento.
- [ ] **Step 5: Commit.** Fazer commit local `feat: connect demo chat to sanitized live run`.

## Task 4: Ligar `DemoApp`, runtime e navegação sem reexecução

**Files:**
- Modify: `frontend/App.tsx`
- Modify: `frontend/src/__tests__/app.test.tsx`
- Modify: `frontend/src/demo/components/demo-shell.tsx`
- Modify: `frontend/src/demo/components/demo-tabs.tsx` only if a11y/state wiring requires it

**Interfaces:**

- `DemoApp` cria um `DemoApi` estável com `useMemo`; a construção só valida/configura o cliente e nunca chama método de rede. Um `demoApi` injetado continua disponível para testes.
- `DemoApp` usa diretamente `useReducer(demoRunReducer, initialDemoRunState)` para runtime e execução, chama `getRuntime` uma vez em `useEffect`, mantém `activeTab`, `pipelineMode` e `presentationIndex`, e passa callbacks puros para Chat/Como funciona.
- `NormalApp` mantém `apiBaseUrl?: string`, `sendChat?: SendChat`, hooks, retry, grounding e fontes atuais. `App` chama `isDemoEnabled()` em cada render e não compartilha hooks condicionais entre árvores.

- [ ] **Step 1: Write the failing tests.** Em `app.test.tsx`, cubra flag ausente/falsy e `true` após mutação de `process.env`; app normal continua chamando apenas `sendChat`; demo nunca chama `sendChat`; construção/render não chama `run` nem `retrieve`; mount chama `getRuntime` uma vez; submit válido chama `run` uma vez; retry chama segunda vez somente ao clique; exemplo não chama; troca por todas as tabs não chama; clicar no botão de pipeline muda para `how-it-works` preservando a resposta e sem request; voltar ao Chat preserva a execução.
- [ ] **Step 2: Run the focused test to verify RED.** Executar `cd frontend; npm test -- --runTestsByPath src/__tests__/app.test.tsx`; esperar falhas porque `DemoApp` ainda monta somente estados M2 e não injeta o estado live.
- [ ] **Step 3: Write the minimal implementation.** Criar cliente com dependências estáveis e `getAllowedHttpsOrigins(process.env.EXPO_PUBLIC_RAG_ALLOWED_HTTPS_ORIGINS)`; uma origem HTTPS só é aceita quando aparece nessa lista pública exata, sem fallback implícito para HTTPS público. Capturar erro de base URL em estado de configuração sem renderizar corpo de exceção e fazer `getRuntime` em `useEffect` controlado, despachando eventos no reducer único. `handleSubmit` chama somente o callback de run; `handleRetry` chama somente retry; `handleViewPipeline` muda aba/modo/índice. A troca de aba apenas seleciona tela; nenhum efeito depende de `activeTab` para buscar dados.
- [ ] **Step 4: Run focused tests to verify GREEN.** Executar teste focado, toda a suíte `cd frontend; npm test` e `npm run typecheck`. Confirmar que a matriz da flag continua funcionando depois do módulo já importado.
- [ ] **Step 5: Commit.** Fazer commit local `feat: wire demo app live state and runtime`.

## Task 5: Expor pipeline real e modos automático/apresentação

**Files:**
- Create: `frontend/src/demo/state/demo-pipeline-model.ts`
- Create: `frontend/src/demo/state/demo-pipeline-model.test.ts`
- Modify: `frontend/src/demo/components/pipeline-stage.tsx`
- Modify: `frontend/src/demo/screens/how-it-works-screen.tsx`
- Create: `frontend/src/demo/screens/how-it-works-screen.test.tsx`

**Interfaces:**

- `DemoPipelineStageState = "available" | "not-required" | "unavailable" | "not-measured"`.
- `DemoPipelineStageView` contém `id`, `title`, `simpleExplanation`, `technicalDetails`, `state`, `value?: string`, `source?: string`; `buildDemoPipeline(state: DemoRunState): DemoPipelineStageView[]` sempre retorna as 11 etapas na ordem Pergunta, Análise/decomposição, Embedding, Qdrant, Retrieval, Reranking, Contexto, LLM, Citações, Grounding, Resposta.
- Antes de uma execução, `HowItWorksScreen` mostra `Execute uma pergunta no Chat para visualizar o pipeline` e não cria resposta/score/fonte/timing fake. Após sucesso, todos os modos consomem o mesmo `DemoRunState` e nenhum recebe `DemoApi`.

- [ ] **Step 1: Write the failing tests.** No modelo, teste uma execução `TEST DATA` com runtime e sources: Pergunta disponível; Análise com o texto exato `O endpoint demo M1 está configurado para executar single-query nesta versão` e `source: "configuração estática da rota M1"`, sem tratar isso como campo do response; Embedding com modelo quando fornecido e dimensão `Não disponível`; Qdrant com collection real; Retrieval com ordem/documento/página/scores nullable; Reranking com pré/pós `Não disponível`; Contexto `Não disponível nesta versão da demo`; LLM com provider/model/timing real; Citações com `citation_ids` sem retry count; Grounding com texto estrutural; Resposta com answer. Teste também sources vazias, runtime null e erro.
- [ ] **Step 2: Run the focused tests to verify RED.** Executar `cd frontend; npm test -- --runTestsByPath src/demo/state/demo-pipeline-model.test.ts src/demo/screens/how-it-works-screen.test.tsx`; esperar falhas por modelo/props M3 ausentes.
- [ ] **Step 3: Write the minimal implementation.** Derivar cada detalhe somente do DTO M1 e runtime validado. Marcar `multi-query`, decomposition, ranking pré/pós, contexto final, retry count e dimensão como indisponíveis; não chamar fonte recuperada de contexto enviado ao LLM. No modo automático renderizar todas as etapas; no modo apresentação renderizar somente o índice atual, habilitar `Anterior`/`Próximo` nos limites e `Ver tudo` para voltar ao conjunto completo. O clique de Chat define tab `how-it-works`, modo apresentação e índice zero sem alterar estado da execução.
- [ ] **Step 4: Run focused tests to verify GREEN.** Executar testes focados, `cd frontend; npm run typecheck` e confirmar por spy que `Próximo`, `Anterior`, `Ver tudo` e troca de aba não chamam `getRuntime`, `run` ou `retrieve`.
- [ ] **Step 5: Commit.** Fazer commit local `feat: present live demo pipeline diagnostics`.

## Task 6: QA e revisão de segurança sem mutações

**Files:** nenhuma alteração de produção, teste ou documentação por QA/security reviewer.

- [ ] **Step 1: QA automático.** Executar `cd frontend; npm test`, `npm run typecheck` e na raiz `git diff --check`. Inspecionar o diff para confirmar ausência de backend, `.env`, corpus, Qdrant, Docker, provider, fixtures de replay e dependências novas.
- [ ] **Step 2: QA de estados.** Verificar loading honesto, sucesso com grounding true/false, sources vazias, scores null, runtime error, run error, retry manual, pergunta inválida, demo backend desabilitada e preservação do resultado ao trocar de aba. Usar somente fetch mocks; não iniciar provider externo.
- [ ] **Step 3: QA de requests.** Espionar fetch e demonstrar: zero request na construção; exatamente um GET de runtime por montagem; um POST apenas após submit; segundo POST somente após retry manual; zero request em exemplo, tabs, botão de pipeline, apresentação e controles do Laboratório.
- [ ] **Step 4: Revisão de privacidade.** Procurar em estado, textos, exceções e logs por corpo bruto, `detail`, traceback, token, senha, path absoluto, URL interna, `.env`, `CHATSCM` e metadata arbitrária. Confirmar que adapters exibem apenas `public_id`, documento, página, ordem, excerpt e scores autorizados.
- [ ] **Step 5: Gate de contrato.** Conferir `app/schemas/demo.py` e `app/api/routes/demo.py` somente como leitura: `auto_decompose=False`, DTO fechado e `GET /runtime` sem dimensão/perfil adicionais. Se houver mismatch, bloquear e reportar; não alterar backend para satisfazer a UI.

## Task 7: Validação runtime condicionada e documentação após QA

**Files:**
- Modify: `docs/demo-m1.md`
- Modify: `docs/CONTEXTO_CONTINUIDADE.md`

- [ ] **Step 1: Executar validação local segura.** Sem ler/imprimir `.env` ou credenciais, configurar somente variáveis públicas em sessão temporária: `cd frontend; $env:EXPO_PUBLIC_RAG_DEMO_ENABLED="true"; $env:EXPO_PUBLIC_RAG_API_BASE_URL="http://127.0.0.1:8000"; npm run web`. O backend deve estar previamente iniciado pelo procedimento controlado do projeto com `DEMO_ENABLED=true` e allowlist pública aprovada; não usar `CORS_ALLOWED_ORIGINS=*`.
- [ ] **Step 2: Validar runtime sem provider.** Se o backend controlado estiver disponível, observar um único `GET /v1/demo/runtime` e confirmar apenas versão/provider/model/embedding/retrieval/collection/policy sanitizados. Não exigir dimensão ou perfil; mostrar `Não disponível` quando não existir.
- [ ] **Step 3: Condicionar POST real.** Só executar `POST /v1/demo/run` com pergunta pública aprovada se o usuário fornecer/autorizar o ambiente seguro e houver provider já configurado sem conteúdo privado. Se isso não estiver disponível, não chamar provider: registrar a sequência exata para execução manual e marcar runtime live como `aguardando validação`.
- [ ] **Step 4: Validar visualmente M3.** Repetir `1366x768`, `1024x600`, `390x844` e `360x800`, verificando resposta Markdown, citações/fontes, scores, grounding, pipeline, modos de apresentação, botões, overflow e legibilidade. Se IAB não controlar dimensão, documentar cada tamanho como `aguardando validação manual`.
- [ ] **Step 5: Documentar evidências após QA.** Atualizar `docs/demo-m1.md` separando M1 verificado, M2 verificado/aguardando visual e M3 implementado/verificado/aguardando runtime conforme saídas reais. Registrar flags independentes, allowlist de base URL, sequência local, endpoints usados, loading honesto, single-query, campos indisponíveis, grounding estrutural, ausência de CORS wildcard, erro sanitizado, diferença live versus futuro replay e fronteira M4.
- [ ] **Step 6: Atualizar continuidade.** Adicionar seção datada em `docs/CONTEXTO_CONTINUIDADE.md` com branch, HEAD, commits, arquivos, testes RED/GREEN, Jest, TypeScript, backend/Ruff aplicável, runtime/visual gates, findings QA/reviewer/security, pendências e `git status`. Preservar o handoff M1/M2 histórico e não registrar sucesso sem comando/teste correspondente.
- [ ] **Step 7: Commit documental.** Após aprovação de QA e security reviewer, fazer commit local `docs: record RagTest demo M3 handoff`. Não fazer push, PR, merge ou alteração de main.

## Required Multi-Agent Gates

1. `REVIEWER`: revisar este plano e o desenho de integração antes do developer; bloquear se houver extensão de DTO, chamada automática, exposição de raw body, CORS wildcard, M4 ou replay.
2. `DEVELOPER`: executar Tasks 1–5 com TDD, commits locais pequenos e sem tocar backend/corpus/providers/Qdrant/Docker/.env.
3. `QA`: executar Task 6 sem editar produção, testes ou docs; falhas retornam ao developer para correção e revalidação.
4. `SECURITY_PRIVACY_REVIEWER`: revisar Task 6 com foco em allowlist, CORS, errors, runtime, excerpts, logs, DevTools razoável e estado compartilhado; não alterar código.
5. `REVIEWER`: revisar novamente o diff e as evidências após QA/security; nenhum status de verificado sem saída correspondente.
6. `DOCUMENTER`: somente após os gates, executar Task 7 e registrar limitações/pendências sem converter M3/M4/M6 em implementados.
7. `ORCHESTRATOR`: executar validação final, confirmar `git status --short --branch` e parar. Não implementar M4 sem nova autorização.

## Final Handoff Checklist

- [ ] branch, HEAD e commits locais informados; workspace limpo ou alterações explicitamente listadas;
- [ ] arquivos criados/modificados listados, sem backend/Qdrant/corpus/provider/.env/configuração de agentes;
- [ ] fluxo Chat live, estado compartilhado e endpoints descritos;
- [ ] runtime sanitizado e execução real distinguida de validação mockada;
- [ ] dados reais exibidos e dados indisponíveis explicitamente enumerados;
- [ ] single-query, ausência de multi-query/decomposition, scores nullable, contexto e grounding explicados;
- [ ] modo automático/apresentação, loading, erros, retry manual e ausência de request na navegação demonstrados;
- [ ] RED/GREEN, Jest, TypeScript, backend/Ruff somente se aplicável e `git diff --check` registrados;
- [ ] findings QA, reviewer e security/privacy registrados;
- [ ] quatro viewports marcados como verificados somente com observação direta, ou como aguardando validação manual;
- [ ] proposta M4 limitada ao Laboratório experimental e sem replay completo;
- [ ] nenhum push, PR, merge, alteração de main ou implementação M4 executado.
