# Plano de Finalização — RagTest / Módulo RAG "Se Cuida Mulher"

> Análise feita em 28/09/2026 sobre o GitHub (`Daniel-SLima/RagTest`) e sobre a pasta local `00-RagTest`.
> Objetivo: terminar o TCC sem perder a lógica da proposta do professor, com o menor retrabalho possível.

---

## 1. Veredito (resumo)

**Não refaça o projeto.** A base está correta e, em várias partes, vai além do que a proposta pede
(retrieval avaliado com métricas, guardrails de citação, sessões, auditoria, CI, Docker, 149 testes verdes
no `main`). Refazer jogaria fora ~382 commits e um histórico de decisões/dificuldades que é **material
pronto para a monografia**.

O problema real não é a arquitetura — é **direção**:

1. **Engenharia demais em infraestrutura, pouco no domínio.** Nas últimas versões o esforço foi em
   hardening (auditoria 0.7.0-A com 18 commits, request-id, sanitização de erros), enquanto o núcleo do
   problema do professor — **Papanicolau, mamografia e agendamento** — **não aparece em nenhum caso de
   avaliação** e quase não aparece no corpus.
2. **O conteúdo mais importante está bloqueado.** Os arquivos `chatscm/*.docx` são o FAQ do próprio
   Se Cuida Mulher (idade do preventivo 25–64, mamografia 40–74, "como agendo o pré-natal", sinais de
   urgência). Eles estão proibidos de ir para LLM externo "até revisão manual de privacidade" — revisão
   que nunca foi feita. Pelo conteúdo, é um FAQ institucional sem dados pessoais.
3. **Faltam 2 entregas explícitas da proposta:** *links de redirecionamento* e *gatilhos de agendamento
   de lembretes*.
4. **Processo pesado para um TCC solo:** fluxo obrigatório de 6 agentes, `CONTEXTO_CONTINUIDADE.md` com
   2.513 linhas, 24 branches remotas, uma sidequest de demo (~6.000 linhas) órfã, README com histórico
   de fases misturado com documentação de uso.

**Estratégia:** congelar hardening → consolidar o repositório → virar o foco para o domínio
(saúde da mulher + agendamento) → fechar os entregáveis que faltam → medir → escrever.

---

## 2. Estado atual

### 2.1 Git: local × GitHub

| Item | Situação |
|---|---|
| `origin/main` (GitHub) | `f173a29` — versão **0.6.0** (sessões). 149 testes passando, Ruff limpo (verifiquei rodando). |
| Branch local atual | `feature/audit-0.7.0` — **18 commits à frente do remoto, sem push** (auditoria 0.7.0-A, Tasks 1–7 + fix). |
| "132 arquivos modificados" no local | **Não são mudanças reais.** `git diff --ignore-cr-at-eol` fica vazio: é só conversão de fim de linha (CRLF do Windows). Falta um `.gitattributes`. |
| `sidequest/ragtest-demo` | Existe local e remoto, sincronizada. App de demonstração (laboratório, roadmap, endpoint `/demo`), **não mesclada** e não ancestral da auditoria. |
| Branches | 24 remotas, a maioria de features já mescladas (0.5.7 → 0.5.24). |
| `.git/index.lock` | Existe um lock preso na pasta local — apague-o (com o Git fechado) antes do próximo commit. |
| Segredos | `.env` está no `.gitignore` e não está versionado. OK. |

### 2.2 Cobertura da proposta do professor

