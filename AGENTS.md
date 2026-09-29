# Contrato de trabalho dos agentes — RagTest

Vale para qualquer agente de IA (Claude Code, Codex, Cowork etc.).

## Antes de qualquer coisa, leia nesta ordem

1. `docs/ESTADO_ATUAL.md` — **onde o trabalho parou e qual é a próxima tarefa** (fonte autoritativa);
2. `docs/PLANO_FINALIZACAO_TCC.md` — plano por fases e o porquê da reorientação;
3. `docs/decisoes-tecnicas.md` e `docs/dificuldades-tcc.md` — só as entradas ligadas à tarefa;
4. o código e os testes da área que vai mexer.

`docs/historico/` guarda o contexto antigo (até a 0.7.0). Consulte apenas se precisar de um
detalhe histórico; não atualize esses arquivos.

## Foco do projeto

**Backend headless:** o produto é a API. O frontend Expo é cliente de referência congelado; não
adicione features nele. Regra de negócio e textos de exibição ficam no backend.

Módulo RAG para o app **Se Cuida Mulher**: letramento em saúde da mulher e orientação de
agendamento (preventivo, mamografia, pré-natal, urgência). Toda tarefa deve aproximar o projeto
dos objetivos da proposta do orientador (ver plano). **Não abra novas frentes de hardening,
providers ou modos de retrieval** sem que o `ESTADO_ATUAL.md` peça.

## Fluxo de trabalho

- Mudança de contrato da API, segurança ou guardrail: especificar → TDD → revisão → documentar.
- Demais mudanças: TDD (RED → GREEN), suíte completa, lint, commit pequeno.
- Uma versão por fase do plano (0.8 domínio, 0.9 segurança + ações, 0.10 interface, 1.0 integração).
- **Regra obrigatória: ao terminar cada etapa, atualize `docs/ESTADO_ATUAL.md` e o status em
  `docs/PLANO_FINALIZACAO_TCC.md`** (o que foi feito, evidência de teste/comando, próxima tarefa exata).
  Não acumule várias etapas sem atualizar.

## Divisão de trabalho (autor × agente)

- O agente trabalha na pasta local, numa branch por etapa (`feature/<tema>-<versão>`), com TDD,
  commits pequenos e documentação atualizada a cada etapa.
- O autor faz o que exige credenciais ou a máquina dele: `git push`, abrir e mesclar PRs no GitHub,
  rodar Docker, avaliações com os modelos reais e chamadas ao provider de LLM.
- O agente escreve em `docs/ESTADO_ATUAL.md` (seção 3) os comandos exatos que o autor precisa rodar;
  as saídas voltam para `docs/resultados/`, onde o agente as lê.
- Fluxo de branch: 1 PR por branch → CI verde (lint, test, e2e-qdrant, frontend) → merge no `main`
  → nova branch a partir do `main` atualizado.

## Git

- Comece por `git status --short --branch` e `git log --oneline -5`.
- Preserve alterações locais e arquivos não rastreados.
- Proibido sem autorização explícita: `reset --hard`, `clean`, `restore` destrutivo, rebase,
  force-push, apagar branch, push, merge.
- Fins de linha são normalizados por `.gitattributes` (LF).
- Commits terminam com as linhas de atribuição do agente, quando houver.

## Testes

- Backend: Python 3.12, `pytest` e `ruff check .` (Ruff 0.16.8).
- Se a pasta `.pytest_cache` estiver bloqueada: `pytest tests -p no:cacheprovider --ignore=.pytest_cache`.
- Frontend: `cd frontend && npm test && npm run typecheck`.
- Docker: `docker compose config`; não recrie volumes.

## Privacidade e segurança

- Nunca leia, imprima, versione ou envie valores de `.env`/API keys.
- `data/source/chatscm/*.docx`: liberado para desenvolvimento e avaliação (D038 aprovada em
  2026-09-28; auditoria automática com 0 achados). Não usar dados reais de usuárias.
- Corpus: o autor definiu que **os documentos de `data/source` são a base documental suficiente**.
  Não adicione fontes externas sem pedido explícito.
- Logs não registram perguntas, respostas, prompts, trechos ou credenciais.
- `grounded=true` é cobertura estrutural de citações, não prova de verdade clínica.
- O backend continua independente do Expo e do Se Cuida Mulher: ações (links, lembretes) são
  sugeridas pela API e executadas pelo cliente integrador.

## Qdrant e ingestão

- Não execute `ragtest-ingest --recreate` nem `docker compose down -v`.
- Para incluir fontes novas: `ragtest-plan-ingestion-sync` → `ragtest-sync-ingestion`.
- Não altere parâmetros de retrieval/embeddings sem uma entrada nova em `decisoes-tecnicas.md`.

## Documentação

- Estado e próximos passos: `docs/ESTADO_ATUAL.md` (curto; no máximo ~200 linhas).
- Decisões: `docs/decisoes-tecnicas.md` (D0xx). Falhas reproduzíveis: `docs/dificuldades-tcc.md`.
- Uso público: `README.md`.
- Diferencie planejado, implementado, aguardando validação e verificado. Não declare sucesso sem
  a saída do comando ou teste correspondente.
