# Roteiro de execução até a conclusão (v1.0.0)

> Roteiro com micro-etapas numeradas (`1.1.1`) para qualquer agente de IA levar o RagTest do estado
> atual até o TCC 100% concluído, sem precisar do histórico da conversa.
> Criado em **29/09/2026** por Claude (Cowork). Marque `[x]` em cada micro-etapa concluída e
> registre a data. Os comandos são para o **PowerShell na pasta do projeto**
> (`C:\Users\Usuario\Documents\TCC\00-RagTest`), salvo indicação em contrário.

---

# PARTE A — Briefing obrigatório para o agente

## A.1 O projeto em poucas linhas

- **O que é:** módulo conversacional RAG (Retrieval-Augmented Generation) para o app **Se Cuida
  Mulher**. Apoia o letramento em saúde da mulher e orienta o agendamento de serviços do SUS:
  preventivo, mamografia, pré-natal e sinais de urgência. É o TCC de ADS do autor, **Theniels**
  (GitHub `Daniel-SLima`), a partir de proposta do orientador.
- **Diretriz central — backend headless:** o produto é a **API**. O frontend Expo
  (`frontend/`) é só um **cliente de referência congelado**. Nenhuma feature nova vai para ele.
  Toda regra de negócio e todo texto de exibição ficam no backend. O app final vai ser escrito
  depois (Flutter ou React Native) e só vai desenhar telas.
- **Stack (a que o orientador sugeriu):**
  - Python 3.12 + FastAPI;
  - Qdrant 1.19 (vetores densos + esparsos BM25);
  - FastEmbed;
  - LangChain (uso seletivo);
  - providers de LLM Groq (GPT-OSS 120B, o padrão), Gemini e Ollama;
  - Expo/React Native via REST;
  - Docker Compose;
  - GitHub Actions.
- **Corpus:** somente os documentos de `data/source/`, por decisão do autor. Nenhuma fonte
  externa entra sem pedido explícito.

## A.2 Leitura obrigatória, nesta ordem

| # | Arquivo | Para quê |
|---|---|---|
| 1 | `AGENTS.md` | Regras invioláveis, divisão autor × agente, Git, testes, privacidade, Qdrant. |
| 2 | **este arquivo** (`docs/ROTEIRO_EXECUCAO.md`) | O que fazer, em que ordem, e o critério de pronto de cada passo. |
| 3 | `docs/ESTADO_ATUAL.md` | Onde o trabalho parou; seção 0 = decisões do autor; seção 3 = pendências do autor; seção 7 = registro de sessões. |
| 4 | `docs/PLANO_FINALIZACAO_TCC.md` | Seção 0 (diretriz headless e aderência à stack) e seção 6 (status das fases). As seções 1–3 são histórico da análise inicial. |
| 5 | `docs/INTEGRACAO.md` | O contrato da API do ponto de vista do app integrador (campos `display`, `safety`, `actions`, erros, autenticação). |

## A.3 Leitura sob demanda, conforme a micro-etapa

| Arquivo | Quando ler |
|---|---|
| `docs/decisoes-tecnicas.md` | Antes de mudar retrieval, guardrails, contrato ou segurança. Contém D001–D054; **a próxima é D055**. |
| `docs/dificuldades-tcc.md` | Antes de investigar uma falha (pode já estar descrita). Tem #1–#40; **o próximo é #41**. |
| `docs/avaliacao-retrieval.md` | Metodologia (dev × holdout), resultados v2/v3 e critério de aprovação. |
| `docs/avaliacao-respostas.md` | Rubrica 0–2 das respostas e resultados da coleta. |
| `docs/DEPLOY.md` | Homologação com HTTPS (Caddy) e `API_KEYS`. |
| `docs/contrato/openapi-v1.json` | Contrato congelado. Nunca editar à mão; regenerar. |
| `docs/monografia/ESQUELETO.md` | Mapa capítulo → evidência. |
| `docs/revisao-privacidade-chatscm.md` | Liberação do FAQ CHATSCM (D038). |
| `data/source/README.md` e `data/source/servicos/catalogo_servicos.json` | Corpus e catálogo de serviços (links, lembretes, sugestões). |
| `docs/resultados/` | Saídas brutas das execuções feitas pelo autor. |
| `docs/historico/` | Contexto antigo (até a 0.7.0). **Somente leitura.** |

## A.4 Regras invioláveis (resumo do `AGENTS.md`)