| Objetivo da proposta | Situação | Evidência / lacuna |
|---|---|---|
| **Pipeline de ingestão** (extração, limpeza, chunking, vetorização) | ✅ Forte | PDF + OCR seletivo (Tesseract), DOCX, chunking LangChain, FastEmbed multilíngue, Qdrant, sync incremental, auditoria de corpus. |
| Cartilhas SUS | ✅ | 17 PDFs oficiais. |
| Bulários | ⚠️ Parcial | Só RENAME 2024 (lista, não bula). |
| **Fluxogramas locais de atendimento** | ❌ | Nada sobre UBS, horários, onde/como agendar (exceto o que está no CHATSCM bloqueado). |
| Diretrizes de rastreamento (colo do útero / mama) | ❌ | Nenhum documento do INCA/MS sobre rastreamento. |
| **Retrieval** + validação de hit rate | ✅ Forte, mas fora do domínio | dense-rerank, hybrid, multi-query, decomposição, HitRate/MRR/SourceRecall/NDCG, dev + holdout. Porém os 22 casos são sobre vacinas, DIU, insulina, direitos — **zero sobre preventivo/mamografia/agendamento**. |
| **Mitigação de alucinação** | ✅ Forte | Gate de cobertura de citações, repair direcionado, poda determinística, fallback seguro, defesa contra prompt injection. |
| Segurança clínica (urgência) | ❌ | O CHATSCM tem regras "vá à maternidade/UPA"; não existe triagem determinística de sinais de alarme antes do LLM. |
| **Logs de auditoria estruturados** | ✅ (local) | 0.7.0-A implementada, **sem push**. |
| **Interface de chat** fluida/responsiva | ⚠️ Básica | Expo (web/mobile), rich-text Markdown, fontes citadas, estados de grounding, retry. |
| Links de redirecionamento | ❌ | |
| Gatilhos de agendamento de lembretes | ❌ | Só registrado como "ação estruturada futura". |
| **Stack sugerida** | ✅ | FastAPI, Qdrant, LangChain (uso mínimo), Expo/React Native, REST, Docker Compose. |
| Testes automatizados | ✅ | 149 (main) / 233 (local) backend + Jest/RNTL + CI em 3 jobs. |
| Métricas de desempenho para a monografia | ⚠️ | Existem para retrieval; faltam métricas de **resposta** (fidelidade, relevância), latência p50/p95, custo, e usabilidade. |

---

## 3. Continuar × Refazer

| Critério | Continuar (recomendado) | Refazer do zero |
|---|---|---|
| Tempo até ter algo defensável | 1–2 semanas | 4–6 semanas só para voltar ao ponto atual |
| Risco | Baixo (base testada) | Alto (reintroduz bugs já resolvidos: OCR, Cloudflare 1010, citações Unicode, etc.) |
| Material para monografia | 37 decisões + 32 dificuldades documentadas | Perdido ou reescrito |
| Aderência ao professor | Precisa virar o foco para o domínio | Mesmo trabalho de domínio, mais o custo da reconstrução |

**Único cenário em que refazer faria sentido:** se o professor exigisse LlamaIndex ou WebSockets como
obrigatórios. Nenhum dos dois é obrigatório ("ou"/"sugerida"). O uso de LangChain (PromptTemplate +
TextSplitter) atende a sugestão; a escolha de **não** usar chains completas é uma decisão arquitetural
justificável (controle do gate de citações, testabilidade) e deve virar a decisão D038 na monografia.

**Se quiser "refazer da forma correta" sem jogar código fora:** faça as fases 0 e 1 abaixo. Elas
reorganizam o repositório e o foco — é o "refazer" de que o projeto precisa.

---

## 4. Plano de execução (≈ 8 semanas)

Cada fase tem **Entregáveis** e **Pronto quando**. Mantenha TDD nas mudanças de código, mas sem o fluxo
completo de 6 agentes para mudanças pequenas.

### Fase 0 — Consolidar o repositório (1–2 dias)

1. Apagar `.git/index.lock` (com o Git fechado).
2. Criar `.gitattributes` para acabar com o ruído de CRLF:
   ```
   * text=auto eol=lf
   *.pdf binary
   *.docx binary
   ```
   Depois rodar `git add --renormalize .` e commitar só isso.
3. Push de `feature/audit-0.7.0` → PR → CI verde → merge no `main` → tag `v0.7.0`.
4. Sidequest de demo: **não mesclar agora**. Criar a tag `archive/ragtest-demo` e deixá-la parada.
   Reaproveitar peças (painel de diagnóstico do pipeline) só na Fase 5, se sobrar tempo para a defesa.
5. Criar tags das features antigas já mescladas e apagar as branches remotas (fica só o `main` + a feature ativa).
6. Enxugar a documentação:
   - `README.md` → só: o que é, arquitetura (diagrama), como rodar, endpoints, métricas atuais, limitações.
     O histórico por versão vai para `docs/historico/CHANGELOG.md`.
   - `CONTEXTO_CONTINUIDADE.md` → no máximo 150 linhas (estado atual + próximos passos). O resto vai para
     `docs/historico/`.
   - Manter `decisoes-tecnicas.md` e `dificuldades-tcc.md` (são capítulos da monografia).
7. Simplificar o `AGENTS.md`: fluxo completo só para mudanças de contrato/segurança; para o resto,
   desenvolvedor + QA.

**Pronto quando:** `main` = 0.7.0, `git status` limpo, README com menos de 250 linhas, 2 branches ativas.

