# Estado atual — handoff entre agentes

> Documento **autoritativo e curto**. Todo agente lê este arquivo primeiro e o atualiza ao terminar.
> **Roteiro passo a passo até a v1.0.0: `docs/ROTEIRO_EXECUCAO.md`** (seguir a próxima micro-etapa não marcada).
> Plano completo: `docs/PLANO_FINALIZACAO_TCC.md`. Histórico até a 0.7.0: `docs/historico/`.

Última atualização: **2026-09-28** — Claude (Cowork), sessão de reorientação para o domínio.

---

## 0. Decisões do autor que valem para todo o projeto

| Data | Decisão |
|---|---|
| 28/09 | Não refazer o projeto; reorientar para o domínio do orientador (`PLANO_FINALIZACAO_TCC.md`). |
| 28/09 | Corpus = apenas os documentos de `data/source`; sem fontes externas sem pedido explícito. |
| 28/09 | CHATSCM liberado para desenvolvimento e avaliação (D038). |
| 28/09 | **Backend headless**: o produto é a API; o Expo é cliente de referência congelado; toda regra e texto de exibição ficam no backend (D042). |
| 28/09 | Stack do orientador mantida (FastAPI, Qdrant, LangChain, React Native via REST, Docker). |
| 28/09 | Documentação atualizada a cada etapa (este arquivo + status no plano). |
| 28/09 | Divisão de trabalho autor × agente e fluxo de branches/PRs: ver `AGENTS.md`. |
| 28/09 | Metodologia: ajustes só com o dev; holdouts são rodados uma vez e nunca usados para ajustar (v2 consumido, v3 independente). |

## 1. Onde estamos

> **Diretriz vigente: backend headless.** O produto é a API; o Expo é cliente de referência congelado.