1. Nunca leia, imprima ou versione valores do `.env` nem chaves de API.
2. Nunca rode `ragtest-ingest --recreate` nem `docker compose down -v`.
3. Para incluir fontes, use sempre `ragtest-plan-ingestion-sync` e depois `ragtest-sync-ingestion --apply`.
4. Git:
   - nunca use `reset --hard`, `clean`, rebase nem force-push;
   - não apague branch;
   - **push e merge são do autor**.
5. Mudança funcional segue TDD:
   - teste RED;
   - implementação;
   - suíte completa;
   - `ruff check .`
6. **Ajustes só com os datasets de dev.** Holdouts rodam uma vez e nunca guiam ajustes. O v2 já foi
   consumido. O v3 foi rodado uma vez e está contaminado pela falha "libido" (ver 2.2).
7. Mudou o contrato da API? Rode `ragtest-export-openapi`, depois `cd frontend && npm run generate:api`
   e revise o diff de `docs/contrato/openapi-v1.json`.
8. Logs e auditoria nunca registram perguntas, respostas, prompts ou trechos. O texto bruto de
   respostas rejeitadas só aparece na coleta local (`ragtest-collect-answers`).
9. `grounded=true` significa cobertura estrutural de citações, **não** validação clínica.
10. **Ao terminar cada micro-etapa:**
    - marque `[x]` aqui;
    - atualize `docs/ESTADO_ATUAL.md` (seções 1, 3, 4 e 7);
    - atualize o status em `PLANO_FINALIZACAO_TCC.md` §6, quando mudar uma fase;
    - registre decisão (Dxxx) ou dificuldade (#n) quando houver.

## A.5 Divisão de trabalho autor × agente

| Quem | Faz |
|---|---|
| **Agente** | Código, testes, documentação e análise dos resultados. Trabalha na pasta local, numa branch por etapa, e faz commits. |
| **Autor** | `git push`, PRs e merge no GitHub, Docker, execuções com modelos reais (embeddings e LLM, que precisam de rede e chave), deploy, notas da rubrica, contato com o orientador e com as participantes. |

- O agente escreve os comandos exatos para o autor na seção 3 do `ESTADO_ATUAL.md` e na
  micro-etapa correspondente deste roteiro.
- O autor devolve as saídas em `docs/resultados/`, e o agente lê de lá.
- Fluxo de branch: `feature/<tema>-<versão>` a partir do `main` atualizado → 1 PR → CI verde
  (`lint`, `test`, `e2e-qdrant`, `frontend-test`) → merge → `git switch main` e `git pull`.

## A.6 Ambiente e comandos úteis

| Tarefa | Comando |
|---|---|
| Testes backend (máquina normal) | `pytest` e `ruff check .` |
| Testes backend (VM do agente, com `.pytest_cache` bloqueado) | `pytest tests -p no:cacheprovider --ignore=.pytest_cache -o addopts="" -q` |
| Testes frontend | `cd frontend && npm test && npm run typecheck` |
| Regenerar contrato | `ragtest-export-openapi` e `cd frontend && npm run generate:api` |
| Subir tudo | `docker compose up -d --build` |
| Sincronizar corpus | `docker compose exec api ragtest-plan-ingestion-sync` e `... ragtest-sync-ingestion --apply` |
| Avaliação completa + critério | `powershell -ExecutionPolicy Bypass -File scripts/avaliar_dominio.ps1` |
| Diagnóstico de uma pergunta | `docker compose exec api ragtest-chat "pergunta"` |
| Coleta de respostas (rubrica) | `docker compose exec api ragtest-collect-answers` e `docker compose cp api:/app/state/respostas_modelo.csv docs\resultados\<nome>.csv` |

Armadilhas conhecidas:

- `tests/conftest.py` troca as chaves por valores falsos. **Nunca remover** (dificuldade #38).
- No PowerShell 5.1, o `>` grava em UTF-16. Para texto do container, prefira
  `docker compose cp` ou o script de avaliação, que grava em UTF-8 (dificuldades #33 e #37).
- A cota grátis da Groq é de 8 mil tokens por minuto. A coleta usa `--pause-seconds 15`, e só vale
  reportar latência de execuções sem erro 429 (dificuldade #39).
- Na VM do agente, o Git pode deixar `.git/*.lock` e `tmp_obj_*` presos. Peça permissão de exclusão
  e apague só esses arquivos.
- Commits do agente terminam com as linhas de atribuição da sessão, quando o ambiente as fornecer.

## A.7 Convenções

- **Versão:** o pacote está em `0.8.0` (`pyproject.toml`, `app/core/config.py`, `frontend/package.json`).
  As branches `0.9.x` são rótulos de etapa. O bump único para **1.0.0** acontece na Etapa 10.
- **Decisões:** `## D0xx — título` com Data, Mudança ou Decisão, Motivo e Impacto.
- **Dificuldades:** `## N. título` com os campos Planejado, Observado, Diagnóstico, Correção e Aprendizado técnico.
- **Resultados brutos:** `docs/resultados/<tipo>_<AAAA-MM-DD_HHMM>.<ext>`, sempre em UTF-8.

## A.8 Estado no momento em que este roteiro foi escrito (29/09/2026)

- `origin/main` = `9712362`, "docs: improve portfolio README". Commit do autor feito direto no
  `main`, depois do PR #24. **Não sobrescrever o README do autor**; qualquer mudança nele deve ser
  incremental.
- Branch local `feature/robustez-0.9.2` com:
  - `1e380c6`, D054: poda de itens curtos e normalização `【n…】`;
  - o commit deste roteiro.
  
  **Ainda não enviada ao GitHub.**
- **Testes:** 339 no backend (5 ponta a ponta) e 19 no frontend, todos verdes; Ruff limpo.
- **Métricas de retrieval (modo padrão hybrid):**
  - dev v2: 15/15, MRR 0.833;
  - holdout v3: 24/25, MRR 0.801;
  - critério de aprovação: PASS.
- **Respostas (execução 1):**
  - 11 de 13 verificadas;
  - 2 de 2 triagens;
  - 4 de 4 recusas corretas;
  - os 2 fallbacks foram corrigidos pela D054, mas **falta revalidar**;
  - a latência medida está contaminada por erros 429.
- **Pendentes do autor:**
  - push e merge da 0.9.2;
  - coleta 2;
  - rubrica;
  - deploy de homologação (opcional).

## A.9 Definição de "100% concluído" (v1.0.0)

1. `main` com a versão **1.0.0**, tag `v1.0.0` e release no GitHub. CI verde.
2. Avaliação final registrada:
   - retrieval dev + **holdout v4** (nunca usado para ajustes);
   - critério de aprovação PASS;
   - métricas das respostas (rubrica, grounded, fallback, recusa, triagem, latência sem 429).
3. API homologada, num servidor com HTTPS ou num ambiente local documentado com smoke test.
4. `docs/INTEGRACAO.md` completo, com exemplos de cliente em TypeScript e Dart, e `CHANGELOG.md`
   do 0.5 ao 1.0.
5. Teste de usabilidade feito, com o SUS calculado, **ou** a justificativa de não ter sido feito
   registrada com o aval do orientador.
6. Monografia com todos os capítulos redigidos a partir das evidências, figuras e tabelas finais, e
   revisada pelo orientador.
7. Roteiro de apresentação e demonstração pronto.
8. `ESTADO_ATUAL.md` com o encerramento e o plano §6 todo em ✅.

## A.10 Formato de cada micro-etapa

```
- [ ] X.Y.Z [Quem] Ação — detalhes.
      Comandos / Arquivos / Pronto quando / Registrar
```

`[Autor]` = só o autor pode fazer. `[Agente]` = o agente faz. `[Ambos]` = o agente prepara e o autor executa.

---

# PARTE B — Etapas até a conclusão

## Etapa 0 — O que este agente está fazendo agora (29/09)

- [x] 0.1.1 [Agente] Criar este roteiro (`docs/ROTEIRO_EXECUCAO.md`) na branch `feature/robustez-0.9.2`.
- [x] 0.1.2 [Agente] Colocar este roteiro no topo da ordem de leitura do `AGENTS.md` e do `ESTADO_ATUAL.md`.
- [x] 0.1.3 [Agente] Commit "docs: roteiro de execução em micro-etapas até a v1.0.0".
- [x] 0.1.4 [Autor] Seguir a Etapa 1.1, que publica este roteiro junto com a D054. (05/10/2026, PR #25)

## Etapa 1 — Fechar a 0.9.2 (robustez das respostas)

### 1.1 Publicar a branch atual

> Concluída em 05/10/2026: a branch `feature/transferencia-0.9.2` foi criada do `main`
> público (`9712362`) e recebeu a D054, este roteiro e a documentação de transferência.
> O PR #25 foi mesclado; a antiga `feature/robustez-0.9.2` permanece apenas como referência local.

- [x] 1.1.1 [Autor] Enviar a branch: `git push -u origin feature/transferencia-0.9.2`. (05/10/2026)
- [x] 1.1.2 [Autor] Criar o PR `feature/transferencia-0.9.2` → `main`. (PR #25, 05/10/2026)
  - Título: "0.9.2 — robustez das respostas e documentação de continuidade".
- [x] 1.1.3 [Autor] Conferir os 4 checks da CI verdes: `lint`, `test`, `e2e-qdrant` e
  `frontend-test`. (05/10/2026, PR #25)
- [x] 1.1.4 [Autor] Fazer o merge, depois `git switch main` e `git pull --ff-only`. (05/10/2026, merge `42c8f7f`)
- [x] 1.1.5 [Agente] Conferir que o `main` contém o commit `9712362`, a mudança da D054
  (reaplicada como `53cc70c`) e o guia de continuidade. (05/10/2026; estado §1 e §6 atualizados)

### 1.2 Coleta de respostas 2 (revalidar a D054)

- [ ] 1.2.1 [Autor] Rodar `docker compose up -d --build`.
- [ ] 1.2.2 [Autor] Rodar `docker compose exec api ragtest-collect-answers` (19 perguntas, cerca de 6 minutos).
- [ ] 1.2.3 [Autor] Copiar o resultado:
  `docker compose cp api:/app/state/respostas_modelo.csv docs\resultados\respostas_modelo_2.csv`.
- [ ] 1.2.4 [Agente] Criar o comando `ragtest-summarize-answers` (TDD), que lê um ou mais CSVs e
  imprime:
  - contagem por `status`;
  - taxa de `verified` entre as perguntas do domínio não triadas;
  - taxa de recusa correta nos casos `v2-oos-*`;
  - taxa de repair;
  - latência média e p95;
  - média de cada coluna da rubrica, quando preenchida.
  
  Arquivos: `app/evaluation/summary.py`, `app/cli/summarize_answers.py`, `tests/test_answer_summary.py`
  e `pyproject.toml` (novo script). Esse comando roda fora do Docker: `python -m app.cli.summarize_answers <csv>`.
- [ ] 1.2.5 [Agente] Rodar o resumo sobre `respostas_modelo.csv` e `respostas_modelo_2.csv` e
  registrar a "Execução 2" em `docs/avaliacao-respostas.md`, comparando com a execução 1.
  - **Pronto quando:** a tabela de comparação está no documento.
- [ ] 1.2.6 [Agente] Se ainda houver fallback ou recusa errada:
  1. ler `blocos_sem_citacao` e `resposta_rejeitada`;
  2. reproduzir num teste;
  3. corrigir;
  4. registrar D055+ e a dificuldade #41+.
  
  Se não houver, registrar "sem fallbacks" na §1 do `ESTADO_ATUAL.md`.

### 1.3 Rubrica manual

- [ ] 1.3.1 [Autor] Abrir `docs\resultados\respostas_modelo_2.csv` no Excel e preencher
  `fidelidade_0a2`, `relevancia_0a2` e `clareza_0a2` seguindo `docs/avaliacao-respostas.md`.
  Salvar como "CSV UTF-8 (delimitado por vírgulas)" e manter o `;`.
- [ ] 1.3.2 [Autor, opcional e recomendado] Uma segunda pessoa pontua uma cópia,
  `respostas_modelo_2_avaliador2.csv`, sem ver as notas do autor.
- [ ] 1.3.3 [Agente] Estender o `ragtest-summarize-answers` com:
  - kappa de Cohen ponderado por critério, quando houver os dois arquivos;
  - porcentagem de notas 2.
  
  TDD com notas sintéticas.
- [ ] 1.3.4 [Agente] Registrar os resultados da rubrica em `docs/avaliacao-respostas.md` e nas
  §1 e §7 do `ESTADO_ATUAL.md`.
  - **Pronto quando:** médias e kappa (ou "avaliador único") estão registrados.

## Etapa 2 — Qualidade restante do retrieval (branch `feature/retrieval-0.9.3`)

> Metodologia: congelar o **holdout v4 antes** de qualquer ajuste desta etapa. Os ajustes usam
> só os casos de dev.

### 2.1 Congelar o holdout final v4

- [ ] 2.1.1 [Agente] Criar a branch `feature/retrieval-0.9.3` a partir do `main` atualizado.
- [ ] 2.1.2 [Agente] Escrever `app/evaluation/datasets/dominio-v4-holdout.json` com 30 perguntas
  novas, em linguagem de usuária:
  - 8 de rastreamento, 6 de agendamento, 8 de gestação, 4 de urgência (conversacionais, sem
    primeira pessoa óbvia), 2 de prevenção e 2 de contracepção;
  - `acceptable_sources` só com arquivos de `data/source`;
  - nenhuma pergunta repetida dos datasets v2 e v3.
- [ ] 2.1.3 [Agente] Estender `tests/test_domain_dataset_v2.py`: o v4 tem 30 casos, é disjunto do
  v2 e do v3, e todas as fontes existem.
- [ ] 2.1.4 [Agente] Registrar em `docs/avaliacao-retrieval.md`: "Holdout v4 congelado em <data>,
  não executado". **Não rodar o v4 até a Etapa 6.**

### 2.2 Casos de dev para as falhas conhecidas

- [ ] 2.2.1 [Agente] Criar `app/evaluation/datasets/dominio-dev-extra.json` com 8 a 10 casos de dev
  que exercitem os mesmos fenômenos das falhas conhecidas, **com outras palavras**:
  - sinônimo coloquial → termo técnico (ex.: "tesão", "desejo sexual" → libido; "exame do toque" → preventivo);
  - periodicidade ("de quantos em quantos anos...", "com que frequência...").
- [ ] 2.2.2 [Autor] Rodar
  `docker compose exec -T api ragtest-evaluate-retrieval --dataset dominio-dev-extra --mode all`,
  salvando com o script ou com `docker compose cp` (ver 2.2.3).
- [ ] 2.2.3 [Agente] Se for preciso, adicionar ao `scripts/avaliar_dominio.ps1` um bloco opcional
  `-Extra` que roda o `dominio-dev-extra`, para o autor rodar só esse bloco.
- [ ] 2.2.4 [Agente] Analisar as falhas do dev-extra e registrar a dificuldade #41+.

### 2.3 Expansão de consulta com sinônimos (se 2.2.4 confirmar o problema)

- [ ] 2.3.1 [Agente] Escrever o teste RED `tests/test_query_expansion.py`: dicionário pequeno e
  determinístico, coloquial → termo do corpus. Só acrescenta termos à consulta **esparsa (BM25)**;
  a consulta densa fica como está.
- [ ] 2.3.2 [Agente] Implementar `app/rag/query_expansion.py`, com o dicionário em
  `data/source/servicos/sinonimos.json` ou dentro do catálogo (`sinonimos` já existe por serviço),
  e ligar em `semantic_search` só quando `sparse_embeddings` estiver presente.
- [ ] 2.3.3 [Agente] Garantir que o contrato não muda (`tests/test_contract.py` verde) e que o
  e2e continua verde.
- [ ] 2.3.4 [Autor] Rodar dev v2 + dev-extra + o critério (script com `-Extra`).
- [ ] 2.3.5 [Agente] Aceitar a mudança só se:
  - dev v2 continua ≥ 0.90 / 0.75;
  - dev-extra melhora.
  
  Se não, reverter com um novo commit (nunca com `reset`) e registrar como dificuldade. Registrar D055+.
- [ ] 2.3.6 [Ambos] PR `feature/retrieval-0.9.3` → `main`, CI verde, merge.

## Etapa 3 — Métricas operacionais (branch `feature/observabilidade-0.9.4`)

- [ ] 3.1.1 [Agente] Escrever o teste RED `tests/test_audit_report.py`: dado um arquivo com linhas
  JSON de `AuditEvent` (formato de `app/observability/audit.py`), calcular:
  - contagem por `event_type` e `outcome`;
  - taxa de `grounded`;
  - erros por `error_code`;
  - `duration_ms` p50/p95 por `operation`.
- [ ] 3.1.2 [Agente] Implementar `app/observability/report.py` e o CLI `ragtest-audit-report`, que
  lê um arquivo ou a entrada padrão e ignora linhas que não são JSON de auditoria.
- [ ] 3.1.3 [Agente] Documentar em `docs/DEPLOY.md` (Operação) o uso:
  `docker compose logs api --no-log-prefix > docs\resultados\logs_api.txt`, depois
  `python -m app.cli.audit_report docs\resultados\logs_api.txt`.
  Atenção ao UTF-16 do PowerShell: o CLI deve aceitar UTF-8 e UTF-16, com teste.
- [ ] 3.1.4 [Agente] Adicionar a `ragtest-collect-answers` as colunas `prompt_tokens` e
  `output_tokens`, quando o provider expõe `generation_metrics`. Somar por pergunta, com teste.
- [ ] 3.1.5 [Ambos] PR, CI verde e merge. Registrar D0xx.

## Etapa 4 — Adaptador LangChain (branch `feature/langchain-0.9.5`)

> Reforça a aderência à stack sugerida sem trocar o pipeline próprio (a D055 ou seguinte explica o porquê).

- [ ] 4.1.1 [Agente] Escrever o teste RED `tests/test_langchain_retriever.py`:
  `RagTestRetriever(BaseRetriever)` retorna `Document`s com `page_content` e `metadata`
  (`source`, `page`, `service_id`, `score`) a partir de `semantic_search`, usando fakes. Tem
  versão síncrona e assíncrona (`_get_relevant_documents` e `_aget_relevant_documents`).
- [ ] 4.1.2 [Agente] Implementar `app/integrations/langchain_retriever.py`, sem dependência nova
  além de `langchain-core`, que já existe.
- [ ] 4.1.3 [Agente] Adicionar um exemplo curto em `docs/INTEGRACAO.md` ("Uso como retriever
  LangChain") e uma entrada em `docs/monografia/ESQUELETO.md` (cap. 4).
- [ ] 4.1.4 [Ambos] PR, CI verde e merge. Registrar a decisão.

## Etapa 5 — Homologação (branch `feature/homologacao-1.0.0-rc`)

- [ ] 5.1.1 [Agente] Criar `scripts/smoke_test.ps1` (e `scripts/smoke_test.sh`) com os parâmetros
  `-BaseUrl` e `-ApiKey`. O script testa:
  - `/health` = 200 e `/ready` = `ready`;
  - `/v1/services` = 200 com a chave e 401 sem ela;
  - `/v1/suggestions`;
  - `/v1/chat` com uma pergunta de domínio (`display.status` em `verified` ou `unverified`);
  - `/v1/chat` com uma de urgência (`emergency`, sem LLM);
  - `/v1/chat` com uma fora de escopo.
  
  Grava em `docs/resultados/smoke_<data>.txt` em UTF-8 e sai com código 1 em qualquer falha.
- [ ] 5.1.2 [Autor] Validar a sobreposição de produção localmente:
  `docker compose -f docker-compose.yml -f docker-compose.prod.yml config > $null`. Precisa de
  Docker Compose 2.24 ou mais novo por causa do `!reset`. Se der erro, copiar a mensagem e chamar
  o agente.
- [ ] 5.1.3 [Autor] Smoke test local, com `API_KEYS` definido no `.env`:
  `powershell -ExecutionPolicy Bypass -File scripts/smoke_test.ps1 -BaseUrl http://localhost:8000 -ApiKey <chave>`.
- [ ] 5.1.4 [Autor] Decidir o local da homologação:
  - **(a)** servidor com domínio, seguindo o `docs/DEPLOY.md`;
  - **(b)** homologação local documentada, se não houver servidor. Nesse caso, registrar a decisão
    e o aval do orientador no `ESTADO_ATUAL.md` §0.
- [ ] 5.1.5 [Autor, se (a)] Fazer o deploy conforme o `docs/DEPLOY.md` e rodar o smoke test contra
  `https://<domínio>`.
- [ ] 5.1.6 [Agente] Registrar o resultado do smoke test e a URL (sem chave) no `ESTADO_ATUAL.md`
  e no `docs/DEPLOY.md`. Plano §6: F6 ✅.
- [ ] 5.1.7 [Ambos] PR, CI verde e merge.

## Etapa 6 — Avaliação final congelada

- [ ] 6.1.1 [Agente] Adicionar ao `scripts/avaliar_dominio.ps1` o bloco `-Final`:
  - dev v2 (critério);
  - dev-extra;
  - holdout v4 `--mode all`, **uma vez**;
  - calibração.
- [ ] 6.1.2 [Autor] Rodar `powershell -ExecutionPolicy Bypass -File scripts/avaliar_dominio.ps1 -Final`.
- [ ] 6.1.3 [Agente] Registrar a tabela final (dense × dense-rerank × hybrid no holdout v4) em
  `docs/avaliacao-retrieval.md` como **resultado oficial da monografia**. Não ajustar nada depois.
- [ ] 6.1.4 [Autor] Coleta final de respostas (`ragtest-collect-answers`, gravando em
  `respostas_final.csv`), **só se** a geração mudou desde a coleta 2. Se mudou, repetir a rubrica
  (1.3.1 e 1.3.2).
- [ ] 6.1.5 [Agente] Consolidar em `docs/resultados/RESUMO_FINAL.md`:
  - retrieval final;
  - respostas;
  - triagem;
  - recusas;
  - latência sem 429;
  - tokens por pergunta.

## Etapa 7 — Validação com usuárias (recomendada; depende do orientador)

- [ ] 7.1.1 [Agente] Criar `docs/usabilidade/ROTEIRO.md` com:
  - objetivo;
  - perfil (5 a 8 mulheres, 18+);
  - 6 tarefas (preventivo, mamografia, pré-natal, urgência, lembrete, pergunta fora do tema);
  - métricas (sucesso, tempo, SUS);
  - roteiro do moderador;
  - cuidados de privacidade: sem dados de saúde reais, sem gravar voz sem consentimento.
- [ ] 7.1.2 [Agente] Criar `docs/usabilidade/SUS_ptbr.md` (10 itens, escala 1–5, cálculo) e o
  **modelo** de TCLE em `docs/usabilidade/TCLE_modelo.md`, marcado como "a validar com o orientador
  e o comitê, se exigido".
- [ ] 7.1.3 [Agente] Criar `docs/usabilidade/planilha_modelo.csv` (participante, tarefa, sucesso,
  tempo_s, SUS_1..10) e estender o `ragtest-summarize-answers`, ou um CLI novo, para calcular o SUS. TDD.
- [ ] 7.1.4 [Autor] Levar o roteiro e o TCLE ao orientador e registrar a decisão (fazer ou não, com
  ou sem comitê) no `ESTADO_ATUAL.md` §0.
- [ ] 7.1.5 [Autor] Fazer as sessões com o cliente de referência Expo
  (`cd frontend && npm install && npm run web`, com a API local) e preencher a planilha em
  `docs/resultados/usabilidade.csv`, sem nomes.
- [ ] 7.1.6 [Agente] Calcular o SUS e as taxas de sucesso e registrar em `docs/usabilidade/RESULTADOS.md`.
- [ ] 7.1.7 [Agente, se 7.1.4 = não fazer] Registrar a justificativa e mover o tema para
  "Trabalhos futuros" na monografia.

## Etapa 8 — Pronto para integração

- [ ] 8.1.1 [Agente] Em `docs/INTEGRACAO.md`, incluir:
  - exemplo completo em TypeScript (fetch com `X-API-Key`, sessão, render de `display` e `actions`);
  - exemplo em Dart/Flutter (`http` com `utf8.decode(response.bodyBytes)`, por causa da D049);
  - geração do cliente Dart com `openapi-generator`.
- [ ] 8.1.2 [Agente] Criar `docs/CHECKLIST_INTEGRACAO.md` para o time do Se Cuida Mulher:
  - chave por ambiente;
  - mapeamento de `seucuida://unidades` para a tela de Unidades;
  - notificação local para `schedule_reminder`;
  - discador para `call_emergency`;
  - tratamento de 401, 409, 410, 429 e 503;
  - troca do catálogo pelos dados reais do município.
- [ ] 8.1.3 [Agente] Criar o `CHANGELOG.md` do 0.5.x ao 1.0.0 a partir de
  `docs/historico/README_ate_0.7.0.md`, dos PRs #19–#24 e das decisões D001–D0xx.
- [ ] 8.1.4 [Ambos] PR, CI verde e merge.

## Etapa 9 — Monografia (`docs/monografia/`)

### 9.1 Figuras

- [ ] 9.1.1 [Agente] `docs/monografia/figuras/arquitetura.mmd`: diagrama Mermaid dos componentes
  (cliente → FastAPI → triagem → retrieval hybrid → LLM → gate → ações → auditoria; Qdrant; SQLite).
- [ ] 9.1.2 [Agente] `docs/monografia/figuras/fluxo_chat.mmd`: sequência do `/v1/chat`, com os
  caminhos urgência, fora de escopo, verificado e fallback.
- [ ] 9.1.3 [Agente] `docs/monografia/figuras/pipeline_ingestao.mmd`: loaders, OCR, chunking com
  contexto (D047), embeddings, sync incremental.
- [ ] 9.1.4 [Autor] Exportar as figuras para PNG (mermaid.live ou extensão do VS Code) para o
  documento final.

### 9.2 Capítulos (rascunho do agente; revisão e ABNT pelo autor)

- [ ] 9.2.1 [Agente] `capitulos/01-introducao.md`: problema, objetivos (proposta do orientador),
  justificativa, contribuição.
- [ ] 9.2.2 [Agente] `capitulos/02-fundamentacao.md`: RAG, embeddings, BM25, RRF, alucinação,
  métricas (HitRate, MRR, NDCG, SUS), letramento em saúde. As referências bibliográficas ficam
  marcadas `[REF: ...]` para o autor completar.
- [ ] 9.2.3 [Agente] `capitulos/03-metodologia.md`: processo (TDD, CI, decisões e dificuldades),
  corpus e privacidade (D038), datasets dev/holdout (v1–v4) e a regra de não ajustar em holdout,
  rubrica, usabilidade.
- [ ] 9.2.4 [Agente] `capitulos/04-arquitetura.md`: componentes, padrões de projeto (Factory,
  Strategy, Repository, Adapter, Middleware), contrato headless, segurança. Citar as decisões pelo número.
- [ ] 9.2.5 [Agente] `capitulos/05-resultados.md`: tabelas do `RESUMO_FINAL.md`, casos qualitativos
  (mamografia antes e depois; recusa com citação falsa), SUS.
- [ ] 9.2.6 [Agente] `capitulos/06-discussao.md`: lições das dificuldades #34, #35, #36, #38, #40;
  limitações; trabalhos futuros.
- [ ] 9.2.7 [Agente] `capitulos/07-conclusao.md`.
- [ ] 9.2.8 [Autor] Revisar, completar as referências `[REF]` e formatar em ABNT no editor final
  (Word ou LaTeX).
- [ ] 9.2.9 [Autor] Enviar ao orientador e registrar o retorno em `docs/monografia/REVISOES.md`.
- [ ] 9.2.10 [Agente] Aplicar as correções técnicas pedidas pelo orientador que envolvam código,
  resultados ou texto técnico.

## Etapa 10 — Entrega v1.0.0

- [ ] 10.1.1 [Agente] Criar a branch `release/1.0.0` e fazer o bump para `1.0.0` em:
  - `pyproject.toml`;
  - `app/core/config.py` (`app_version`);
  - `tests/test_session_config.py`;
  - `frontend/package.json` e `frontend/app.json`.
  
  Depois regenerar o contrato (o `info.version` fica "v1", sem diff esperado).
- [ ] 10.1.2 [Agente] Atualizar o `README.md` **de forma incremental**, preservando o texto de
  portfólio do autor (`9712362`): status 1.0.0, links para `INTEGRACAO`, `DEPLOY`, `RESUMO_FINAL` e a monografia.
- [ ] 10.1.3 [Agente] Criar `docs/APRESENTACAO.md` com:
  - roteiro de 10 a 15 minutos (problema, arquitetura, demo, resultados, lições);
  - script da demo (pergunta verificada, urgência, fora de escopo, lembrete, sessão);
  - plano B se o provider cair (usar `docs/resultados/` e vídeo gravado).
- [ ] 10.1.4 [Autor] Gravar um vídeo curto da demo, como plano B.
- [ ] 10.1.5 [Ambos] PR `release/1.0.0` → `main`, CI verde e merge.
- [ ] 10.1.6 [Autor] Criar a tag e a release:
  `git tag -a v1.0.0 -m "RagTest 1.0.0"` e `git push origin v1.0.0`. Criar a Release no GitHub
  com o resumo do `CHANGELOG.md`.
- [ ] 10.1.7 [Agente] Encerramento:
  - `ESTADO_ATUAL.md` com "Projeto concluído em <data>";
  - plano §6 todo em ✅;
  - este roteiro com todos os itens marcados.

---

## Apêndice — Riscos e o que fazer

| Risco | Ação |
|---|---|
| Cota do Groq estourando (429) | Usar `--pause-seconds` maior, rodar em outro horário ou trocar `LLM_PROVIDER=gemini` no `.env` (mesmo contrato). |
| Conflito com o README do autor | Parar, mostrar o diff ao autor e integrar à mão, sem sobrescrever. |
| CI vermelha só na CI | Suspeitar de dependência do ambiente (#38). Reproduzir num ambiente limpo (venv novo, sem `.env`). |
| Mudança que piora o dev | Reverter com um commit novo e registrar a dificuldade. Nunca "ajustar até passar" usando holdout. |
| Orientador pedir outra stack ou recurso | Registrar no `ESTADO_ATUAL.md` §0, criar uma etapa nova aqui antes de implementar. |
| Tempo curto | Ordem de corte: Etapa 4 → Etapa 7 (vira trabalho futuro) → 3.1.4 → 2.3. **Não cortar** 1, 5, 6, 9 e 10. |