### Fase 1 — Virar o foco para o domínio: corpus (semana 1)

1. **Liberar o CHATSCM** com uma revisão de privacidade documentada (1 hora):
   - checklist: nomes próprios, CPF, telefones, endereços residenciais, datas de nascimento, casos clínicos individuais;
   - script `ragtest-audit-pii` (regex para CPF/telefone/e-mail + lista de nomes) sobre os 3 DOCX;
   - registrar a decisão **D038 — CHATSCM revisado e liberado** com a saída do script.
2. **Adicionar as fontes oficiais que faltam** (`data/source/rastreamento/`):
   - INCA — *Diretrizes Brasileiras para o Rastreamento do Câncer do Colo do Útero*;
   - INCA/MS — *Diretrizes para a Detecção Precoce do Câncer de Mama*;
   - MS — *Caderno de Atenção Básica nº 13 (Controle dos cânceres do colo do útero e da mama)*;
   - material do MS sobre o **exame preventivo** voltado à usuária (linguagem simples).
3. **Criar o "fluxograma local" como dado estruturado** (não PDF), p.ex. `data/services/servicos.yaml`:
   ```yaml
   - id: preventivo
     nome: Exame preventivo (Papanicolau)
     publico: mulheres de 25 a 64 anos
     periodicidade: 1ª vez, repetir em 1 ano, depois a cada 3 anos se normais
     onde: UBS/USF de referência
     como_agendar: recepção da UBS; levar Cartão SUS e documento com foto
     preparo: não usar duchas/cremes vaginais 48h antes; evitar relação sexual 48h antes
     link: seucuida://unidades           # link simbólico; o integrador resolve
     lembrete_padrao_dias: 1095
     fonte: INCA 2016
   - id: mamografia
     ...
   - id: prenatal
     ...
   ```
   Isso vira: (a) chunks indexados, com metadado `doc_type=servico`; (b) a fonte das **ações** da Fase 4.
   Use UBS **fictícias** ou públicas (sem dados pessoais) e deixe claro na monografia que é um ambiente simulado.
4. Metadados: acrescentar `audience=mulher` e `topic` (rastreamento, gestacao, contracepcao, direitos...).
5. Ingestão incremental com `ragtest-plan-ingestion-sync` → `ragtest-sync-ingestion` (sem `--recreate`).
6. **Opcional — reduzir o escopo do corpus:** se as respostas começarem a puxar insulina, idoso ou criança
   para perguntas de mulheres, mova esses documentos para `data/source/_fora_escopo/`. A proposta é
   saúde da mulher; um corpus focado melhora a precisão e simplifica a defesa.

**Pronto quando:** as perguntas "com que idade faço o preventivo?", "como agendo mamografia?" e
"estou grávida, e agora?" retornam fontes corretas no top 3.

### Fase 2 — Avaliação no domínio (semana 2)

1. **Dataset v2** (`2026-10-v2`) com cerca de 40 perguntas, escritas como a usuária escreveria
   (erros de digitação, "papanicolau", "exame de toque", "exame da mama", "tô grávida"):
   - 15 de rastreamento (preventivo/mamografia), 10 de agendamento/acesso, 8 de gestação,
     4 de urgência, 3 fora de escopo;
   - separar dev (15) e holdout congelado (25), como já é feito.
2. Métricas de **retrieval** (já existentes): HitRate@k, MRR, SourceRecall, NDCG — por tópico.
3. Métricas de **resposta** (novas):
   - `grounded_rate`, `fallback_rate`, `retry_rate` (já estão disponíveis no ChatResult);
   - **fidelidade (faithfulness)** e **relevância da resposta**: RAGAS com LLM juiz, **ou** rubrica
     manual 0–2 aplicada por você + 1 colega sobre 25 respostas (calcule a concordância com kappa de
     Cohen). A rubrica manual é mais barata e defensável;
   - taxa de acerto da **triagem de urgência** e da **recusa fora de escopo** (Fase 3).
4. **Desempenho:** latência p50/p95 por provider (Groq, Gemini, Ollama) e tokens por resposta.
5. Script `ragtest-report` que gera `docs/resultados/AAAA-MM-DD.md` com todas as tabelas (vai direto para a monografia).

**Pronto quando:** existe uma tabela de baseline reproduzível, com um comando.

### Fase 3 — Segurança de domínio (semanas 3–4)

Camadas **antes** do LLM, determinísticas e testáveis:

1. **Triagem de sinais de alarme** (`app/safety/triage.py`): lista de padrões vinda do CHATSCM
   (sangramento, pressão alta, dor de cabeça forte, visão embaçada, "estrelinhas", perda de líquido,
   ausência de movimento do bebê, convulsão). Se casar: resposta **fixa** de urgência
   (maternidade/UPA/SAMU 192) + ação `call_emergency`, **sem chamar o LLM**. Casos com e sem gestação.
2. **Fora de escopo:** se o melhor score do retrieval ficar abaixo do limiar calibrado no dataset v2,
   responder com uma mensagem padrão ("não encontrei nas cartilhas...") + sugestão de procurar a UBS.
3. **Não-diagnóstico:** detectar pedidos de diagnóstico/prescrição ("que remédio tomo", "é câncer?")
   → resposta de orientação para o profissional de saúde.
4. **Minimização de dados pessoais** na entrada: mascarar CPF, telefone e e-mail antes de enviar ao provider
   (a auditoria 0.7.0 já não registra conteúdo).
5. **Autenticação simples para o integrador:** header `X-API-Key` (uma chave por cliente, via `.env`) + rate limit por chave.
6. Adicionar na resposta os campos `safety: {triaged, out_of_scope, disclaimer}`.

**Pronto quando:** 100% dos casos de urgência do dataset são triados sem LLM, e os casos fora de escopo são recusados.

### Fase 4 — Ações estruturadas: links e lembretes (semanas 4–5)

Mantém a decisão já tomada: **o backend sugere, o app integrador executa.**

1. Novo campo no contrato de `POST /v1/chat`:
   ```json
   "actions": [
     {"type": "open_link",        "label": "Ver unidades de saúde", "url": "seucuida://unidades"},
     {"type": "schedule_reminder","label": "Lembrar do preventivo",  "service_id": "preventivo",
      "suggested_in_days": 1095, "title": "Exame preventivo"},
     {"type": "call_emergency",   "label": "Ligar 192", "phone": "192"}
   ]
   ```
2. **Quem decide as ações:** regras determinísticas, não o LLM. Classificador de intenção leve
   (palavras-chave + similaridade com os `servicos.yaml`) → `service_id` → ações do catálogo.
   Só entra ação se o serviço também aparecer nas fontes recuperadas (coerência com o grounding).
3. `GET /v1/services` e `GET /v1/services/{id}` expõem o catálogo (útil para o Se Cuida Mulher).
4. Evento de auditoria `chat.actions_suggested` (só tipos/ids, sem conteúdo).
5. Testes: contrato, mapeamento intenção → serviço, "sem ação quando o grounding falha".

**Pronto quando:** "quero marcar o preventivo" devolve a resposta citada + `open_link` + `schedule_reminder`.

### Fase 5 — Interface (semanas 5–6)

No Expo existente (sem reescrever):

1. **Chips de ação** abaixo da resposta, renderizados a partir de `actions`.
2. **Lembretes reais** com `expo-notifications` (notificação local agendada) + tela "Meus lembretes"
   (AsyncStorage). No web, fallback para arquivo `.ics`.
3. **Links**: `Linking.openURL`; os links `seucuida://` mostram um aviso "disponível no app integrado".
4. Cartão de **urgência** destacado (vermelho, botão 192) quando `safety.triaged=true`.
5. Sugestões iniciais ("Quando fazer o preventivo?", "Como agendar mamografia?", "Estou grávida").
6. Acessibilidade: tamanho de fonte, contraste AA, `accessibilityLabel` e linguagem simples.
7. (Opcional) streaming via SSE para melhorar a latência percebida; o REST continua como padrão.
8. (Opcional, para a defesa) reaproveitar da sidequest o painel "como funciona" (etapas do pipeline).

**Pronto quando:** o fluxo "pergunta → resposta citada → criar lembrete → notificação" funciona no Android (Expo Go) e na web.

### Fase 6 — Pronto para integrar no Se Cuida Mulher (semana 7)

1. `docs/INTEGRACAO.md`: contrato OpenAPI (`/docs`), autenticação, sessões, ações, códigos de erro,
   exemplo em React Native **e** Flutter (o app real pode ser qualquer um dos dois).
2. Pacote cliente TypeScript (`frontend/src/lib/chat-api.ts` extraído) para copiar para o app.
3. `docker-compose.prod.yml` + deploy de **homologação** (VPS/Render/Railway) com HTTPS, para o professor testar.
4. Script de resumo dos logs de auditoria → métricas operacionais (volume, grounded %, erros por provider).
5. Tag `v1.0.0`.

