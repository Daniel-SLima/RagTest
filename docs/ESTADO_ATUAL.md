# Estado atual — handoff entre agentes

> Documento **autoritativo e curto**. Todo agente lê este arquivo primeiro e o atualiza ao terminar.
> Plano completo: `docs/PLANO_FINALIZACAO_TCC.md`. Histórico até a 0.7.0: `docs/historico/`.

Última atualização: **2026-09-28** — Claude (Cowork), sessão de reorientação para o domínio.

---

## 1. Onde estamos

| Item | Valor |
|---|---|
| Fase do plano | **Fase 1 concluída no código** (falta sincronizar o Qdrant) · **Fase 2 preparada** (dataset v2 pronto, sem execução) |
| Branch de trabalho | `feature/dominio-0.8.0` (criada a partir de `feature/audit-0.7.0`) |
| Remoto | ver seção 3 (push) |
| Testes | `248 passed`; `ruff check .` → `All checks passed!` (28/09, Python 3.12) |
| Corpus indexado no Qdrant | Inalterado (767 chunks). Catálogo de serviços **ainda não sincronizado**. |

**Escopo do corpus (decisão do autor, 28/09):** os documentos de `data/source` são a base
documental suficiente. Não buscar nem adicionar fontes externas sem pedido explícito.

## 2. O que já foi feito (verificado)

1. `.gitattributes` (eol=lf) — acabou o falso "132 arquivos modificados" do CRLF.
2. `ragtest-audit-pii` — CHATSCM: 0 achados. **D038 aprovada** pelo autor: CHATSCM liberado para
   desenvolvimento e avaliação (checklist manual segue recomendado antes de produção).
3. Catálogo `data/source/servicos/catalogo_servicos.json` (preventivo, mamografia, pré-natal,
   urgência) validado por `app/catalog/services.py`; o loader gera 1 documento por serviço
   (`doc_type=servico`, `service_id`, `audience`). O texto de agendamento segue o CHATSCM
   (preventivo: "verifique a data do agendamento" na UBS; mamografia: UBS não realiza, a recepção
   busca vaga no sistema). O payload do Qdrant já recebe todo o metadata (`upsert` usa
   `{"text", **metadata}`), então `service_id` chegará em `SearchHit.metadata` após o sync.
4. Dataset de avaliação v2 em `app/evaluation/datasets/` (15 dev, 25 holdout congelado,
   4 fora de escopo), empacotado no `pyproject` e testado em `tests/test_domain_dataset_v2.py`.
   Instruções em `docs/avaliacao-retrieval.md` (seção "Dataset de domínio v2").
5. Documentação: este arquivo, `AGENTS.md` simplificado, `CLAUDE.md`, histórico em `docs/historico/`.

## 3. Pendências que dependem do autor (Theniels)

- [ ] **Sincronizar o Qdrant** com Docker ligado: `docker compose up -d --build` →
      `docker compose exec api ragtest-plan-ingestion-sync` → `docker compose exec api ragtest-sync-ingestion`
      (nunca `--recreate`).
- [ ] Rodar a avaliação v2 (comandos em `docs/avaliacao-retrieval.md`) e colar a saída aqui.
- [ ] Abrir os PRs no GitHub (ver seção 6: status do push).

## 4. Próxima tarefa para o agente (em ordem)

1. **Se a avaliação v2 já tiver resultados:** registrar a tabela em `docs/avaliacao-retrieval.md`,
   analisar falhas do **dev** (nunca ajustar em cima do holdout) e registrar dificuldades.
2. **Triagem de urgência determinística** (Fase 3): `app/safety/triage.py` com os
   `sinais_alarme` do serviço `urgencia_obstetrica` do catálogo + variações coloquiais
   ("vista embaçada", "tô sangrando", "bolsa estourou"); se casar, `/v1/chat` devolve resposta fixa
   (maternidade/UPA/192) **sem chamar o LLM**, com `safety.triaged=true`. TDD com os casos
   `topic=urgencia` do dataset v2.
3. **Fora de escopo** (Fase 3): limiar de score calibrado no dev + `dominio-v2-fora-escopo.json`.
4. **Ações estruturadas** (Fase 4): campo `actions` no `/v1/chat` a partir do `service_id` das
   fontes citadas (`open_link`, `schedule_reminder` com `lembretes` do catálogo, `call_emergency`).
5. Depois: UI (Fase 5) e guia de integração (Fase 6).

## 5. Como rodar (resumo)

    python -m pip install -e ".[dev]"
    pytest                      # ou: pytest tests -p no:cacheprovider --ignore=.pytest_cache
    ruff check .
    ragtest-audit-pii --subdir chatscm
    docker compose up -d && curl http://localhost:8000/ready

## 6. Push / GitHub

(atualizado ao final da sessão)

## 7. Registro de sessões (mais recente no topo; 3–6 linhas cada)

- **2026-09-28 — Claude (Cowork)**: análise do repositório e plano (`PLANO_FINALIZACAO_TCC.md`);
  Fase 0 parcial (`.gitattributes`, docs); Fase 1: auditoria de PII, D038 proposta, catálogo de
  serviços indexável. Commits na `feature/dominio-0.8.0`.
  Depois: escopo do corpus fixado em `data/source`, D038 aprovada, catálogo alinhado ao CHATSCM,
  dataset de avaliação v2 criado.