| Item | Valor |
|---|---|
| Versão | `main` com 0.8.0 + 0.9.0 + 0.9.1 (PRs #22–#24) · trabalho novo em `feature/robustez-0.9.2` |
| Branch de trabalho | `feature/robustez-0.9.2` (a partir do `main`), **não enviada ao GitHub** |
| Testes | backend `339 passed` (inclui 5 ponta a ponta), `ruff` limpo · frontend Jest `19 passed`, `tsc` ok (28/09) |
| Avaliação | hybrid: dev v2 15/15 (MRR 0.833) · **holdout v3 24/25 (MRR 0.801, independente)** · critério PASS |
| Respostas | 11/13 verificadas, 2/2 triagens, 4/4 recusas corretas; 2 fallbacks de agendamento diagnosticados e corrigidos (D054), falta repetir a coleta; rubrica manual pendente |
| Teste real | mamografia agora `grounded=true` (D050/D051) — `docs/resultados/diagnostico_mamografia_2.txt` |
| Qdrant | 773 chunks, sincronizado em 28/09 |

**Escopo do corpus:** só `data/source`. **Stack do orientador:** FastAPI ✅ · Qdrant ✅ · LangChain ✅ (uso seletivo) · React Native via REST ✅ · Docker Compose ✅.

## 2. O que já foi feito (verificado por teste)

1. Git: `.gitattributes` (LF). Docs: `ESTADO_ATUAL`, `AGENTS.md` enxuto, `CLAUDE.md`, README novo
   (antigo em `docs/historico/`), `docs/INTEGRACAO.md`.
2. `ragtest-audit-pii`; **D038 aprovada** (CHATSCM liberado para desenvolvimento/avaliação).
3. Catálogo de serviços `data/source/servicos/catalogo_servicos.json` → 1 documento indexado por
   serviço (`doc_type=servico`, `service_id`), alinhado ao CHATSCM.
4. Dataset v2 em `app/evaluation/datasets/` (15 dev, 25 holdout congelado, 4 fora de escopo);
   `ragtest-evaluate-retrieval --dataset dominio-v2-dev`.
5. **Triagem de urgência** (`app/safety/triage.py`, D039): sinais de alarme em primeira pessoa →
   resposta fixa (maternidade/UPA + 192) sem retrieval/LLM; `safety.triaged`, `safety.rule_id`.
6. **Fora de escopo** (D041): `RETRIEVAL_MIN_SCORE` (desligado até calibrar) +
   `ragtest-calibrate-scope`; resposta fixa orientando a UBS; `safety.out_of_scope`.
7. **Ações estruturadas** (`app/rag/actions.py`, D040): `open_link`, `schedule_reminder`,
   `call_emergency` a partir do serviço **citado**; campo `actions` no `/v1/chat`.
8. **Frontend**: cartão "Sinal de alerta", botões de ação, lembretes em memória ("Meus lembretes"
   com data), aviso para links `seucuida://`, perguntas sugeridas. Compatível com respostas antigas.
9. **Headless (D042)**: `display`, rótulos de fontes, ações com `due_date`/`requires_host_app`/`note`,
   `GET /v1/suggestions`; Expo reduzido a renderizar esses campos.
10. **Contrato congelado (D043)**: snapshot OpenAPI testado, cliente TS gerado, `GET /v1/services[/{id}]`.
11. **Autenticação e limites (D044)**: `X-API-Key` por app integrador, rate limit no chat.
12. **Ponta a ponta (D045)**: ingestão → Qdrant → `/v1/chat` com auth, sessões, citações, ações e auditoria.
13. `scripts/avaliar_dominio.ps1`: sobe o Docker, sincroniza o Qdrant, roda dev/holdout e a
   calibração, salvando em `docs/resultados/`.

## 3. Pendências que dependem do autor (Theniels)

- [ ] `git push -u origin feature/robustez-0.9.2`, PR para `main`, CI verde, merge, `git switch main`, `git pull`.
- [ ] Repetir a coleta completa (agora com pausa de 15 s entre perguntas, ~6 minutos):
      `docker compose up -d --build`, `docker compose exec api ragtest-collect-answers` e
      `docker compose cp api:/app/state/respostas_modelo.csv docs\resultados\respostas_modelo_2.csv`.
- [ ] Pontuar a rubrica em `docs/resultados/respostas_modelo_2.csv` (colunas de 0 a 2; ver `docs/avaliacao-respostas.md`).
- [ ] (Quando quiser homologar) seguir `docs/DEPLOY.md`.

## 4. Próxima tarefa para o agente

Seguir `docs/ROTEIRO_EXECUCAO.md`: próxima micro-etapa do agente é **1.1.5** (após o autor
concluir 1.1.1–1.1.4), depois **1.2.4** (`ragtest-summarize-answers`).

Sempre que mudar o contrato: `ragtest-export-openapi` e `cd frontend && npm run generate:api`.
Ambiente remoto: `pytest tests -p no:cacheprovider --ignore=.pytest_cache`; o `tests/conftest.py`
isola o `.env` local (chaves falsas).

## 5. Como rodar (resumo)

    python -m pip install -e ".[dev]"
    pytest                      # ou: pytest tests -p no:cacheprovider --ignore=.pytest_cache
    ruff check .
    ragtest-audit-pii --subdir chatscm
    docker compose up -d && curl http://localhost:8000/ready

## 6. Push / GitHub

0.8.0 mesclada no `main` pelo PR #22 (28/09); o PR #21 da 0.7.0 foi absorvido por ele.

### Histórico

Em 28/09 o agente **não conseguiu fazer push**: o ambiente dele não tem credencial do GitHub, e o
terminal do Windows só aceita cliques. O autor deve rodar no PowerShell, na pasta do projeto:

    git push -u origin feature/audit-0.7.0 feature/dominio-0.8.0

Depois abrir, nesta ordem: PR `feature/audit-0.7.0` → `main`; após o merge, PR
`feature/dominio-0.8.0` → `main`. Quando feito, trocar esta seção por "branches enviadas em DD/MM".

## 7. Registro de sessões (mais recente no topo; 3–6 linhas cada)

- **2026-09-29 — Claude (Cowork)**: criado `docs/ROTEIRO_EXECUCAO.md` (briefing + Etapas 0–10 em
  micro-etapas até a v1.0.0); AGENTS e estado apontam para ele. `main` remoto tem commit do autor no README (`9712362`).
- **2026-09-28 (8) — Claude (Cowork)**: decisões do autor consolidadas (seção 0) e divisão de trabalho
  no AGENTS.md; fallbacks de agendamento corrigidos com poda de itens curtos e normalização ampla (D054).
- **2026-09-28 (7) — Claude (Cowork)**: holdout v3 = 24/25 (hybrid), critério PASS; coleta de
  respostas: 11/13 verificadas, 4/4 recusas; coleta ganhou `--only`, pausa e blocos sem citação.
- **2026-09-28 (6) — Claude (Cowork)**: 0.8.0 mesclada; branch `feature/qualidade-0.9.0`: citações
  【n†L】 (D051), critério mínimo + holdout v3 (D052), homologação com Caddy (D053), coleta de
  respostas para rubrica, esqueleto da monografia.
- **2026-09-28 (5) — Claude (Cowork)**: diagnóstico da mamografia → gate entende títulos em negrito e
  hierarquia de listas (D050).
- **2026-09-28 (4) — Claude (Cowork)**: avaliação v2 analisada (hybrid padrão, D046/D047); teste real do
  chat revelou recusa com citação falsa (D048), charset ausente (D049) e fallback na mamografia (#36).
- **2026-09-28 (3) — Claude (Cowork)**: diretriz backend headless registrada no plano, no AGENTS.md
  e aqui; regra de atualizar plano/estado a cada etapa. Ordem headless concluída: D042 (lógica na API), D043 (contrato), D044 (auth), D045 (e2e).

- **2026-09-28 — Claude (Cowork)**: análise do repositório e plano (`PLANO_FINALIZACAO_TCC.md`);
  Fase 0 parcial (`.gitattributes`, docs); Fase 1: auditoria de PII, D038 proposta, catálogo de
  serviços indexável. Commits na `feature/dominio-0.8.0`.
  Depois: escopo do corpus fixado em `data/source`, D038 aprovada, catálogo alinhado ao CHATSCM,
  dataset de avaliação v2 criado. Em seguida: triagem de urgência, fora de escopo calibrável,
  ações estruturadas, UI de ações/lembretes, INTEGRACAO.md, README novo, versão 0.8.0.
