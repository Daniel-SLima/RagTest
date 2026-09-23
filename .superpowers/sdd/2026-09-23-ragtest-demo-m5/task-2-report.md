# Task 2 — relatório auditável

## Objetivo

Transformar a aba `O que ainda falta` em uma visão rastreável do produto, consumindo o catálogo
M5 puro e versionado, sem requests ou alterações no backend.

## Contexto consultado

- `AGENTS.md` e a ordem de continuidade definida no contrato do projeto;
- `docs/CONTEXTO_CONTINUIDADE.md`, `docs/decisoes-tecnicas.md`, `docs/dificuldades-tcc.md`;
- `.superpowers/sdd/2026-09-23-ragtest-demo-m5/task-2-brief.md`;
- `docs/superpowers/plans/2026-09-23-ragtest-demo-m5.md`;
- catálogo implementado em `frontend/src/demo/types/roadmap.ts` e `frontend/src/demo/data/roadmap.ts`;
- DemoShell, navegação e testes frontend existentes.

## Evidências e decisões

- O RED inicial falhou porque a tela ainda renderizava apenas o stub M2, sem snapshot, filtros ou
  interação: `roadmap-screen.test.tsx` falhou em 9 testes por elementos/roles ausentes.
- A tela usa `ROADMAP_SNAPSHOT`, `ROADMAP_ITEMS`, `ROADMAP_AREAS`, `ROADMAP_STATUSES`,
  `filterRoadmapItems` e `getRoadmapCounts`; não chama API, provider ou endpoint.
- Status e áreas recebem controles acessíveis; status usa rótulos `Status: ...` e área usa
  `Área: ...` para distinguir filtros de badges e títulos.
- Cada item é um accordion `Pressable` com `accessibilityState.expanded`; detalhes técnicos,
  importância, limitações, dependências, evidências e origem só aparecem ao expandir. “Por que
  ainda falta?” só é renderizado quando `whyMissing` existe.
- A arquitetura atual e a visão planejada são blocos separados; o layout usa reflow/flex-wrap para
  os viewports definidos pelo M5.

## Arquivos alterados

- `frontend/src/demo/screens/roadmap-screen.tsx`
- `frontend/src/demo/components/roadmap-item.tsx`
- `frontend/src/demo/screens/roadmap-screen.test.tsx`
- este relatório.

Nenhum arquivo de backend, replay, catálogo, corpus, Qdrant, provider ou frontend fora da Task 2
foi alterado.

## Comportamento implementado

- visão `VISÃO GERAL` com badge de fotografia e branch, commit-base, versão e data;
- separação explícita de `Arquitetura atual` e `Visão planejada`;
- cards por área com contagens calculadas do catálogo;
- filtros `Todos`, quatro status oficiais e todas as áreas do catálogo;
- mensagem de resultado vazio sem conteúdo fabricado;
- accordion acessível com explicação simples, detalhes técnicos, dependências e referências
  relativas de evidência/origem;
- ausência de porcentagens, paths pessoais, secrets, `.env`, `CHATSCM` e claims de replay no
  conteúdo renderizado.

## Testes executados

- `npm test -- --runInBand src/demo/screens/roadmap-screen.test.tsx` — **9 testes passaram**;
- `npm run typecheck` — **passou**;
- `npm test -- --runInBand src/demo/screens/roadmap-screen.test.tsx src/demo/screens/demo-screens.test.tsx src/__tests__/app.test.tsx` — 36 passaram e 2 falharam em `demo-screens.test.tsx`;
- `npm test -- --runInBand` — 12 suites/112 testes passaram; 2 testes falharam no mesmo arquivo
  obsoleto M2.
- `git diff --check` — passou (somente avisos normais de conversão LF/CRLF do Git).

## Problemas, riscos e pendências

`frontend/src/demo/screens/demo-screens.test.tsx` ainda contém duas expectativas incompatíveis
com o catálogo M5: restringe `snapshotVersion` a M1/M2 embora o catálogo tenha evidências M4, e
usa `getByText("Planejado")` apesar de a nova tela exibir o status no filtro e nos badges. O
arquivo ficou fora da lista exclusiva de arquivos da Task 2 e não foi alterado. A suíte completa
não pode ser declarada verde até o ORCHESTRATOR decidir a atualização desse teste obsoleto.

Validação visual manual dos quatro viewports e tema claro/escuro continua pendente para a Task 3;
os gates automatizados não substituem essa observação.

## Próxima etapa recomendada

ORCHESTRATOR/QA deve atualizar ou autorizar a atualização do teste M2 obsoleto, repetir a suíte e
executar a validação visual dos viewports `1366x768`, `1024x600`, `390x844` e `360x800` sem
backend/provider.
