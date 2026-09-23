# RagTest Demo M5 — Visão rastreável do produto Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar a aba `O que ainda falta` em uma visão didática, versionada e baseada em evidências sobre o RagTest atual, as evoluções justificadas e a futura integração ao Se Cuida Mulher.

**Architecture:** Substituir o catálogo mínimo M2 por dados TypeScript congelados em snapshot, sem parsing de Markdown em runtime. A tela calcula contagens a partir do catálogo, permite filtrar por status/área e abre detalhes acessíveis com explicação simples, detalhes técnicos, dependências, origem, evidências e limitações. O backend, o contrato de chat, o retrieval, o corpus, o Qdrant e o replay permanecem intocados.

**Tech Stack:** Expo/React Native 0.86, React 19, TypeScript 5.9, Jest/RNTL e tokens do tema da DemoShell.

**Spec:** Especificação M5 fornecida pelo usuário em 2026-09-23: `O que ainda falta / visão do produto completo`.

## Global Constraints

- Trabalhar exclusivamente na branch `sidequest/ragtest-demo`, iniciando no HEAD `75c924c` e mantendo workspace local, sem push, PR, merge, alteração de `main`, `feature/audit-0.7.0` ou configuração multiagente.
- Usar somente os status oficiais `Implementado`, `Parcial / em desenvolvimento`, `Planejado` e `Em estudo`, com critérios explícitos e evidência por item.
- Não inventar roadmap: itens sem evidência devem ser removidos; `Em estudo` exige evidência de discussão/avaliação; replay não será implementado nem apresentado como evolução M5.
- O item M2 obsoleto `m3-replay` foi removido porque M5 não possui requisito de replay aprovado; replay permanece fora do escopo.
- Não fazer parsing dinâmico de Markdown em runtime; o catálogo deve ser TypeScript versionado e revisado.
- Não usar porcentagens de progresso; contagens de cards são calculadas a partir do catálogo.
- Snapshot deve usar branch, commit-base, versão do snapshot e data versionada, sem expor paths pessoais, secrets, `.env`, URLs privadas, logs crus, `CHATSCM` ou dados pessoais.
- M5 deve ser essencialmente frontend, dados versionados, testes e documentação; não alterar backend, retrieval, chat, providers, corpus, embeddings, collection Qdrant ou ingestão.
- Separar arquitetura atual de visão planejada; não presumir autenticação, integração oficial, política clínica, LGPD completa, telemetria, agenda ou notificações já existentes.
- Manter o bloqueio externo/produção visível: autenticação, rate limiting, auditoria final, logs preexistentes e prompt injection continuam limites documentados.
- Preservar responsividade e acessibilidade básicas da DemoShell nos viewports `1366x768`, `1024x600`, `390x844` e `360x800`; tema claro e DevTools continuam limitações observacionais permitidas.

## Review Focus

- Item sem evidência ou replay residual deve ser excluído/reclassificado, não convertido em plano por inferência — teste de catálogo filtrando somente itens com `evidence` não vazia e ausência de `replay`.
- Contagens de área/status devem derivar do catálogo e permanecer consistentes após filtro — teste de agregação e seleção.
- Detalhes de item devem manter explicação simples, técnica, dependências, origem e “por que ainda falta?” quando aplicável — teste de expansão acessível.
- Snapshot e evidências não podem vazar paths absolutos, secrets, `.env`, URLs privadas ou conteúdo sensível — teste de sanitização dos dados versionados/renderizados.
- Arquitetura atual, visão planejada e limitações de saúde/privacidade devem permanecer separadas e sem claims de prontidão — teste de textos estruturais e ausência de percentuais.

---

### Task 1: Catálogo M5 e agregações puras

**Files:**
- Modify: `frontend/src/demo/types/roadmap.ts`
- Modify: `frontend/src/demo/data/roadmap.ts` (substitui o catálogo mínimo M2)
- Create: `frontend/src/demo/data/roadmap.test.ts`

**Interfaces:**
- Consumes: evidências em `docs/CONTEXTO_CONTINUIDADE.md`, `docs/decisoes-tecnicas.md`, `docs/demo-m1.md`, `README.md`, especificação de sessões, código/testes atuais e planos versionados.
- Produces: `ROADMAP_SNAPSHOT`, `ROADMAP_ITEMS`, `ROADMAP_AREAS`, `ROADMAP_STATUSES`, `getRoadmapCounts`, `filterRoadmapItems` e tipos fechados para a tela.

