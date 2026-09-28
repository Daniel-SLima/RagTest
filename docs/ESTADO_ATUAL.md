# Estado atual — handoff entre agentes

> Documento **autoritativo e curto**. Todo agente lê este arquivo primeiro e o atualiza ao terminar.
> Plano completo: `docs/PLANO_FINALIZACAO_TCC.md`. Histórico até a 0.7.0: `docs/historico/`.

Última atualização: **2026-09-28** — Claude (Cowork), sessão de reorientação para o domínio.

---

## 1. Onde estamos

> **Diretriz vigente (28/09): backend headless.** O produto é a API; o Expo é cliente de referência
> congelado. Detalhes na seção 0 do `PLANO_FINALIZACAO_TCC.md`.

| Item | Valor |
|---|---|
| Versão | **0.8.0** (backend e frontend) |
| Etapa atual | Avaliação v2 + teste real do chat feitos (28/09). Corrigidos: recusa com citação falsa (D048) e charset (D049). Fallback da mamografia diagnosticado e corrigido (D050) — falta repetir o teste real |
| Branch de trabalho | `feature/dominio-0.8.0` (a partir de `feature/audit-0.7.0`) |
| Testes | backend `322 passed` (inclui 5 ponta a ponta), `ruff` limpo · frontend Jest `19 passed`, `tsc` ok (28/09) |
| Avaliação v2 | hybrid: dev 15/15 (MRR 0.833), holdout 24/25 após D047 (não independente) · dense-rerank: 9/15 e 21/25 — ver `docs/avaliacao-retrieval.md` |
| Qdrant | 773 chunks, sincronizado em 28/09 após a D047 |
| GitHub | `feature/audit-0.7.0` e `feature/dominio-0.8.0` enviadas em 28/09 (até `59b35ab`); commits posteriores só locais |

**Escopo do corpus (decisão do autor):** só os documentos de `data/source`.
**Stack do orientador:** FastAPI ✅ · Qdrant ✅ · LangChain ✅ (uso seletivo) · React Native via REST ✅ · Docker Compose ✅.

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

- [x] Avaliação v2, teste do chat, diagnóstico da mamografia e push inicial (28/09).
- [ ] `git push` dos commits novos, esperar a CI e fazer o merge: primeiro o PR `audit-0.7.0`,
      depois o `dominio-0.8.0`. Em seguida `git switch main` e `git pull`.
- [ ] Repetir o teste real: `docker compose up -d --build` e
      `docker compose exec api ragtest-chat "Como eu agendo a mamografia?" > docs\resultados\diagnostico_mamografia_2.txt`.
- [ ] Antes de expor a API fora do seu computador, definir `API_KEYS` no `.env`.

## 4. Próxima tarefa para o agente (ordem headless)

1. ~~Rodar a avaliação v2~~ → depende do autor (seção 3). Quando existir `docs/resultados/avaliacao_*.txt`,
   registrar as métricas em `docs/avaliacao-retrieval.md` e analisar falhas só do dev.
2. ✅ **Lógica de apresentação na API** (D042): `display`, `sources[].title/location_label`,
   `actions[].due_date/requires_host_app/note`, `GET /v1/suggestions`. Expo só renderiza.
3. ✅ **Contrato congelado** (D043): `docs/contrato/openapi-v1.json` + `tests/test_contract.py`,
   `ragtest-export-openapi`, cliente TS gerado (`npm run generate:api`, checado na CI),
   `GET /v1/services` e `GET /v1/services/{id}`.
4. ✅ **Autenticação** (D044): `API_KEYS` + `X-API-Key` em `/v1/*`, limite `RATE_LIMIT_PER_MINUTE`
   no `/v1/chat`, 401/429 normalizados e auditados.
5. ✅ **Teste ponta a ponta** (D045): `tests/e2e/` (Qdrant em memória local; job `e2e-qdrant` na CI
   com Qdrant real).

**Próximas tarefas (depois da ordem headless):**

6. ✅ Dificuldade #36 corrigida (D050). Conferir `diagnostico_mamografia_2.txt` quando existir.
   Depois do merge, trabalhar em branch nova a partir da `main` (ex.: `feature/qualidade-0.9.0`).
7. ✅ Avaliação v2 registrada; hybrid padrão (D046); calibração sem separação (limiar desligado);
   recusas viram fora de escopo (D048).
   Próximo: congelar **holdout v3** (perguntas novas) e transformar mínimos em critério de
   aprovação (`--min-passrate`), usando o dev v2 como referência.
8. Rubrica manual das respostas (`docs/avaliacao-respostas.md`) com o provider real.
9. `docker-compose.prod.yml` + deploy de homologação com `API_KEYS` (F6 item 4).
10. Monografia: capítulos de arquitetura, guardrails e resultados a partir de `decisoes-tecnicas.md`
   (D001–D045), `dificuldades-tcc.md` e `docs/resultados/`.

Sempre que mudar o contrato: `ragtest-export-openapi` e `cd frontend && npm run generate:api`.

**Observação para agentes em ambiente remoto:** `pytest tests -p no:cacheprovider --ignore=.pytest_cache`
(a pasta `.pytest_cache` pode estar bloqueada); o frontend precisa de `npm install` próprio fora da
pasta do usuário se o `node_modules` dela for do Windows.

## 5. Como rodar (resumo)

    python -m pip install -e ".[dev]"
    pytest                      # ou: pytest tests -p no:cacheprovider --ignore=.pytest_cache
    ruff check .
    ragtest-audit-pii --subdir chatscm
    docker compose up -d && curl http://localhost:8000/ready

## 6. Push / GitHub

Em 28/09 o agente **não conseguiu fazer push**: o ambiente dele não tem credencial do GitHub, e o
terminal do Windows só aceita cliques. O autor deve rodar no PowerShell, na pasta do projeto:

    git push -u origin feature/audit-0.7.0 feature/dominio-0.8.0

Depois abrir, nesta ordem: PR `feature/audit-0.7.0` → `main`; após o merge, PR
`feature/dominio-0.8.0` → `main`. Quando feito, trocar esta seção por "branches enviadas em DD/MM".

## 7. Registro de sessões (mais recente no topo; 3–6 linhas cada)

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
