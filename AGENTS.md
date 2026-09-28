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

Módulo RAG para o app **Se Cuida Mulher**: letramento em saúde da mulher e orientação de
agendamento (preventivo, mamografia, pré-natal, urgência). Toda tarefa deve aproximar o projeto
dos objetivos da proposta do orientador (ver plano). **Não abra novas frentes de hardening,
providers ou modos de retrieval** sem que o `ESTADO_ATUAL.md` peça.

## Fluxo de trabalho

- Mudança de contrato da API, segurança ou guardrail: especificar → TDD → revisão → documentar.
- Demais mudanças: TDD (RED → GREEN), suíte completa, lint, commit pequeno.
- Uma versão por fase do plano (0.8 domínio, 0.9 segurança + ações, 0.10 interface, 1.0 integração).
- **Ao terminar cada tarefa (ou antes de encerrar a sessão), atualize `docs/ESTADO_ATUAL.md`**:
  o que foi feito, evidência (saída de teste/comando), e a próxima tarefa exata.

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
