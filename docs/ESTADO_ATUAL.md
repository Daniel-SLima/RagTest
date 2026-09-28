# Estado atual — handoff entre agentes

> Documento **autoritativo e curto**. Todo agente lê este arquivo primeiro e o atualiza ao terminar.
> Plano completo: `docs/PLANO_FINALIZACAO_TCC.md`. Histórico até a 0.7.0: `docs/historico/`.

Última atualização: **2026-09-28** — Claude (Cowork), sessão de reorientação para o domínio.

---

## 1. Onde estamos

| Item | Valor |
|---|---|
| Versão | **0.8.0** (backend e frontend) |
| Fases do plano | F1 ✅ código · F2 ⏳ dataset pronto, falta executar · F3 ✅ triagem + fora de escopo (limiar a calibrar) · F4 ✅ ações · F5 🟡 UI básica pronta · F6 🟡 `INTEGRACAO.md` pronto |
| Branch de trabalho | `feature/dominio-0.8.0` (a partir de `feature/audit-0.7.0`) |
| Testes | backend `280 passed`, `ruff` limpo · frontend Jest `18 passed`, `tsc` ok (28/09) |
| Qdrant | Inalterado (767 chunks). Catálogo **não sincronizado** — o agente não tem Docker nem acesso ao HuggingFace. |

**Escopo do corpus (decisão do autor):** só os documentos de `data/source`.

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
9. `scripts/avaliar_dominio.ps1`: sobe o Docker, sincroniza o Qdrant, roda dev/holdout e a
   calibração, salvando em `docs/resultados/`.

## 3. Pendências que dependem do autor (Theniels)

- [ ] Rodar `scripts/avaliar_dominio.ps1` no PowerShell (Docker Desktop ligado). Se o
      PowerShell bloquear scripts: `powershell -ExecutionPolicy Bypass -File scripts/avaliar_dominio.ps1`.
- [ ] Se a calibração sugerir um valor, colocar `RETRIEVAL_MIN_SCORE=<valor>` no `.env` e
      `docker compose up -d`.
- [ ] Testar o app: `cd frontend && npm install && npm run web` e perguntar
      "como agendo a mamografia?" e "estou grávida e sangrando".
- [ ] `git push -u origin feature/audit-0.7.0 feature/dominio-0.8.0` e abrir os PRs (seção 6).

## 4. Próxima tarefa para o agente (em ordem)

1. **Ler `docs/resultados/avaliacao_*.txt`** (se existir): registrar HitRate/MRR por modo em
   `docs/avaliacao-retrieval.md`, analisar falhas só do **dev**, registrar dificuldades reais.
2. **Avaliação da resposta** (F2): rubrica manual 0–2 (fidelidade, relevância, clareza) em
   `docs/avaliacao-respostas.md` para ~15 perguntas do dev, com `grounded_rate`/`fallback_rate`.
3. **Lembretes nativos** (F5): `npx expo install expo-notifications` e agendar notificação local
   em `handleScheduleReminder` (App.tsx) por trás de uma interface injetável (manter testes).
4. **Triagem: mais variações** a partir das falhas observadas; manter `tests/test_triage.py`.
5. F6/F7: deploy de homologação, teste de usabilidade (SUS), capítulos da monografia.

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

- **2026-09-28 — Claude (Cowork)**: análise do repositório e plano (`PLANO_FINALIZACAO_TCC.md`);
  Fase 0 parcial (`.gitattributes`, docs); Fase 1: auditoria de PII, D038 proposta, catálogo de
  serviços indexável. Commits na `feature/dominio-0.8.0`.
  Depois: escopo do corpus fixado em `data/source`, D038 aprovada, catálogo alinhado ao CHATSCM,
  dataset de avaliação v2 criado. Em seguida: triagem de urgência, fora de escopo calibrável,
  ações estruturadas, UI de ações/lembretes, INTEGRACAO.md, README novo, versão 0.8.0.