- [ ] **Step 1: Especificar testes RED para catálogo e contagens**

  Cobrir snapshot com `branch`, `commit`, `version` e `date`; lista somente com os quatro status; contagem calculada por área/status; filtro por `all`, status e área; dependências por IDs; evidência não vazia; ausência de `replay`, secrets, `.env`, paths absolutos e URLs privadas; e presença de itens implementados, parciais, planejados e em estudo sustentados pelas fontes.

- [ ] **Step 2: Executar testes RED**

  Rodar `npm test -- --runInBand frontend/src/demo/data/roadmap.test.ts`; esperar falha porque o catálogo M2 não possui os campos/agregações M5.

- [ ] **Step 3: Modelar dados versionados e inventário evidence-based**

  Expandir `RoadmapItem` com `id`, `area`, `title`, `status`, `simpleExplanation`, `technicalExplanation`, `whyItMatters`, `whyMissing`, `dependencies`, `evidence`, `origin`, `snapshotVersion`, `snapshotCommit` e `notes`. Usar somente itens com evidência real, incluindo o núcleo RAG/API, retrieval e avaliação, grounding estrutural, chat demonstrativo, laboratório M4, sessões backend sem integração Expo, base documental/sincronização, segurança/produção, privacidade/LGPD, avaliação especializada/usabilidade e integração futura ao Se Cuida Mulher quando documentados. Excluir o antigo item `m3-replay`; registrar em documentação que foi removido por contradizer o limite explícito do M5.

  Fixar o snapshot M5 no estado de entrada (`branch: sidequest/ragtest-demo`, `commit: 75c924c`, `version: M5`, `date: 2026-09-23`) e manter referências relativas ao repositório. Status `implemented` exige código/teste/evidência; `partial` exige parte implementada e lacuna explícita; `planned` exige decisão/documentação futura; `research` exige discussão/avaliação sem decisão.

- [ ] **Step 4: Implementar agregações e filtros puros**

  `getRoadmapCounts(items)` deve retornar contagens por status e área a partir da lista recebida. `filterRoadmapItems(items, { status, area })` deve aceitar `all` e retornar nova lista sem mutar o catálogo. Dependências devem referenciar somente IDs existentes; a validação de catálogo deve falhar em desenvolvimento/testes para referências órfãs.

- [ ] **Step 5: Executar GREEN e lint direcionado**

  Rodar `npm test -- --runInBand frontend/src/demo/data/roadmap.test.ts` e `npm run typecheck`; ambos devem passar antes de integrar a tela.

- [ ] **Step 6: Commit local**

  `git add frontend/src/demo/types/roadmap.ts frontend/src/demo/data/roadmap.ts frontend/src/demo/data/roadmap.test.ts && git commit -m "feat: version M5 roadmap evidence catalog"`

### Task 2: Tela didática com filtros, snapshot e detalhes

**Files:**
- Modify: `frontend/src/demo/screens/roadmap-screen.tsx`
- Modify: `frontend/src/demo/components/roadmap-item.tsx`
- Create: `frontend/src/demo/screens/roadmap-screen.test.tsx`
- Modify: `frontend/src/__tests__/app.test.tsx` only when existing navigation assertions need the new accessible labels.

**Interfaces:**
- Consumes: `ROADMAP_SNAPSHOT`, `ROADMAP_ITEMS`, `ROADMAP_AREAS`, `ROADMAP_STATUSES`, `getRoadmapCounts`, `filterRoadmapItems`, `RoadmapItem` and `useDemoTheme`.
- Produces: overview current/planned, snapshot metadata, area cards with calculated counts, status/area filters, expandable item details, dependency chain, evidence/origin labels and accessible responsive UI.

- [ ] **Step 1: Especificar testes RED de interação e acessibilidade**

  Testar render inicial com visão atual/planejada e snapshot; cards de áreas e contagens derivadas; filtros `Todos`, cada status e área; abertura/fechamento por botão acessível; detalhes simples/técnicos, “Por que ainda falta?” condicional, dependências e evidências; nenhum percentual; nenhum path pessoal/secret; responsividade estrutural e quatro status.

- [ ] **Step 2: Executar testes RED**

  Rodar `npm test -- --runInBand frontend/src/demo/screens/roadmap-screen.test.tsx`; esperar falha porque a tela atual só lista três cards sem interação.

