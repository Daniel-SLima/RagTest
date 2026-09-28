# Estado atual — handoff entre agentes

> Documento **autoritativo e curto**. Todo agente lê este arquivo primeiro e o atualiza ao terminar.
> Plano completo: `docs/PLANO_FINALIZACAO_TCC.md`. Histórico até a 0.7.0: `docs/historico/`.

Última atualização: **2026-09-28** — Claude (Cowork), sessão de reorientação para o domínio.

---

## 1. Onde estamos

> **Diretriz vigente: backend headless.** O produto é a API; o Expo é cliente de referência congelado.

| Item | Valor |
|---|---|
| Versão | **0.8.0** no `main` (PR #22 mesclado em 28/09) · trabalho novo em `feature/qualidade-0.9.0` |
| Branch de trabalho | `feature/qualidade-0.9.0` (a partir do `main`), **não enviada ao GitHub** |
| Testes | backend `332 passed` (inclui 5 ponta a ponta), `ruff` limpo · frontend Jest `19 passed`, `tsc` ok (28/09) |
| Avaliação | hybrid: dev v2 15/15 (MRR 0.833) · holdout v2 24/25 (não independente) · **holdout v3 congelado, não executado** |
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

- [ ] `git push -u origin feature/qualidade-0.9.0`, abrir PR para `main`, esperar CI verde e fazer merge.
- [ ] Rodar de novo `powershell -ExecutionPolicy Bypass -File scripts/avaliar_dominio.ps1`
      (agora roda o **holdout v3** e o **critério de aprovação**).
- [ ] Gerar a planilha da rubrica: ver `docs/avaliacao-respostas.md` (3 comandos) e pontuar as colunas.
- [ ] (Quando quiser homologar) seguir `docs/DEPLOY.md` num servidor com domínio.
- [ ] Antes de expor a API fora do seu computador, definir `API_KEYS` no `.env`.

## 4. Próxima tarefa para o agente

1. Quando existir o novo `docs/resultados/avaliacao_*.txt`: registrar holdout v3 e o resultado do
   critério em `docs/avaliacao-retrieval.md` (sem ajustar nada olhando o v3).
2. Quando existir `docs/resultados/respostas_modelo.csv` pontuado: calcular médias, taxas e
   latência e preencher "Resultados" em `docs/avaliacao-respostas.md`.
3. Falha conhecida do retrieval: "de quanto em quanto tempo repito o preventivo" (holdout v2).
   Só investigar com perguntas do **dev**; considerar criar um caso dev equivalente.
4. Monografia: usar `docs/monografia/ESQUELETO.md` como índice de evidências.
5. Opcional (defesa): adaptador `BaseRetriever` do LangChain sobre o retriever próprio.

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