**Pronto quando:** alguém de fora consegue integrar lendo só o `INTEGRACAO.md`.

### Fase 7 — Validação com usuárias e monografia (semanas 7–8, em paralelo)

1. **Teste de usabilidade** com 5–8 mulheres (roteiro de 6 tarefas: preventivo, mamografia, pré-natal,
   urgência, lembrete, pergunta fora de escopo) + questionário **SUS (System Usability Scale)** +
   tempo por tarefa. Use o TCLE/termo que o professor indicar e não colete dados de saúde reais.
2. Rodar o `ragtest-report` final (retrieval + resposta + desempenho + segurança).
3. Monografia — mapeamento direto do que já existe:

| Capítulo | Fonte no repositório |
|---|---|
| Introdução / problema | Proposta do professor |
| Fundamentação (RAG, embeddings, busca híbrida, RRF, alucinação) | `decisoes-tecnicas.md` D002–D012 |
| Arquitetura e padrões | Diagrama + Factory (LLM/embeddings), Strategy (perfis de retrieval), Repository (sessões), Adapter (providers) |
| Pipeline de dados | Ingestão, OCR, auditoria de corpus (dificuldades 1–8) |
| Guardrails | Dificuldades 11–26, D018–D023 + Fase 3 |
| Resultados | Relatórios da Fase 2/7 |
| Lições aprendidas | `dificuldades-tcc.md` (32+ casos — ótimo diferencial) |
| Limitações e trabalhos futuros | Integração real no app, juiz semântico, ambiente de produção/LGPD |

---

## 5. O que parar de fazer

- Novas camadas de hardening/auditoria antes de fechar o domínio (a 0.7.0-A já basta para o TCC).
- Versões de patch para cada ajuste (0.5.7 → 0.5.24 em poucos dias). Use uma versão por fase: 0.8 (domínio), 0.9 (segurança + ações), 1.0 (UI + integração).
- Documentar cada micro-passo no `CONTEXTO_CONTINUIDADE.md`. Registre só decisões (D0xx) e dificuldades reais.
- Novos providers ou modos de retrieval. Três providers e três modos já são suficientes para comparação.

---

## 6. Cronograma

| Semana | Fase | Versão |
|---|---|---|
| 0 (2 dias) | F0 Consolidar | 0.7.0 |
| 1 | F1 Corpus de domínio | 0.8.0 |
| 2 | F2 Avaliação v2 (baseline) | 0.8.x |
| 3–4 | F3 Segurança de domínio | 0.9.0 |
| 4–5 | F4 Ações (links/lembretes) | 0.9.x |
| 5–6 | F5 Interface | 0.10.0 |
| 7 | F6 Integração + homologação | 1.0.0 |
| 7–8 | F7 Usabilidade + monografia | — |

Se o prazo apertar, a ordem de corte é: F5 itens 7–8 → F6 item 3 (deploy) → F2 RAGAS (fica só a rubrica manual).
**Não corte** F1, F3 item 1 (urgência) nem F4 — são exatamente o que o professor pediu.

---

## 7. Riscos

| Risco | Mitigação |
|---|---|
| Cota/instabilidade dos providers (Gemini 429/503) | Groq como padrão de desenvolvimento, Ollama como contingência, retry já existente. |
| Dados de UBS reais indisponíveis | Catálogo simulado, declarado como tal; o formato YAML permite trocar pelos dados reais na integração. |
| Resposta clínica incorreta | Grounding obrigatório + triagem determinística + disclaimer; não prometer diagnóstico. |
| Sem acesso ao Se Cuida Mulher | Contrato + guia de integração + cliente TS; a validação é "ambiente simulado/homologado", como a proposta permite. |
| Retrabalho por excesso de processo | Fluxo leve (seção 5). |

---

## 8. Próximas 5 ações (hoje)

1. Apagar `.git/index.lock`, criar `.gitattributes`, rodar `git add --renormalize .` e commitar.
2. Push de `feature/audit-0.7.0`, abrir o PR, esperar a CI e fazer o merge.
3. Rodar o checklist de privacidade no CHATSCM e registrar a D038.
4. Baixar as 3 diretrizes do INCA/MS de rastreamento para `data/source/rastreamento/`.
5. Rascunhar `data/services/servicos.yaml` com preventivo, mamografia e pré-natal.