- [ ] **Step 3: Implementar visão geral e snapshot**

  Mostrar título, narrativa curta, badge `Fotografia do projeto`, `RagTest`, branch, commit-base, versão e data. Separar blocos `Arquitetura atual` (Demo/Expo → FastAPI → RAG/retrieval/grounding → Qdrant + provider) e `Visão planejada` (integração Se Cuida Mulher somente como alvo documentado), com rótulos explícitos e sem prometer módulos não evidenciados.

- [ ] **Step 4: Implementar cards e filtros calculados**

  Renderizar uma card por área presente no catálogo, cada qual com `getRoadmapCounts` e botão `Ver detalhes`. Filtros usam `filterRoadmapItems`, incluem `Todos`, os quatro status e áreas presentes, preservam seleção acessível e não fazem requests. O resultado vazio deve informar que não há itens para o filtro, sem fabricar conteúdo.

- [ ] **Step 5: Implementar detalhes e dependências**

  `RoadmapItem` deve ser um accordion acessível: botão com `accessibilityState.expanded`, resumo, status, explicação simples, seção técnica, por que importa, `Por que ainda falta?` apenas quando `whyMissing` existe, limitações, dependências e evidências/origem em paths relativos. Não renderizar o item como parede de texto nem como tabela gigante.

- [ ] **Step 6: Executar GREEN e gates frontend**

  Rodar `npm test -- --runInBand frontend/src/demo/screens/roadmap-screen.test.tsx frontend/src/__tests__/app.test.tsx`, depois `npm test -- --runInBand` e `npm run typecheck`.

- [ ] **Step 7: Commit local**

  `git add frontend/src/demo/screens/roadmap-screen.tsx frontend/src/demo/components/roadmap-item.tsx frontend/src/demo/screens/roadmap-screen.test.tsx frontend/src/__tests__/app.test.tsx && git commit -m "feat: build evidence-based roadmap view"`

### Task 3: Documentação, validação visual e fechamento M5

**Files:**
- Modify: `docs/demo-m1.md`
- Modify: `docs/CONTEXTO_CONTINUIDADE.md`
- Modify: `README.md` only if a public limitation or snapshot note is missing there; do not rewrite historical version headings.

**Interfaces:**
- Consumes: catalog code, UI tests, reviewer/QA/security reports and runtime-free visual validation.
- Produces: traceable M5 handoff distinguishing implemented, partial, planned and research, removed replay item, snapshot source, counts, visual gates and limits.

- [ ] **Step 1: Atualizar documentação sem claims novos**

  Registrar arquivos, snapshot-base, total e contagens do catálogo, áreas usadas, item replay removido, evidências por fonte, visão atual/planned, saúde, privacidade/LGPD, segurança, avaliação, dependências, filtros, acessibilidade, limitações do tema claro/DevTools e proposta M6 apenas como fronteira futura sem implementação.

- [ ] **Step 2: Validar visualmente os quatro viewports**

  Iniciar Expo Web sem backend e inspecionar `1366x768`, `1024x600`, `390x844`, `360x800`: cards, badges, filtros, accordions, dependências, origem/evidência, textos e ausência de overflow horizontal. Não iniciar Qdrant nem provider.

- [ ] **Step 3: Executar gates finais**

  Rodar `npm test -- --runInBand`, `npm run typecheck` e `git diff --check`. Ruff/backend somente se arquivos backend forem tocados; M5 não deve tocá-los.

- [ ] **Step 4: Commit local documental**

  `git add docs/demo-m1.md docs/CONTEXTO_CONTINUIDADE.md README.md && git commit -m "docs: record M5 roadmap validation"` (incluir somente arquivos realmente alterados).

## Self-review coverage

- O catálogo cobre os quatro status sem usar porcentagens e cada item exige evidência; replay foi explicitamente removido.
- A tela separa arquitetura atual e visão planejada, sem afirmar autenticação, LGPD, saúde clínica, Se Cuida Mulher completo, auditoria ou produção como implementados.
- Sessões, multi-query, grounding, retrieval, corpus e avaliação aparecem somente com a semântica sustentada pelo código/documentação atual.
- Filtros, contagens, detalhes, dependências, snapshot, responsividade e acessibilidade têm testes dedicados.
- Nenhum task altera backend, Qdrant, corpus, embeddings, providers ou replay; M6 fica somente como proposta documental.
