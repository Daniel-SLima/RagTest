# Estado atual — handoff entre agentes

> Documento **autoritativo e curto**. Todo agente lê este arquivo primeiro e o atualiza ao terminar.
> Plano completo: `docs/PLANO_FINALIZACAO_TCC.md`. Histórico até a 0.7.0: `docs/historico/`.

Última atualização: **2026-09-28** — Claude (Cowork), sessão de reorientação para o domínio.

---

## 1. Onde estamos

| Item | Valor |
|---|---|
| Fase do plano | **Fase 1 — corpus de domínio** (em andamento). Fase 0 parcialmente concluída. |
| Branch de trabalho | `feature/dominio-0.8.0` (criada a partir de `feature/audit-0.7.0`) |
| Remoto | `origin/main` = 0.6.0 (`f173a29`). **Nada desta sessão foi enviado** (sem push). |
| Branches locais não enviadas | `feature/audit-0.7.0` (+18 commits sobre o remoto) e `feature/dominio-0.8.0` (+4 sobre a audit) |
| Testes | `243 passed`; `ruff check .` → `All checks passed!` (28/09, Python 3.12) |
| Corpus indexado no Qdrant | Inalterado (767 chunks). Catálogo e novas fontes **ainda não sincronizados**. |

## 2. O que foi feito nesta sessão (verificado)

1. **`.gitattributes` (eol=lf)** — eliminou o falso "132 arquivos modificados" causado por CRLF.
2. **`ragtest-audit-pii`** (`app/rag/pii_audit.py`, `app/cli/audit_pii.py`, `tests/test_pii_audit.py`):
   detecta CPF, CNPJ, CNS, telefone, e-mail, CEP e datas em DOCX sem imprimir texto.
   Resultado no CHATSCM: **0 achados nos 3 arquivos**.
3. **D038 (proposta)** em `docs/decisoes-tecnicas.md` + checklist em `docs/revisao-privacidade-chatscm.md`.
4. **Catálogo de serviços** `data/source/servicos/catalogo_servicos.json` (v `2026-09-28-v1`):
   `preventivo`, `mamografia`, `prenatal`, `urgencia_obstetrica`, com público, periodicidade,
   onde/como agendar, documentos, preparo, sinais de alarme, link, lembretes sugeridos e fontes.
   - Modelo/validação: `app/catalog/services.py` (Pydantic; exige fonte e ids únicos).
   - O loader (`app/rag/loaders.py`) agora aceita `.json` em `data/source` e gera **1 documento
     por serviço** com `doc_type=servico`, `service_id`, `audience`, `catalog_version`.
   - Testes: `tests/test_service_catalog.py`.
   - Conteúdo clínico conferido com: Diretriz MS 2025 (DNA-HPV, 25–64 anos, 5 anos),
     INCA 2016 (Papanicolau 1 ano + 1 ano, depois 3 anos), NT 626/2025 (mamografia 50–74 bienal;
     40–49 e >74 por decisão compartilhada), CHATSCM e Caderneta da Gestante 2024 (sinais de alerta).
5. **Documentação reorganizada**: este arquivo criado; `AGENTS.md` simplificado; `CLAUDE.md`
   aponta para o `AGENTS.md`; `CONTEXTO_CONTINUIDADE.md` e `PROMPT_RETOMADA.md` movidos para `docs/historico/`.

## 3. Pendências que dependem do autor (Theniels)

- [ ] **Aprovar a D038**: preencher o checklist em `docs/revisao-privacidade-chatscm.md`,
      mudar o status da D038 para "Aprovada" e remover a restrição do CHATSCM no `AGENTS.md`.
- [ ] **Baixar os PDFs de rastreamento** listados em `data/source/rastreamento/LEIA-ME.md`
      (a rede do agente bloqueou gov.br/cofen).
- [ ] **Push + PR** (quando quiser): primeiro `feature/audit-0.7.0` → PR para `main`; depois
      `feature/dominio-0.8.0` → PR para `main` (após o merge da audit).
- [ ] **Sincronizar o Qdrant** com Docker ligado: `docker compose up -d` →
      `ragtest-plan-ingestion-sync` → `ragtest-sync-ingestion` (nunca `--recreate`).

## 4. Próxima tarefa para o agente (em ordem)

1. **Metadados de domínio no retrieval** (Fase 1):
   - confirmar em teste que `doc_type` e `service_id` chegam ao payload do Qdrant e a `SearchHit.metadata`;
   - adicionar `doc_type` à lista de payload indexes em `QdrantVectorStore` (`vector_store.py`, perto de
     `for field_name in ("category", "audience", "source", "file_type")`) — só afeta collections novas;
     registrar em `decisoes-tecnicas.md`;
   - `infer_audience`: pastas `rastreamento/` → `mulher`.
2. **Dataset de avaliação v2** (Fase 2): criar `app/evaluation/cases_v2.py` (ou JSON versionado
   `2026-10-v2`) com ~40 perguntas em linguagem de usuária: 15 rastreamento, 10 agendamento/acesso,
   8 gestação, 4 urgência, 3 fora de escopo; dev (15) × holdout congelado (25); fontes esperadas
   incluindo `servicos/catalogo_servicos.json` e `chatscm/*`. Reusar `evaluate_retrieval`.
   Rodar só após o Qdrant ser sincronizado.
3. **Triagem de urgência determinística** (Fase 3): `app/safety/triage.py` usando
   `sinais_alarme` do serviço `urgencia_obstetrica` do catálogo; resposta fixa sem LLM.
4. Depois seguir o plano: fora de escopo → ações estruturadas (`actions` no `/v1/chat`) → UI.

## 5. Como rodar (resumo)

    python -m pip install -e ".[dev]"
    pytest                      # ou: pytest tests -p no:cacheprovider --ignore=.pytest_cache
    ruff check .
    ragtest-audit-pii --subdir chatscm
    docker compose up -d && curl http://localhost:8000/ready

## 6. Registro de sessões (mais recente no topo; 3–6 linhas cada)

- **2026-09-28 — Claude (Cowork)**: análise do repositório e plano (`PLANO_FINALIZACAO_TCC.md`);
  Fase 0 parcial (`.gitattributes`, docs); Fase 1: auditoria de PII, D038 proposta, catálogo de
  serviços indexável. Commits na `feature/dominio-0.8.0`. Sem push.
