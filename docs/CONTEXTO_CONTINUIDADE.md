# Contexto de Continuidade do Projeto — RagTest / Se Cuida Mulher

> **Documento vivo de continuidade.**
>
> Este arquivo existe para permitir que o desenvolvimento continue em outro chat sem perda de contexto.
> **Sempre que houver mudança relevante de código, arquitetura, testes, métricas, decisões, dificuldades ou próximos passos, este arquivo deve ser atualizado antes de encerrar a tarefa.**
>
> Em um novo chat, antes de continuar o projeto, leia este arquivo e depois confira o estado atual do repositório/branch/PR.


## HANDOFF AUTORITATIVO ATUAL — 2026-09-22 ESTADO LOCAL E INFRAESTRUTURA MULTIAGENTE

> **Esta seção prevalece sobre qualquer trecho histórico conflitante existente abaixo.**
> O restante do arquivo preserva o histórico do projeto e pode mencionar branches, PRs e versões anteriores.

### Estado exato do repositório

- Repositório: `Daniel-SLima/RagTest`
- Branch padrão: `main`
- Versão integrada e validada no `origin/main` remoto: **0.5.24**
- Versão integrada e validada na `main` local: **0.6.0**, commit `f173a29`
- PR #19: **merged**
- Merge commit da 0.5.24: `28edf6a51bf29a4aa62ff56a74efbffb640e728f`
- Head final da feature antes do merge: `534e1c5334424a57e7cd0adb56f6ea763c20b4ec`
- CI final pré-merge: run `35677374957`, com `lint`, backend `test` e frontend tests/typecheck em `success`
- CI pós-merge em `main`: run `35677503800`, com os três jobs em `success`
- Runtime local Expo Web da 0.5.24: **verificado para grounding e retry manual**
- Corpus, embeddings e Qdrant: **inalterados**
- O `origin/main` remoto permanece em `4badc96`; o workspace local está deliberadamente à frente.
- Branch atual: `feature/audit-0.7.0`.
- HEAD local: `eb17d28`, contendo a especificação da auditoria estruturada 0.7.0-A; a implementação
  funcional da auditoria está pausada.
- Não existe branch remota nem PR correspondente a `feature/audit-0.7.0`.
- A arquitetura da **0.6.0 — sessões conversacionais portáveis** foi aprovada em conversa.
- A consolidação escrita está em `docs/superpowers/specs/2026-09-21-sessoes-conversacionais-0.6.0-design.md` e foi aprovada pelo usuário em 2026-09-22.
- O plano TDD foi executado de forma nativa nesta branch.
- As Tasks 1–7 da 0.6.0 estão implementadas e integradas na `main` local; a coleta atual contém
  149 testes e a suíte local passa integralmente.
- A configuração multiagente foi criada, tecnicamente revisada e versionada nesta branch por este
  commit: `AGENTS.md`, `.codex/config.toml` e `.codex/agents/*.toml`.
- `.codex/config.toml` não define `model` nem `model_reasoning_effort` no nível do projeto: o modelo
  principal continua sendo determinado pela sessão do Codex. Cada agente personalizado possui seu
  próprio modelo/esforço explícitos; todos usam exclusivamente `gpt-5.6-luna`; não há default
  implícito de subagente.
- A referência anterior a **150 testes** foi uma contagem incorreta: a execução oficial atual e a
  coleta explícita retornam **149**. Uma revalidação leve do QA chegou a relatar 147 por erro de
  soma/transcrição; a saída por arquivo foi conferida e totaliza 149, incluindo os 2 testes de
  `test_vector_store.py`. Não há diff em `tests/`, marcadores skip/xfail, seletores de exclusão ou
  teste removido/desabilitado.
- O QA foi executado como subagente real em `workspace-write`, sem alterar código, testes,
  documentação, corpus, Qdrant ou dependências e sem deixar artefatos: backend pytest **149 passed**,
  Ruff **All checks passed**, frontend Jest **13 passed** e TypeScript **passou**.
- A mudança de QA para `workspace-write` é deliberada para permitir caches/artefatos transitórios de
  ferramentas. Uma sondagem posterior com `read-only` não retornou dentro do intervalo de observação
  e foi interrompida, sem produzir erro de permissão diagnosticável; por isso não tratamos read-only
  como gate confiável para esta suíte. `AGENTS.md` e `qa.toml` proíbem alterar código de produção,
  testes ou documentação para fazer uma validação passar.
- Branch histórica da feature: `feature/ux-grounding-0.5.24`, preservada após o merge.

### O que a 0.5.24 entregou

- três estados explícitos de grounding na interface;
- separação entre fontes citadas e fontes apenas recuperadas;
- mensagem amigável específica para HTTP 503 sem exposição do detalhe técnico do provider;
- retry manual da última pergunta, sem chamadas automáticas;
- auto-scroll do histórico para manter loading, respostas e erros visíveis;
- validação visual de `grounded=true` e do retry em viewport baixa;
- contrato público `POST /v1/chat` preservado;
- backend RAG continuou desacoplado do frontend;
- `GET /health` validado com versão `0.5.24`;
- `GET /ready` validado com Qdrant `ok`;
- `POST /v1/chat` validado em runtime real;
- retrieval sem filtros da pergunta de vacinação para idosos retornou fonte oficial, sem `chatscm/`.

### Direção oficial consolidada

- O produto principal é o módulo RAG portável e integrável; o Expo é somente cliente demonstrativo.
- Funcionalidade, qualidade de retrieval, respostas, segurança, auditoria e capacidade de integração têm prioridade sobre estilização.
- Providers de LLM devem continuar intercambiáveis pela abstração existente, sem afetar API, sessões ou clientes.
- Gatilhos futuros de agendamento e lembretes devem ser ações estruturadas neutras, executadas pelo sistema integrador.

### Próximo passo exato

1. **Fase A:** sincronizar a `main` local 0.6.0 (`f173a29`) com `origin/main` 0.5.24 (`4badc96`),
   preferencialmente por fast-forward; se houver proteção de branch, abrir uma branch/PR exclusiva
   para essa sincronização;
2. **Fase B:** publicar `feature/audit-0.7.0` em sua branch remota e abrir PR contra `origin/main`
   já atualizado para 0.6.0;
3. só depois retomar a implementação funcional da auditoria 0.7.0-A, seguindo REVIEWER → DEVELOPER
   → QA → REVIEWER → DOCUMENTER;
4. não fazer merge, push ou sincronização sem autorização explícita.

### Regras críticas preservadas

- não usar `ragtest-ingest --recreate`;
- não usar `docker compose down -v`;
- não recriar corpus, embeddings, collection Qdrant ou os 767 pontos atuais sem autorização;
- não enviar conteúdo `chatscm/*.docx` para Groq, Gemini ou outro provider externo antes de revisão manual de privacidade;
- providers continuam explícitos, sem fallback automático;
- `grounded=true` significa cobertura estrutural de citações sob o gate implementado, não entailment semântico automático;
- backend RAG permanece independente do cliente Expo e do futuro Se Cuida Mulher;
- não fazer merge de futuros PRs sem autorização explícita do usuário.

---

**Última atualização:** 2026-09-22 — revisão técnica multiagente, QA real e commit de infraestrutura concluídos.
**Repositório:** `Daniel-SLima/RagTest`  
**Branch padrão:** `main`  
**Estado validado e mesclado no main:** `0.5.24`
**Trabalho em andamento:** configuração multiagente versionada na branch `feature/audit-0.7.0`; a implementação funcional da auditoria 0.7.0-A permanece pausada até nova autorização.

---

## Atualização de continuidade — sidequest Demo M1 (2026-09-23)

Esta seção registra a fotografia específica da sidequest M1 e não substitui o handoff
autoritativo histórico acima.

- **Implementado/verificado no workspace:** a branch `sidequest/ragtest-demo` está no HEAD
  `94a5822` (`5ecd3c2` endpoints demo, `ecb977c` hardening, `94a5822` redaction final). Os
  endpoints opt-in são `POST /v1/demo/run`, `POST /v1/demo/retrieval` e `GET /v1/demo/runtime`;
  com `DEMO_ENABLED=false` (padrão), não são registrados nem aparecem no OpenAPI. A configuração
  de allowlist positiva em `DEMO_ALLOWED_SOURCE_PREFIXES` falha fechada quando vazia e rejeita
  sempre `chatscm`/fontes privadas.
- **Implementado/verificado por testes:** os schemas demo aceitam `query` e `retrieval_mode`
  limitado a `dense`, `dense-rerank` ou `hybrid`, sem alterar `Settings.retrieval_mode`. DTOs
  fechados expõem somente IDs determinísticos, documentos públicos, excerpts sanitizados, scores
  disponíveis e `retrieval_ms`, `generation_ms` e `total_ms` monotônicos (`generation_ms=null`
  no retrieval-only). Metadata arbitrária, paths pessoais, prompts, tokens, segredos, `.env` e
  exceções cruas ficam fora do contrato. Evidências: `tests/test_demo.py` (37 testes demo), suíte
  backend com 186 testes e Ruff 0.16.8; `git diff --check` é o gate documental desta atualização.
- **Aguardando validação real:** ainda não há execução com provider externo ou Qdrant real para
  esta demo; portanto os tempos, respostas e comportamento em runtime real permanecem não
  verificados. A documentação pública da sidequest está em `docs/demo-m1.md`.
- **Fora de escopo M1:** frontend/UI, replay, corpus, embeddings, ingestão, mutações de Qdrant,
  configuração de providers e qualquer M2+.
- **Segurança operacional:** uma execução anterior de `docker compose config` materializou
  credenciais na saída. Os valores não foram repetidos nem lidos no fluxo atual; rotação de
  credenciais é pendência antes de compartilhar ou publicar qualquer transcript. Esta nota não
  classifica aquela execução como validação bem-sucedida.

## Atualização de continuidade — sidequest Demo M2 (2026-09-23)

Esta seção complementa a fotografia M1 acima. O handoff histórico e as decisões anteriores
permanecem preservados; em caso de conflito, o estado local e as evidências desta seção são a
fonte específica da sidequest.

### Estado e evidências

- **Implementado:** a fundação visual opt-in do Expo foi integrada na branch
  `sidequest/ragtest-demo`, com HEAD `f675243` (`fix: align M2 future boundaries and labels`). O M2
  contém as abas `Chat`, `Como funciona`, `Laboratório` e `O que ainda falta`, componentes
  responsivos, estados vazios/neutros, catálogo de roadmap e contratos TypeScript para uso
  futuro. Após o QA final, a narrativa registra 11 etapas, a aba Chat mantém a ação futura
  desabilitada, a identidade informa que a demo não é a versão final do produto Se Cuida Mulher,
  e o Laboratório apresenta oito controles futuros desabilitados. O Laboratório é uma superfície
  explicitamente reservada ao M4, não ao M3.
- **Verificado:** as etapas públicas do pipeline exibem **aguardando execução**; o enum interno
  estável `awaiting-execution` preserva o contrato sem simular execução, resposta, ranking, fonte
  ou timing.
- **Verificado:** os statuses públicos do roadmap permanecem fechados em `Implementado`,
  `Parcial / em desenvolvimento`, `Planejado` e `Em estudo`; cada item mantém referência de
  evidência e não transforma intenção em resultado.
- **Verificado:** a flag `EXPO_PUBLIC_RAG_DEMO_ENABLED` só habilita o frontend para `true`
  após normalização `trim().toLowerCase()`; ela é independente de `DEMO_ENABLED` e
  `DEMO_ALLOWED_SOURCE_PREFIXES`. A matriz de valores falsy/ausentes e a separação entre
  `NormalApp` e `DemoApp` são cobertas pelos testes. O M2 não faz requests na construção,
  renderização, troca de aba ou exemplos e não aciona providers, Qdrant ou endpoints demo.
- **Verificado:** a orientação nativa permanece `portrait` e a validação Web usa landscape.
  Os viewports-alvo são `1366x768`, `1024x600`, `390x844` e `360x800`; o layout usa reflow de
  abas, cards empilhados, safe-area, foco visível, alvos acessíveis, Dynamic Type e contraste
  para os temas claro/escuro. O bundle Expo Web foi gerado sem backend.
- **Verificado por gates:** 49 testes Jest, `npm run typecheck`, Ruff e `git diff --check`
  passaram. O M1 backend permanece verificado separadamente; esses gates não são uma execução
  real com provider externo ou Qdrant.
- **Aguardando validação:** qualquer validação visual manual adicional em runtime nativo/Web
  e a revisão operacional para permitir chamadas reais permanecem pendentes. M2 não classifica
  M3, M4 ou M5 como implementados.

### Limites e próxima fronteira

M2 é exclusivamente visual e preparatório: não há live run, replay, ranking, resposta gerada,
grounding ao vivo, telemetria nem requests. Antes de iniciar M3, são obrigatórias a validação
dos DTOs de runtime no cliente, a política de origem/base URL com HTTPS allowlist quando
aplicável, a revisão de CORS/autenticação/privacidade e a revisão dos exemplos, grounding e
telemetria. O backend M1 e o frontend M2 continuam habilitados por flags independentes.

### Risco operacional preservado

Uma execução histórica de `docker compose config` materializou credenciais na saída. Nenhum
valor é repetido aqui; a rotação deve ocorrer antes de compartilhar qualquer transcript que
contenha aquela saída. Este incidente não é evidência de validação de runtime e não autoriza
alteração de secrets, providers, Docker ou Qdrant.

**Última atualização desta sidequest:** 2026-09-23 — M2 implementado no commit `f675243`,
QA final concluído, gates automatizados e bundle Expo Web sem backend verificados; M3 aguardando
validação e revisão.

## Atualização de continuidade — sidequest Demo M3 (2026-09-23)

Esta seção registra o handoff do recorte M3 e complementa, sem apagar, os registros M1 e M2.

### Estado implementado e contrato do cliente

- **Implementado no frontend:** no HEAD `c7925d7`, a demo Expo usa estado/reducer compartilhado
  entre `Chat` e `Como funciona`. `GET /v1/demo/runtime` é disparado uma vez na montagem;
  `POST /v1/demo/run` ocorre somente no envio explícito e no retry explícito. Troca de abas,
  modos de apresentação e montagem em StrictMode não devem duplicar a execução.
- **Implementado/verificado por testes:** o cliente valida DTOs fechados, conteúdo obrigatório,
  limites, valores finitos, monotonicidade de `retrieval_ms`, `generation_ms` e `total_ms`, e a
  correlação de `citation_ids` com `source.order`. Erros são sanitizados para mensagens
  allowlisted. A política de base URL aceita HTTP apenas em loopback/RFC1918 e HTTPS apenas em
  origens exatas de `EXPO_PUBLIC_RAG_ALLOWED_HTTPS_ORIGINS`; isso é distinto de CORS e de
  `DEMO_ENABLED` no backend.
- **Implementado:** a apresentação live cobre vazio, loading, erro, retry manual, fontes e
  grounding. Scores nulos/ausentes e diagnósticos que não existem no DTO M1 são exibidos como
  indisponíveis. `grounded=true` é cobertura estrutural de citações, não garantia factual ou
  clínica. O single-query é uma descrição estática da configuração da versão; multi-query,
  decomposição, retry count, contexto final, dimensão de embedding e métricas pre/post-reranking
  permanecem indisponíveis e não são inferidos.
- **Fora do recorte:** nenhum código backend, provider, corpus, embedding, collection Qdrant,
  Docker ou `.env` foi alterado. O endpoint `/v1/demo/retrieval` permanece contrato M1, mas não é
  usado pelo fluxo principal M3. Replay não foi implementado; o Laboratório continua reservado
  ao M4.

### Evidências, validação e riscos

- **Verificado pelos gates finais do orquestrador:** 85 testes Jest em 9 suites, `npm run
  typecheck`, Ruff via `.venv\\Scripts\\ruff.exe`, `git diff --check` e bundle Expo Web offline.
  O bundle confirma a inicialização da demo sem backend; não comprova operação live. O QA
  anterior registrou 84 testes e Ruff **não executado** por indisponibilidade do executável naquele
  ambiente; a verificação posterior do orquestrador fechou essa pendência.
- **Aguardando validação:** runtime real com provider, Qdrant e POST live; validação manual dos
  viewports `1366x768`, `1024x600`, `390x844` e `360x800`; e qualquer uso com dados reais. Não há
  evidência para classificar esses itens como verificados.
- **Segurança:** revisão frontend **PASS condicionada**. Os logs crus preexistentes de Groq e
  Ollama continuam um bloqueio P1 para exposição externa/produção e não foram alterados, pois a
  autorização M3 exclui expansão backend. Operar somente em ambiente local controlado, manter
  `DEMO_ENABLED=false` fora dele e não enviar dados pessoais/privados a providers externos.

### Próxima fronteira

M4 permanece apenas planejado: Laboratório experimental com Dense, Dense+rerank, Hybrid, Top K,
Multi-query e comparação, sujeito a contrato explícito, privacidade, autenticação, rate limiting
e logs sanitizados. Replay e demais diagnósticos de backend ficam para uma etapa futura autorizada.

**Última atualização desta sidequest:** 2026-09-23 — M3 frontend implementado no HEAD `c7925d7`;
85 Jest/9 suites, typecheck, Ruff e diff-check aprovados pelo orquestrador, com bundle Expo Web
offline registrado; runtime live e quatro viewports permanecem pendentes conforme acima.

## Atualização de continuidade — gate M3.5 da sidequest Demo (2026-09-23)

Esta seção complementa o handoff M3 sem reclassificar evidência automatizada como validação
operacional. O gate M3.5 foi executado no HEAD funcional `7015db8` (`fix: theme demo answer
presentation`); os commits documentais anteriores são `c90822b` e `824cbc0`.

### Classificação do gate

- **RUNTIME VALIDATED:** somente no ambiente local/controlado descrito abaixo.
- **Não verificado:** operação externa/produção, quatro viewports individualmente, tema claro
  manual, retry live independente e inspeção direta de Network/console.
- **Não autorizado:** M4. O Laboratório, seus controles e qualquer expansão de backend continuam
  planejados.

### Ambiente validado e controle negativo

- FastAPI em `127.0.0.1:8001`, sem alteração de `.env`;
- `DEMO_ENABLED=true`, allowlist pública e CORS local;
- Qdrant em `localhost:6333`, com os 767 pontos preservados;
- Ollama local com `qwen3:8b`;
- nenhuma transmissão externa, nenhum dado pessoal e nenhum conteúdo `CHATSCM`.

O controle negativo usou a composição na porta 8000 com `DEMO_ENABLED=false`: o endpoint
`GET /v1/demo/runtime` respondeu `404`, confirmando que o runtime demo permanece fechado quando
o backend não está habilitado.

### Evidências sanitizadas

- `/health`, `/ready` e `/v1/demo/runtime`: `200` no cenário habilitado;
- `/v1/demo/retrieval`: `200`, com uma fonte pública da página 34 e scores;
- `/v1/demo/run`: `200`, `grounded=true`, uma citação/fonte e timings monotônicos;
- Expo Web em `8082`: runtime, resposta Markdown, fontes, grounding e navegação `Chat` ↔
  `Como funciona` observados;
- correção do tema escuro registrada no `7015db8`, com apresentação legível na observação
  visual.

Esses fatos sustentam apenas a classificação local/controlada. Não sustentam disponibilidade
externa, segurança de produção, entailment semântico ou garantia clínica.

### Requisições, loading e retry

O runtime foi consultado uma vez por montagem; uma execução `POST` ocorreu por ação explícita.
Não houve novos runs ao trocar abas, abrir o pipeline ou alternar `Automático`, `Apresentação`,
`Próximo` ou `Anterior`. Loading foi observado durante a execução. No controle negativo, o erro
`404` recebeu apresentação amigável e o retry manual foi observado.

### Segurança, riscos e pendências

A revisão é **PASS local**, porém **BLOCKED para uso externo/produção** por logs crus
preexistentes de Groq/Ollama, ausência de autenticação/rate limiting e risco residual de prompt
injection. Manter `DEMO_ENABLED=false` fora de ambiente local controlado e não usar dados pessoais
ou `CHATSCM`.

Pendências importantes: observar individualmente `1366x768`, `1024x600`, `390x844` e `360x800`;
validar manualmente o tema claro; demonstrar retry live independente; e inspecionar diretamente
Network/console no DevTools. O gate M3.5 não altera corpus, embeddings, Qdrant ou providers.

## Atualização de continuidade — gate M3.6 da sidequest Demo (2026-09-23)

O gate M3.6 complementa o registro M3.5. O ponto de partida documental foi `d24c76a`; a
correção funcional `62a2983` tratou títulos longos no viewport de 360 px. Nenhum código fora
dessa correção, corpus, Qdrant, provider ou `.env` foi alterado nesta validação.

### Validação visual

Após `62a2983`, os quatro viewports foram observados individualmente com resultado **PASS**:
`1366x768`, `1024x600`, `390x844` e `360x800`. O tema claro não foi observável manualmente na
sessão: o IAB/OS permaneceu em tema escuro e não havia emulação disponível. Portanto, tema claro
continua **pendente**, não verificado.

### Retry live e requisições

Com a API interrompida, a interface exibiu erro amigável; depois da restauração, um único retry
explícito gerou o segundo `POST`, obteve sucesso e não duplicou a execução. A tentativa com a API
parada não chegou ao backend. As contagens observadas foram: um `GET /v1/demo/runtime` por
montagem, primeiro `POST` acompanhado de preflight `OPTIONS` e segundo `POST` no retry.

As 11 etapas do pipeline corresponderam ao novo run. Troca de abas, pipeline e modos de
apresentação não produziram novos runs.

### Observabilidade e segurança

DevTools Network/Console não foram observáveis diretamente porque o IAB não ofereceu CDP e o
Chrome estava indisponível. A inspeção estática do frontend e o comportamento sanitizado
permanecem **PASS** dentro dessa limitação.

O bloqueio de segurança externo/produção permanece: logs crus preexistentes de Groq/Ollama,
ausência de autenticação/rate limiting e risco residual de prompt injection. M4 continua não
autorizado. O tema claro e a inspeção direta de Network/Console seguem como pendências distintas,
sem rebaixar os quatro viewports e o retry que foram observados como PASS.

---

## 1. Objetivo final do projeto

Este projeto é o módulo conversacional baseado em RAG do TCC:

**“Desenvolvimento de Módulo Conversacional Baseado em RAG para Apoio ao Letramento em Saúde e Acesso a Serviços no Aplicativo Se Cuida Mulher”.**

O objetivo final é entregar um módulo independente, reutilizável e integrável ao aplicativo **Se Cuida Mulher**, capaz de:

- receber perguntas em linguagem natural;
- recuperar trechos relevantes de documentos oficiais e materiais do corpus;
- gerar respostas contextualizadas e fundamentadas;
- citar as fontes utilizadas;
- reduzir alucinações;
- manter rastreabilidade/auditoria das respostas;
- futuramente oferecer histórico de sessão, streaming e integração com o aplicativo;
- servir como artefato técnico do TCC, com métricas de retrieval e documentação das decisões de engenharia.

O módulo deve continuar independente da interface mobile até o pipeline RAG estar estável e mensurável.

---

## 2. Escopo acadêmico e técnico

### Objetivo geral

Desenvolver e integrar um módulo de chat inteligente baseado em RAG para apoio ao letramento informacional em saúde e orientação de acesso/agendamento de serviços.

### Objetivos técnicos

1. Pipeline automatizado de ingestão, extração, OCR quando necessário, limpeza, chunking e vetorização.
2. Retrieval semântico e/ou híbrido sobre corpus documental.
3. Geração fundamentada com LLM e citações de fontes.
4. Segurança, resiliência e mitigação de respostas sem base documental.
5. Auditoria e métricas de qualidade do retrieval.
6. API REST reutilizável.
7. Futuramente: sessões, histórico, streaming/WebSocket, links/gatilhos de serviços e integração com app.

---

## 3. Arquitetura atual

### Backend

- Python 3.12
- FastAPI
- Docker / Docker Compose

### Banco vetorial

- Qdrant

### Embeddings

**Dense:**
- FastEmbed
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- dimensão: 384

**Sparse:**
- FastEmbed
- `Qdrant/bm25`
- idioma: português

### LLM

- Google Gemini
- modelo atual: `gemini-3.6-flash`

### Processamento documental

- PyPDF para extração textual normal;
- Tesseract OCR + pacote português;
- PyMuPDF para renderização das páginas que precisam de OCR;
- python-docx para DOCX;
- LangChain Text Splitters para chunking.

### API atual

- `GET /health`
- `GET /ready`
- `POST /v1/search`
- `POST /v1/chat`
- Swagger: `http://localhost:8000/docs`

---

## 4. Fluxo atual do RAG

```text
PDF / DOCX
    |
    v
extração normal
    |
    +---- página sem texto ----> OCR Tesseract local
    |
    v
Document
    |
    v
chunking
    |
    +-------------------+
    |                   |
    v                   v
dense embedding       BM25 sparse
    |                   |
    +---------+---------+
              |
              v
            Qdrant
              |
              v
     retrieval de candidatos
              |
              v
     agrupamento por página
              |
              v
      reranking / seleção
              |
              v
          contexto RAG
              |
              v
      Gemini 3.6 Flash
              |
              v
       resposta + fontes
```

---

## 5. Corpus atual

Total de arquivos: **18**

Categorias principais:

- alimentação;
- chatscm;
- diabetes;
- direitos_saude;
- gestacao;
- medicamentos;
- pessoa_idosa;
- saude_sexual_reprodutiva;
- vacinacao.

Arquivos incluem PDFs do SUS/Ministério da Saúde e 3 DOCX da pasta CHATSCM.

### Cobertura após OCR — estado 0.5.6

Antes do OCR havia **699 chunks**.

Após a correção de ingestão:

- corpus total: **767 chunks**;
- Carta dos Direitos e Deveres: 28/28 páginas recuperadas por OCR;
- Carta dos Direitos e Deveres: aproximadamente 41 mil caracteres;
- Carta dos Direitos e Deveres: 62 chunks;
- Caderneta da Gestante: 50/50 páginas com texto, incluindo 3 recuperadas por OCR;
- Caderneta da Pessoa Idosa: 63/64 páginas com texto; a página restante pode ser visualmente vazia e ainda precisa ser auditada se isso se tornar relevante.

---

## 6. Regra de privacidade importante

Os arquivos `chatscm/*.docx` ainda **não foram manualmente auditados neste projeto quanto a dados pessoais/identificáveis**.

Por isso:

- não presumir que estão anonimizados;
- não afirmar que são seguros apenas pelo nome;
- antes de usar conteúdo CHATSCM em chamadas externas do Gemini em contexto real, revisar/desidentificar ou obter autorização adequada;
- nunca versionar chaves, tokens, segredos ou dados clínicos identificáveis.

A `GEMINI_API_KEY` deve existir apenas no `.env` local.

---

## 7. Estado do .env local

Configuração recomendada a partir da 0.5.8:

```env
PDF_OCR_ENABLED=true
PDF_OCR_LANGUAGE=por
PDF_OCR_DPI=200
PDF_OCR_TIMEOUT_SECONDS=60

SPARSE_EMBEDDING_PROVIDER=fastembed_bm25
SPARSE_EMBEDDING_MODEL=Qdrant/bm25
SPARSE_EMBEDDING_LANGUAGE=portuguese

RETRIEVAL_MODE=dense-rerank
RETRIEVAL_MERGE_SAME_PAGE=true
RETRIEVAL_MAX_GROUP_CHARS=5000

LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.6-flash
LLM_TEMPERATURE=0.1
```

A 0.5.8 passa a usar perfis versionados para `dense`, `dense-rerank` e `hybrid`. As antigas variáveis de tuning de candidate multiplier, score margin, pesos lexicais e pesos híbridos podem continuar no `.env` local por compatibilidade, mas são ignoradas pelo runtime novo.

No ambiente local do usuário, `LLM_MAX_OUTPUT_TOKENS` foi mantido em **4096** após um caso real de truncamento da resposta.

Nunca copiar nem registrar o valor da chave Gemini neste documento.

---

## 8. O que já foi concluído

### Fases iniciais

- estrutura do projeto;
- FastAPI;
- Qdrant;
- Docker Compose;
- loaders PDF/DOCX;
- chunking;
- embeddings locais;
- ingestão;
- retrieval;
- endpoint de busca;
- chat RAG;
- Gemini;
- metadado `audience`;
- filtros por público;
- fontes/citações;
- CLI de ingestão, busca, chat e avaliação.

### Melhorias de retrieval

- overfetch;
- agrupamento de chunks da mesma página;
- reconstrução respeitando `start_index`;
- remoção de overlap quando possível;
- reranking lexical;
- retrieval híbrido dense + BM25;
- RRF;
- avaliação com HitRate@5 e MRR@5.

### Qualidade de ingestão

- auditoria por arquivo;
- detecção de `NO_TEXT`, `NO_CHUNKS`, `PARTIAL_TEXT`;
- OCR seletivo local;
- metadata `extraction_method`.

---

## 9. Histórico experimental

### 0.5.1 — dense

Corpus ainda incompleto.

- HitRate@5: 0.857
- MRR@5: 0.714

### 0.5.2 — dense + reranking lexical

Corpus ainda incompleto.

- HitRate@5: 0.857
- MRR@5: 0.786

### 0.5.3 — dense + BM25 + RRF

Corpus ainda incompleto.

- HitRate@5: 0.714
- MRR@5: 0.607

### 0.5.4 — BM25 enriquecido

Corpus ainda incompleto.

- HitRate@5: 0.857
- MRR@5: 0.690

### 0.5.5 — auditoria

Descoberta principal:

`direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf`

tinha:

- 28 páginas;
- 0 páginas com texto;
- 0 caracteres;
- 0 chunks.

Logo, a falha de retrieval da consulta sobre direitos/deveres era principalmente uma falha de ingestão.

### 0.5.6 — OCR seletivo

Corpus corrigido para 767 chunks.

No modo híbrido atual:

- HitRate@5: **1.000 (7/7)**
- MRR@5: **0.821**
- consulta de direitos/deveres recupera a Carta no rank 1.

**Importante:** esta é a primeira baseline pós-correção de cobertura. Os números anteriores não são diretamente comparáveis porque o corpus mudou.

### 0.5.7 — benchmark controlado no mesmo corpus

Todos os modos foram executados sobre os mesmos 767 chunks:

| Modo | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| dense | 1.000 | 0.857 |
| dense-rerank | 1.000 | 0.929 |
| hybrid | 1.000 | 0.821 |

`dense-rerank` é o melhor resultado **medido no conjunto atual de sete consultas**, mas o conjunto ainda é pequeno e não permite concluir superioridade geral.

---

## 10. Dificuldades do TCC já registradas

Arquivo detalhado:

`docs/dificuldades-tcc.md`

Casos atuais:

1. filtro por categoria piorou a recuperação;
2. Gemini atingiu limite de tokens;
3. avaliador dependia de arquivo que não existia no runtime Docker;
4. busca densa não recuperava a carta de direitos;
5. reranking melhorou MRR, mas não recall;
6. retrieval híbrido inicial piorou métricas;
7. BM25 enriquecido não resolveu a fonte problemática;
8. fonte esperada tinha zero texto e zero chunks;
9. retrieval híbrido não superou dense-rerank no mesmo corpus;
10. `pyproject.toml` inválido bloqueou o build Docker da 0.5.11;
11. consulta composta recuperou direitos, mas não detalhou deveres;
12. RRF reforçou a intenção dominante quando a pergunta original foi fundida com as subconsultas;
13. CI bloqueava o pytest por falhas de lint;
14. teste de health tinha versão inicial hardcoded.

**Regra:** quando algo planejado não funcionar como esperado, criar uma nova “Dificuldade TCC #N” com:

- planejado;
- observado;
- diagnóstico;
- correção;
- Aprendizado técnico.

---

## 11. O que está sendo feito agora

### Fase 0.5.14 — CI e execução real da suíte

A 0.5.13 foi validada e mesclada no `main`.

Objetivo atual:

- corrigir as 8 violações Ruff que bloqueiam a CI;
- separar lint e pytest em jobs independentes;
- tornar a versão/regras do Ruff reprodutíveis;
- finalmente observar o resultado real da suíte pytest no GitHub Actions;
- evitar workflows em mudanças exclusivamente documentais.

Branch ativa:

`feature/ci-quality-gate-0.5.14`

Status: **validado em CI e runtime local. Lint verde, pytest 51 passed / 4 warnings, `/health`=0.5.14 e `/ready` com Qdrant ok. PR #8 aguarda autorização explícita de merge.**

### Histórico — fase 0.5.13 — decomposição automática no chat

A 0.5.12 foi validada e mesclada no `main`.

Objetivo atual:

- detectar perguntas potencialmente compostas;
- usar o LLM apenas como planejador de subconsultas quando necessário;
- limitar a decomposição a 2-3 consultas autossuficientes;
- usar o multi-query/RRF validado na 0.5.12;
- preservar single-query para perguntas simples;
- fazer fallback seguro para single-query quando o planejamento falhar;
- expor diagnóstico da estratégia na resposta da API.

Branch ativa:

`feature/automatic-decomposition-0.5.13`

Status: **validado em runtime nos dois caminhos: multi-query automático para pergunta composta e single-query para pergunta simples. PR #7 permanece draft aguardando autorização explícita de merge.**

### Histórico — fase 0.5.12 — experimento controlado de multi-query

A 0.5.11 foi validada e mesclada no `main`.

Objetivo atual:

- provar o mecanismo de multi-query antes de automatizar a decomposição;
- executar a consulta original e subconsultas explícitas;
- preservar `dense-rerank` em cada busca;
- deduplicar resultados por fonte/página;
- fundir rankings por RRF;
- verificar se a página 13 de deveres volta ao top 5 no caso diagnóstico;
- não alterar pesos, corpus ou endpoint `/v1/chat` nesta etapa.

Branch ativa:

`feature/multi-query-retrieval-0.5.12`

Status: **validado em runtime: self-check completo PASS e página 13 de deveres em rank 2 no top 5 multi-query. PR #6 permanece draft aguardando autorização de merge.**

### Histórico — fase 0.5.11 — groundedness e citações verificáveis

A 0.5.10 foi validada e mesclada no `main`.

Objetivo atual:

- remover scores internos do contexto enviado ao LLM;
- tratar documentos recuperados explicitamente como dados não confiáveis;
- adicionar defesa de prompt contra instruções encontradas dentro dos documentos;
- validar programaticamente citações `[n]`;
- repetir a geração uma vez quando citações forem inválidas ou ausentes;
- retornar fallback seguro se a resposta continuar sem citações verificáveis;
- expor `grounded`, `citation_ids` e `citation_retry_count` na API.

Branch ativa:

`feature/grounded-citations-0.5.11`

Status: **fluxo real validado: `grounded=true`, citações [1,2,3] válidas e `citation_retry_count=0`. PR #5 permanece draft. A resposta revelou cobertura parcial de deveres, registrada como Dificuldade TCC #11.**

### Histórico — fase 0.5.10 — métricas source-level

A 0.5.9 foi validada e mesclada no `main`.

Objetivo atual:

- preservar HitRate@k e MRR@k para comparação histórica;
- adicionar SourceRecall@k para medir quantas fontes esperadas distintas foram recuperadas;
- adicionar SourceNDCG@k para medir a ordenação das fontes esperadas sem contar páginas repetidas da mesma fonte como novos acertos;
- mostrar a quantidade de fontes distintas por consulta;
- não alterar retrieval, pesos, corpus ou dataset.

Branch ativa:

`feature/source-metrics-0.5.10`

Status: **implementado, PR #4 aberto como draft e aguardando validação local**.

### Histórico — fase 0.5.9 — avaliação holdout congelada

O PR #2 da 0.5.8 foi autorizado pelo usuário e mesclado no `main`.

Objetivo atual:

- ampliar a avaliação sem alterar os parâmetros do retrieval;
- separar as 7 consultas usadas no desenvolvimento de um conjunto novo;
- congelar um holdout antes da primeira execução;
- verificar se o `dense-rerank` generaliza para perguntas e domínios não usados no ajuste;
- preservar a primeira execução do holdout como evidência experimental.

### Branch ativa

`feature/holdout-evaluation-0.5.9`

### Dataset versionado

`2026-09-20-v1`

Suites:

- `dev`: 7 consultas históricas;
- `holdout`: 15 consultas novas;
- `all`: 22 consultas.

O holdout cobre alimentação, vacinação de adulto/adolescente/criança/idoso/gestante, saúde bucal na gestação, cadernetas, medicamentos, contracepção e paráfrases das consultas centrais.

Status: **implementado e validado localmente. No holdout, `dense-rerank` manteve HitRate@5=1.000 e obteve o maior MRR@5 (0.933) entre os três perfis. A suite dev reproduziu exatamente a baseline histórica. PR #3 aguarda autorização de merge.**

---

## 12. Ponto exato onde o trabalho foi pausado

A 0.5.8 foi validada e mesclada no `main`.

A 0.5.9 foi implementada e validada localmente.

Verificado:

1. `/health` retornou versão 0.5.9;
2. `/ready` retornou ready com Qdrant ok;
3. primeira execução preservada de `dense-rerank` no holdout:
   - HitRate@5=1.000 (15/15);
   - MRR@5=0.933;
4. comparação completa no holdout:
   - dense: HitRate@5=1.000, MRR@5=0.889;
   - dense-rerank: HitRate@5=1.000, MRR@5=0.933;
   - hybrid: HitRate@5=1.000, MRR@5=0.878;
5. regressão da suite dev reproduziu exatamente:
   - dense: HitRate@5=1.000, MRR@5=0.857;
   - dense-rerank: HitRate@5=1.000, MRR@5=0.929;
   - hybrid: HitRate@5=1.000, MRR@5=0.821.

Conclusão experimental: `dense-rerank` foi o perfil com maior MRR tanto na suite dev quanto no primeiro holdout congelado, sempre com HitRate@5=1.000. Isso reforça a escolha do perfil padrão, sem transformar o resultado em uma alegação de superioridade universal.

Dois pontos qualitativos permanecem relevantes:

- `holdout-caderneta-gestante`: a Caderneta da Gestante ficou em rank 2;
- `holdout-vacinas-gestante-parafrase`: o rank 1 foi `chatscm_gestante.docx`; uma fonte esperada ficou em rank 2 e o calendário oficial em rank 5.

O PR #3 ainda não foi mesclado.

Não recriar a collection: os 767 chunks continuam compatíveis.

---

## 13. Próximos 5 passos

### Passo 1 — mesclar a 0.5.10 após autorização

A validação de runtime foi concluída. Aguardar autorização explícita do usuário para mesclar o PR #4.

### Passo 2 — analisar diversidade e cobertura por fonte

Os novos números mostram que o perfil hybrid perdeu uma das duas fontes esperadas em um caso do holdout (SourceRecall@5 agregado=0.967), enquanto dense e dense-rerank mantiveram 1.000. Usar isso como evidência na análise, sem alterar o holdout.

### Passo 3 — preparar decomposição/multi-query

Implementar e avaliar detecção/decomposição de perguntas compostas sem aumentar o top-k global. O caso direitos+deveres é o primeiro caso diagnóstico.

### Passo 4 — preparar relevância preferencial

Definir, em uma fase separada e documentada, como distinguir fonte aceitável de fonte preferencial sem reescrever retroativamente o holdout original.

### Passo 5 — reforçar groundedness e segurança

Validar citações, remover scores internos do prompt, adicionar defesa contra prompt injection documental e revisar a privacidade dos arquivos CHATSCM antes de chamadas externas.

### Passo 6 — preparar a camada de produto

Adicionar logs/auditoria estruturada, sessões, histórico, streaming e integração posterior com o aplicativo Se Cuida Mulher.

---

## 14. Pendências técnicas conhecidas

- warning do FastEmbed sobre mudança de pooling do modelo dense;
- dependências ainda usam intervalos e Qdrant Docker usa `latest`; devem ser pinadas antes da entrega;
- página sem texto restante na Caderneta da Pessoa Idosa pode precisar de inspeção visual;
- loader DOCX atualmente foca em parágrafos; tabelas/cabeçalhos/rodapés ainda devem ser avaliados;
- estratégia de remoção de chunks antigos em ingestão incremental ainda não foi implementada;
- metadata de versão/configuração do embedding na collection deve ser reforçada;
- cliente Gemini pode ser persistido e receber telemetria de `finish_reason`/uso;
- warning de Hugging Face sem autenticação é não bloqueante;
- a suite histórica tem 7 perguntas; a 0.5.9 adiciona 15 perguntas holdout, ainda aguardando primeira execução.

---

## 15. Regras de desenvolvimento daqui para frente

1. Não afirmar que algo “passou” sem teste real.
2. Não alterar métricas para fazer um experimento parecer melhor.
3. Preservar baselines históricas.
4. Sempre comparar estratégias no mesmo corpus quando a comparação for algorítmica.
5. Quando o corpus mudar, registrar explicitamente a mudança.
6. Preferir branch + Pull Request para novas alterações.
7. Não fazer merge sem pedido/validação do usuário.
8. Não expor chaves ou segredos.
9. Não enviar dados de saúde identificáveis a serviços externos.
10. Atualizar **este arquivo** ao final de toda tarefa relevante.
11. Quando uma decisão alterar arquitetura, provider, estratégia padrão, segurança, armazenamento ou metodologia de avaliação, registrar também em `docs/decisoes-tecnicas.md`.

---

## 16. Procedimento para reiniciar em outro chat

Quando o usuário disser algo como:

> “Continuar o RagTest”

ou simplesmente:

> “continuar”

o assistente deve:

1. abrir `docs/CONTEXTO_CONTINUIDADE.md` no GitHub;
2. verificar a branch/PR atual;
3. verificar se houve commits posteriores à última atualização;
4. retomar pelo item **“Ponto exato onde o trabalho foi pausado”**;
5. atualizar este documento novamente ao final da nova etapa.

Se houver divergência entre este arquivo e o estado real do GitHub, o **GitHub atual prevalece** e este arquivo deve ser corrigido.

---

## 17. Arquivos de documentação relacionados

- `docs/CONTEXTO_CONTINUIDADE.md` — este arquivo; estado geral e ponto de retomada;
- `docs/dificuldades-tcc.md` — problemas, diagnósticos, correções e aprendizados;
- `docs/decisoes-tecnicas.md` — registro curto das decisões que mudam arquitetura, comportamento padrão ou metodologia;
- `docs/avaliacao-retrieval.md` — histórico de métricas e experimentos;
- `README.md` — uso e estado funcional do projeto.

---

## 18. Resumo de retomada rápida

```text
Projeto: RagTest / Se Cuida Mulher
Main validado/mesclado: 0.5.18
Corpus: 18 arquivos / 767 chunks após OCR
Qdrant: dense + sparse
Dense: paraphrase-multilingual-MiniLM-L12-v2
Sparse: Qdrant/bm25 português
LLM: Gemini 3.6 Flash
OCR: Tesseract local, seletivo
Baseline pós-OCR híbrida: HitRate@5=1.000 / MRR@5=0.821

Em andamento:
0.5.18 semântica explícita dos rótulos de avaliação

Branch:
feature/evaluation-label-semantics-0.5.18

PR:
#12 draft — Explicita semântica dos rótulos de avaliação na 0.5.18

PR:
#11 draft — Adiciona auditoria estrutural de DOCX na 0.5.17

PR:
#10 draft — Adiciona planejamento seguro da ingestão incremental 0.5.16

PR:
#9 draft — Adiciona fingerprint de runtime na 0.5.15

PR:
#4 draft — Adiciona métricas source-level na avaliação 0.5.10

Dataset:
2026-09-20-v1 — dev=7, holdout=15, all=22

PR:
#3 draft — Adiciona avaliação holdout congelada na 0.5.9

0.5.7 validada:
dense         HitRate@5=1.000 / MRR@5=0.857
dense-rerank  HitRate@5=1.000 / MRR@5=0.929
hybrid        HitRate@5=1.000 / MRR@5=0.821

Pausado em:
a infraestrutura de avaliação v2 da 0.5.18 foi validada localmente. O `ragtest-check-evaluation-v2` passou em todos os checks de semântica OR/AND. A regressão do dataset v1 em `dense-rerank` reproduziu exatamente a baseline histórica: HitRate@5=1.000 (7/7), MRR@5=0.929, SourceRecall@5=1.000 e SourceNDCG@5=0.936. A CI final passou com Ruff verde e `72 passed, 4 warnings`.

O warning do FastEmbed sobre mean pooling continua sendo o warning conhecido do runtime 0.8.0 e não altera a decisão já tomada na 0.5.15 de preservar o runtime validado, em vez de voltar cegamente para 0.5.1.

Próxima ação ao receber "continuar":
aguardar autorização explícita do usuário para merge do PR #12. Após o merge, iniciar a próxima fase de groundedness/segurança sem reindexar a collection.
```


---

## 19. Modelo de conversa e comportamento esperado do assistente

Este projeto está sendo desenvolvido de forma incremental por chat. A continuidade técnica não é suficiente: a experiência de conversa também deve permanecer consistente entre chats.

Ao retomar o projeto em um novo chat, o assistente deve conversar como continuação natural do trabalho anterior, e não como se estivesse conhecendo o projeto pela primeira vez.

### Idioma e tom

- responder em português do Brasil;
- manter tom colaborativo, técnico e acessível;
- ser direto, mas explicar o raciocínio necessário para o usuário entender por que cada mudança está sendo feita;
- evitar respostas excessivamente formais ou acadêmicas durante o desenvolvimento;
- preservar termos usados durante o projeto, como `Dificuldade TCC`, `baseline`, `retrieval`, `chunks`, `dense`, `BM25`, `RRF`, `OCR` e nomes das fases;
- não reexplicar conceitos básicos já consolidados sem necessidade;
- não agir como se o usuário precisasse reapresentar o projeto.

### Forma de conduzir o desenvolvimento

O fluxo de conversa deve seguir este padrão:

1. analisar o log, erro ou resultado enviado;
2. dizer claramente **o que aconteceu**;
3. explicar **o que esse resultado significa tecnicamente**;
4. relacionar o resultado com o TCC quando ele produzir aprendizado relevante;
5. implementar/corrigir no GitHub quando apropriado;
6. informar exatamente o que foi alterado;
7. dizer se precisa ou não reconstruir Docker, reindexar Qdrant ou alterar `.env`;
8. fornecer os comandos exatos para Windows CMD;
9. esperar o usuário executar e enviar o retorno antes de afirmar que a etapa passou;
10. atualizar este arquivo ao final da tarefa relevante.

### Regra de verificação

Nunca dizer que:

- a versão está funcionando;
- um teste passou;
- um bug foi corrigido;
- uma métrica melhorou;
- uma integração está pronta;

sem evidência real de execução.

Usar distinções explícitas:

- **implementado:** código foi alterado;
- **aguardando validação:** ainda não houve execução pelo usuário/CI;
- **verificado:** existe log/teste confirmando;
- **hipótese:** ainda será testada.

### Quando o usuário enviar logs

Se o usuário colar saída de CMD/Docker:

- ler o log completo;
- identificar warnings separadamente de erros bloqueantes;
- não tratar warning como falha automaticamente;
- comparar o resultado com a versão/teste anterior;
- apontar mudanças de métricas;
- registrar uma nova Dificuldade TCC somente quando algo planejado falhar, revelar limitação ou exigir mudança relevante;
- se o resultado estiver correto, dizer claramente que a hipótese foi confirmada;
- dar somente os próximos comandos necessários para a etapa seguinte.

### Quando houver uma Dificuldade TCC

Usar o formato:

```text
Dificuldade TCC #N — título curto

Planejado:
...

Observado:
...

Diagnóstico:
...

Correção:
...

Aprendizado técnico:
...
```

Também atualizar `docs/dificuldades-tcc.md`.

### Quando uma versão mudar

Sempre informar:

- versão anterior;
- nova versão;
- objetivo da mudança;
- branch;
- commit;
- PR, quando existir;
- se exige `docker compose up --build`;
- se exige `ragtest-ingest --recreate`;
- comandos de validação.

### GitHub

Preferir:

```text
feature branch
    ↓
commit
    ↓
Pull Request draft
    ↓
teste real
    ↓
resultado
    ↓
merge somente após validação/pedido do usuário
```

Mudanças de documentação de continuidade podem ser mantidas também no `main`, pois este arquivo precisa estar acessível para recuperação de contexto em novos chats.

### Ritmo da conversa

Não despejar muitas tarefas de uma vez.

O padrão preferido é:

```text
alteração
↓
comandos de teste
↓
usuário envia resultado
↓
análise
↓
próxima alteração
```

Quando vários comandos forem necessários para validar a mesma etapa, agrupá-los no mesmo bloco.

### Resposta após “continuar”

Quando o usuário enviar apenas:

> continuar

não pedir que ele explique novamente o projeto.

Primeiro:

1. ler este arquivo;
2. conferir GitHub/branch/PR;
3. dizer em poucas linhas onde o projeto parou;
4. continuar diretamente da próxima ação registrada.

Exemplo de abertura adequada:

> Perfeito. Retomando exatamente de onde paramos: o `main` validado está na 0.5.6 com 767 chunks após OCR, e a 0.5.7 está na branch `feature/retrieval-benchmark-0.5.7` aguardando o benchmark dense vs dense-rerank vs hybrid. Antes de alterar qualquer código, vou conferir o estado atual da branch e do PR #1.

---

## 20. Exemplo do modelo de resposta usado neste projeto

O exemplo abaixo serve como referência de estrutura, nível de detalhe e estilo. Não deve ser copiado mecanicamente; deve ser adaptado ao resultado real.

### Exemplo: usuário envia um teste bem-sucedido

Usuário:

```text
HitRate@5: 1.000 (7/7)
MRR@5: 0.821
```

Resposta esperada:

> Perfeito. Esse resultado confirma que a correção da ingestão funcionou e que agora todas as sete consultas possuem pelo menos uma fonte esperada no top 5.
>
> O ponto mais importante é separar duas coisas: antes do OCR, a Carta dos Direitos e Deveres não tinha nenhum chunk no índice. Depois do OCR, ela passou a ser recuperada em primeiro lugar. Portanto, não devemos interpretar isso apenas como uma melhora do algoritmo de retrieval; houve uma correção do próprio corpus.
>
> A nova baseline pós-correção fica:
>
> ```text
> HitRate@5 = 1.000 (7/7)
> MRR@5     = 0.821
> ```
>
> Isso também confirma a **Dificuldade TCC #8**: a falha anterior estava na ingestão, não apenas no ranking.
>
> Agora o próximo experimento precisa manter o corpus constante. Por isso vamos comparar `dense`, `dense-rerank` e `hybrid` usando exatamente os mesmos 767 chunks.
>
> A alteração já está preparada na branch:
>
> ```text
> feature/retrieval-benchmark-0.5.7
> ```
>
> Antes de considerar a 0.5.7 pronta, rode:
>
> ```cmd
> git fetch origin
> git switch --track origin/feature/retrieval-benchmark-0.5.7
> docker compose down
> docker compose up --build -d
> curl http://localhost:8000/health
> docker compose run --rm api ragtest-evaluate-retrieval
> ```
>
> Não recrie a collection nessa etapa. Os 767 chunks já estão indexados com vetores dense e sparse.
>
> Quando você enviar o resultado, vamos comparar as três estratégias antes de decidir qual fica como padrão.

### Exemplo: usuário envia um erro

Resposta esperada:

> Encontramos uma falha real nessa etapa.
>
> **Dificuldade TCC #N — descrição curta**
>
> **Planejado:** ...
>
> **Observado:** ...
>
> **Diagnóstico:** ...
>
> **Correção:** ...
>
> **Aprendizado técnico:** ...
>
> Já corrigi/preparei a alteração no GitHub, mas ainda está **aguardando validação**.
>
> Rode:
>
> ```cmd
> comando 1
> comando 2
> ```
>
> Envie o retorno completo. Só depois do teste vamos marcar essa correção como verificada.

---

## 21. Sensação de continuidade entre chats

O objetivo deste arquivo não é apenas recuperar fatos técnicos. Ele deve preservar a forma como o projeto está sendo conduzido.

Em um novo chat, o assistente deve assumir que existe uma relação de trabalho em andamento e:

- usar as mesmas nomenclaturas;
- respeitar decisões anteriores;
- lembrar por que uma arquitetura foi escolhida;
- evitar repetir perguntas já respondidas;
- não desfazer decisões sem apresentar nova evidência;
- continuar registrando experimentos e dificuldades;
- indicar claramente quando está propondo algo novo versus retomando algo já decidido;
- manter a lógica de versões incrementais;
- preservar o foco no TCC e no produto final;
- tratar os logs do usuário como a principal evidência de validação local.

Se houver conflito entre memória do chat, este documento e o estado do GitHub:

1. o estado real do GitHub e os logs de execução mais recentes prevalecem;
2. este documento deve ser atualizado;
3. não inventar uma conclusão para preencher a lacuna.


## Atualização 0.5.19 — cobertura de grounding

A 0.5.18 foi mesclada no main. A 0.5.19 inicia o fortalecimento de groundedness sem usar juiz semântico externo nesta etapa.

Implementado:

- validação determinística por bloco informativo;
- contagem de blocos citados e não citados;
- proporção de cobertura;
- self-check `ragtest-check-grounding-coverage`;
- sem alteração do endpoint `/v1/chat`;
- sem envio de conteúdo CHATSCM a LLM externo para avaliação.

Próximo passo: validar CI e executar o self-check local. Não reindexar Qdrant.


### Etapa 2 da 0.5.19 — gate de cobertura no runtime

O self-check local da cobertura estrutural passou nos quatro cenários esperados, e a CI da primeira etapa passou com Ruff verde e 77 testes.

Com base nisso, a cobertura estrutural foi promovida ao gate de geração do chat:

- toda resposta gerada passa por validação de cobertura por bloco informativo;
- cobertura completa mantém `grounded=true`;
- cobertura incompleta aciona o único retry de reparo já existente;
- se o retry continuar incompleto, retorna fallback seguro com `grounded=false`;
- nenhum juiz semântico externo foi introduzido;
- nenhuma mudança no retrieval/corpus/Qdrant.

Próximo passo: validar a nova CI e executar novamente os self-checks de grounding/cobertura. Depois, testar um chat real apenas com fonte oficial para observar o gate em runtime sem expor CHATSCM ao Gemini.


### Falha real observada e correção — Gemini 503

Na validação real da etapa 2 da 0.5.19:

- `ragtest-check-grounding`: PASS;
- `ragtest-check-grounding-coverage`: PASS;
- chat real com `--category direitos_saude --no-decompose`: falhou antes do gate com `google.genai.errors.ServerError: 503 UNAVAILABLE`, alta demanda temporária.

Registrado como Dificuldade TCC #15.

Correção implementada na mesma branch:

- retry de aplicação somente para 429/500/502/503/504;
- até 2 retries adicionais por padrão;
- backoff exponencial curto e configurável;
- erro de domínio `LLMServiceUnavailableError` após esgotamento;
- API responde HTTP 503;
- CLI mostra mensagem curta, sem traceback;
- erros não transitórios não recebem retry.

Próximo passo: aguardar CI, rebuildar e repetir exatamente o chat oficial de direitos. Não reindexar Qdrant.


### Missão secundária 0.5.19 — provider local Ollama

Ambiente local validado:

    Ollama: 0.34.2
    qwen3:4b: instalado, 2.5 GB, 100% GPU em contexto 4096
    qwen3:8b: instalado, 5.2 GB, Q4_K_M, 8.2B parâmetros
    qwen3:8b contexto 4096: 30% CPU / 70% GPU
    qwen3:8b contexto 8192: 36% CPU / 64% GPU
    Docker -> Ollama: acesso confirmado em http://host.docker.internal:11434

O qwen3:4b vazou reasoning no `message.content` mesmo com `think=false` e `/no_think`; registrado como Dificuldade #16.

O qwen3:8b respeitou `think=false` no CLI e na API e respondeu normalmente em contexto 8192. Ele passa a ser o baseline local.

D020: integração por provider explícito:

    LLM_PROVIDER=gemini
    ou
    LLM_PROVIDER=ollama

Ollama defaults:

    OLLAMA_BASE_URL=http://host.docker.internal:11434
    OLLAMA_MODEL=qwen3:8b
    OLLAMA_CONTEXT_WINDOW=8192
    OLLAMA_THINK=false
    OLLAMA_REQUEST_TIMEOUT_SECONDS=180

Sem fallback automático nesta etapa. A intenção é permitir comparação controlada do mesmo RAG entre Gemini e Qwen3 8B.

Próximo teste após CI/rebuild: definir `LLM_PROVIDER=ollama`, executar `ragtest-runtime-info --skip-qdrant` e repetir a pergunta oficial de direitos com `--category direitos_saude --no-decompose`. Não reindexar.


### Primeira validação RAG real com Qwen3 8B — aguardando diagnóstico

A validação local do provider Ollama foi executada com `LLM_PROVIDER=ollama`, `qwen3:8b`, `OLLAMA_CONTEXT_WINDOW=8192`, `OLLAMA_THINK=false` e `LLM_MAX_OUTPUT_TOKENS=4096`.

Verificado:

- `/health` retornou versão 0.5.19;
- `ragtest-runtime-info --skip-qdrant` confirmou provider/modelo/configuração esperados;
- `ragtest-check-grounding`: PASS;
- `ragtest-check-grounding-coverage`: PASS;
- o retrieval real para "Quais são os direitos da pessoa usuária da saúde?" com `--category direitos_saude --no-decompose` retornou cinco páginas da Carta oficial.

Falha observada:

- execução do chat levou aproximadamente seis minutos;
- `citation_retry_count=1`, portanto houve geração inicial + uma geração de reparo;
- ambas não produziram saída aceita pelo gate;
- resultado final: `grounded=false`, sem `citation_ids`, com fallback seguro.

Registrado como Dificuldade TCC #17.

Diagnóstico atual: retrieval e validadores determinísticos estão funcionando no cenário observado, mas o provider não expõe ainda os metadados de timing/tokenização retornados pelo Ollama nem preserva para diagnóstico as respostas rejeitadas pelo gate. A causa exata da latência e da reprovação estrutural ainda é hipótese e não deve ser tratada como corrigida.

O teste controlado seguinte alterou somente `LLM_MAX_OUTPUT_TOKENS` de 4096 para 512. O resultado manteve `citation_retry_count=1`, `grounded=false` e as mesmas cinco fontes recuperadas, mas reduziu o tempo total para 158,5 s. Isso verifica que o orçamento de saída influencia fortemente a latência, mas não explica nem corrige a reprovação do gate.

Um teste direto do `qwen3:8b` fora do RAG mediu 254 tokens em 28,68 s, com 8,94 tokens/s; o tempo de avaliação do prompt curto foi de aproximadamente 0,21 s e o de geração de saída, 28,42 s.

Instrumentação implementada na mesma branch, sem alterar o comportamento funcional:

- `OllamaProvider` passa a preservar métricas por geração: duração total/carga, tokens e duração do prompt, tokens e duração de saída, tokens/s e `done_reason`;
- o CLI passa a mostrar o diagnóstico estrutural de cada tentativa do gate: validade, sintaxe, cobertura, blocos citados/total e motivo da reprovação;
- respostas brutas rejeitadas não são persistidas nem impressas;
- CI verificada: Ruff `All checks passed!`; pytest `92 passed, 4 warnings`.

Próxima ação: atualizar/rebuildar o ambiente local e repetir a mesma pergunta com override temporário de 512 tokens para observar as novas métricas. Não reindexar Qdrant e não fazer merge do PR #13.


### Reteste do Gemini após período de 503

O mesmo chat oficial foi executado com override temporário `LLM_PROVIDER=gemini`, sem alterar o `.env`.

Resultado observado:

- o Gemini recebeu um erro transitório 503 na primeira tentativa;
- o retry de aplicação entrou em ação após 1 segundo;
- a chamada subsequente conseguiu prosseguir;
- o retrieval retornou as mesmas cinco páginas da Carta oficial;
- o chat terminou com `grounded=false`, `citation_retry_count=1` e sem `citation_ids`.

Conclusão atual:

- o Gemini está novamente acessível, mas ainda apresenta oscilação transitória;
- o retry da Dificuldade #15 funcionou no cenário real;
- como Gemini e Qwen3 8B chegaram ao mesmo fallback estrutural, a investigação do grounding passa a priorizar o contrato compartilhado de prompt/gate, não um provider específico;
- registrado como Dificuldade TCC #18;
- Gemini pode voltar a ser o provider principal de desenvolvimento, com Ollama como contingência manual; fallback automático continua fora do escopo desta etapa para preservar rastreabilidade.

Próxima ação: atualizar/rebuildar a imagem com a instrumentação já implementada e repetir o mesmo teste com Gemini para capturar `Citation validation attempts`. Não reindexar Qdrant e não fazer merge do PR #13.


### Diagnóstico do gate após instrumentação — heading Markdown e repair direcionado

O reteste real com Gemini usando a instrumentação mostrou:

    tentativa 1: syntax=yes, coverage=0.786, blocks=22/28
    tentativa 2: syntax=yes, coverage=0.767, blocks=23/30
    resultado: grounded=false, citation_retry_count=1

A investigação encontrou dois pontos no contrato compartilhado do gate:

1. headings Markdown como `## Direitos da pessoa usuária` eram tratados como claim blocks quando não terminavam em dois-pontos;
2. o chamado "repair" não recebia a resposta anterior nem o motivo específico da falha e, portanto, regenerava do zero.

Registrado como Dificuldade TCC #19.

Correção implementada e verificada em CI (`All checks passed!`; `94 passed, 4 warnings`), aguardando validação real:

- headings Markdown iniciados por `#` não contam como afirmação informativa;
- parágrafos e itens continuam exigindo citações válidas;
- o retry recebe a resposta anterior e o motivo da validação;
- o modelo é instruído a revisar a resposta existente sem acrescentar novas afirmações;
- testes adicionados para os dois comportamentos.

Próxima ação: aguardar CI, rebuildar e repetir exatamente o chat oficial com Gemini. Não reindexar Qdrant e não fazer merge do PR #13.


### Nova oscilação do Gemini — 429 após retries

Após o rebuild com a correção do gate, duas execuções do chat oficial com `LLM_PROVIDER=gemini` não chegaram à geração: ambas receberam `429` na chamada inicial e nos dois retries configurados (1 s e 2 s), terminando com `LLMServiceUnavailableError`.

Isso não invalida a correção do gate; o teste real dessa correção continua pendente porque o provider externo não chegou a produzir resposta. A Dificuldade #15 foi atualizada para registrar que a indisponibilidade do Gemini agora também se manifesta como rate limit/cota, além do 503 já observado.

Próxima decisão: avaliar um terceiro provider de desenvolvimento/fallback manual sem alterar corpus, retrieval ou Qdrant. O Ollama continua disponível localmente; nenhum fallback automático foi habilitado.


### Integração Groq / GPT-OSS 120B

Após novas falhas 429 do Gemini, foi iniciada a integração de um terceiro provider explícito para desenvolvimento e contingência manual:

    LLM_PROVIDER=groq
    GROQ_MODEL=openai/gpt-oss-120b
    GROQ_BASE_URL=https://api.groq.com/openai/v1
    GROQ_REASONING_EFFORT=low

A integração preserva a interface `LLMProvider`, corpus, retrieval, Qdrant e gate de grounding. Não existe fallback automático nesta etapa.

Características implementadas:

- API OpenAI-compatible da Groq via HTTP, sem nova dependência Python;
- `include_reasoning=false` para não expor reasoning;
- citações nativas da Groq desabilitadas para preservar o contrato `[n]` do RagTest;
- retry limitado para 429/498/500/502/503/504;
- respeito a `Retry-After` com espera limitada;
- métricas de prompt/output e latência expostas ao CLI;
- chave somente via `GROQ_API_KEY` no ambiente;
- runtime-info identifica provider/modelo/configuração.

D021 registra a decisão. A validação real deve usar somente a categoria oficial `direitos_saude`; CHATSCM continua proibido em providers externos antes de revisão manual de privacidade.

CI da integração Groq verificada: Ruff `All checks passed!`; pytest `101 passed, 4 warnings`. Próximo passo: adicionar a chave Groq somente no `.env` local, rebuildar e testar primeiro o `runtime-info` e depois o chat RAG oficial. Não reindexar Qdrant.


### Primeira validação real da Groq — Cloudflare 1010

O `runtime-info` confirmou corretamente:

    llm_provider: groq
    llm_model: openai/gpt-oss-120b
    groq_base_url: https://api.groq.com/openai/v1
    groq_reasoning_effort: low

As duas primeiras chamadas reais ao chat falharam antes da geração com `HTTP 403` e `error code: 1010`. O traceback mostrou o bloqueio em `urllib.request.urlopen`.

Diagnóstico: Cloudflare 1010 indica bloqueio por assinatura do cliente HTTP. O provider usava o `User-Agent` padrão do `urllib`, portanto o erro não prova chave inválida e não chegou ao modelo. Registrado como Dificuldade TCC #20.

Correção implementada:

- `GroqProvider` envia `Accept: application/json`;
- envia `User-Agent: Mozilla/5.0 (compatible; RagTest/0.5.19)`;
- teste de regressão exige `User-Agent` explícito;
- nenhuma alteração em corpus, retrieval, Qdrant, prompt ou modelo.

CI da correção verificada: Ruff verde; pytest `102 passed, 4 warnings`. Próxima ação: rebuildar a imagem e repetir apenas o teste curto Groq com 512 tokens. Se ele chegar ao modelo, então executar a pergunta completa. Não reindexar Qdrant.


### Groq chegou ao GPT-OSS 120B — transporte validado, citações pendentes

Após a correção do User-Agent, o teste curto com `LLM_PROVIDER=groq`, `openai/gpt-oss-120b`, duas fontes oficiais e 512 tokens chegou ao modelo com sucesso.

Resultado:

    geração 1: 1,12 s | 512 tokens | ~478,05 tok/s | done_reason=length
    geração 2: 0,94 s | 409 tokens | ~478,22 tok/s | done_reason=stop
    citation validation 1: syntax=no | coverage=0.000 | 0/9
    citation validation 2: syntax=no | coverage=0.000 | 0/9
    grounded=false

A Dificuldade #20 fica validada como corrigida em runtime: o 403/1010 desapareceu.

Nova Dificuldade #21: o GPT-OSS 120B não produziu nenhuma citação literal `[n]` em nenhuma das duas tentativas. Como o repair terminou por `stop`, a falha não pode ser atribuída somente ao teto de 512 tokens.

Próxima ação: executar uma chamada direta mínima ao `GroqProvider`, sem retrieval, solicitando explicitamente uma frase com `[1]`. Não alterar prompt/gate antes desse isolamento. Não reindexar Qdrant.


### Teste literal de citação no GPT-OSS 120B

Uma chamada direta ao `GroqProvider`, sem retrieval e com `LLM_MAX_OUTPUT_TOKENS=256`, solicitou exatamente:

    Direito teste [1].

O modelo retornou exatamente essa frase, incluindo `[1]`.

Conclusão: o GPT-OSS 120B e o `GroqProvider` conseguem obedecer ao formato literal de citação. A Dificuldade #21 fica restrita ao caminho RAG completo; não há evidência para trocar o provider nem para afrouxar o gate.

Próxima ação: capturar uma geração RAG bruta antes da validação, usando somente a categoria oficial `direitos_saude`, para observar o efeito do prompt/contexto. Não reindexar Qdrant.


### Causa da falha de citações do GPT-OSS isolada — variante Unicode

A geração RAG bruta do GPT-OSS 120B revelou que o modelo estava citando as fontes, mas emitia:

    【1】
    【2】

em vez do formato canônico:

    [1]
    [2]

Isso explica por que o gate reportava `syntax=no`, `coverage=0.000` e 0 blocos citados apesar de a resposta visualmente conter referências válidas.

Correção implementada:

- normalização estrita `【n】 -> [n]`;
- aplicada imediatamente após a geração inicial e após o repair;
- `extract_citation_ids` também reconhece a variante por normalização;
- IDs continuam obrigados a estar dentro do intervalo de fontes;
- blocos informativos continuam exigindo citação;
- resposta final usa o formato canônico ASCII;
- testes reproduzem o caso do GPT-OSS.

CI verificada: Ruff `All checks passed!`; pytest `105 passed, 4 warnings`.

Próxima ação: rebuildar e repetir o chat oficial curto com Groq usando 1024 tokens. A correção ainda precisa de validação real antes de marcar a Dificuldade #21 como resolvida em runtime. Não reindexar Qdrant.


### Dificuldade #22 — introdução estrutural de lista no gate

Após a normalização `【n】 -> [n]`, o reteste real com Groq avançou para:

    syntax=yes
    coverage=0.889
    blocks=8/9
    done_reason=stop nas duas gerações

A regressão reproduziu a causa: uma introdução longa terminada em dois-pontos antes de uma lista citada era contada como claim independente.

Correção implementada:

- uma linha terminada em `:` só é tratada como introdução estrutural quando o próximo bloco não vazio é um item real de lista;
- os itens continuam obrigados a conter citações válidas;
- demais frases informativas continuam sujeitas ao gate;
- CI verificada: Ruff `All checks passed!`; pytest `106 passed, 4 warnings`.

Próxima ação: rebuildar e repetir exatamente o mesmo chat curto com Groq e 1024 tokens. Não reindexar Qdrant.


### Reteste após correção da introdução de lista

O chat curto com Groq/GPT-OSS 120B e 1024 tokens foi repetido após a correção contextual da introdução de lista.

Resultado real permaneceu:

    tentativa 1: syntax=yes | coverage=0.889 | blocks=8/9
    tentativa 2: syntax=yes | coverage=0.889 | blocks=8/9
    grounded=false
    done_reason=stop nas duas gerações

Conclusão: a regra de introdução de lista está coberta por teste e CI, mas não explica sozinha o bloco uncited do caso real. A Dificuldade #22 continua aberta em runtime.

Próxima ação: capturar novamente a resposta RAG bruta e comparar linha a linha com a classificação do gate para identificar exatamente qual bloco está sendo contado como uncited. Não alterar o gate até essa identificação.


### Dificuldade #23 — repair agora recebe o bloco uncited exato

O diagnóstico linha a linha isolou o bloco real que causava `8/9`:

    Esses direitos são extraídos dos documentos citados e refletem as garantias previstas para as pessoas usuárias dos serviços de saúde.

A introdução da lista estava corretamente classificada como estrutural, e os dez itens estavam citados. Portanto, a hipótese anterior de que a introdução explicava o caso real foi descartada.

Problema identificado: o repair recebia apenas um motivo genérico de cobertura incompleta, sem o texto do bloco que precisava ser corrigido.

Correção implementada:

- `CitationCoverage` preserva `uncited_blocks`;
- o repair recebe uma seção `BLOCOS SEM CITAÇÃO VÁLIDA`;
- o modelo deve citar o bloco somente se houver fonte que o sustente ou removê-lo se for desnecessário;
- nenhuma regra do gate foi relaxada;
- TDD confirmado: os novos testes falharam antes da implementação;
- CI após implementação: Ruff `All checks passed!`; pytest `106 passed, 4 warnings`.

Próxima ação: rebuildar e repetir exatamente o mesmo chat curto com Groq e 1024 tokens. O resultado esperado é primeira tentativa possivelmente 8/9 e segunda tentativa 100%, ou primeira tentativa já 100% se a geração variar. Não reindexar Qdrant.


### Pós-processamento determinístico após repair — D022 / Dificuldade #24

O reteste real do repair localizado ainda retornou:

    tentativa 1: syntax=yes | coverage=0.889 | blocks=8/9
    tentativa 2: syntax=yes | coverage=0.889 | blocks=8/9
    done_reason=stop nas duas gerações

Como o bloco uncited já era explicitamente enviado ao repair, a estratégia baseada apenas em prompting foi considerada insuficiente.

Implementação atual:

1. geração inicial;
2. validação estrutural;
3. um único repair com blocos uncited explícitos;
4. nova validação;
5. se a sintaxe estiver válida, houver pelo menos um claim citado e restarem claims sem citação, remover deterministicamente apenas esses claims;
6. revalidar;
7. aceitar somente se a cobertura final for 100%; caso contrário, fallback seguro.

O CLI passa a mostrar:

    stage=initial
    stage=repair
    stage=postprocess

`citation_retry_count` continua contando somente retries de LLM, portanto permanece 1 quando o postprocess é usado.

TDD confirmado e CI verificada: Ruff `All checks passed!`; pytest `108 passed, 3 warnings`.

Próxima ação: rebuildar e repetir o mesmo chat curto com Groq e 1024 tokens. O resultado esperado, caso o modelo repita o padrão observado, é initial 8/9, repair 8/9, postprocess 100% e `Grounded: yes`. Não reindexar Qdrant.


### Groq/GPT-OSS 120B — grounding estrutural validado em runtime

O reteste após a D022 confirmou o fluxo completo:

    Grounded: yes
    Citation ids: [1, 2]
    Citation retries: 1

    [1] stage=initial     valid=no  syntax=yes coverage=0.889 blocks=8/9
    [2] stage=repair      valid=no  syntax=yes coverage=0.889 blocks=8/9
    [3] stage=postprocess valid=yes syntax=yes coverage=1.000 blocks=8/8

Métricas observadas:

    geração inicial: 1,14 s | 516 tokens | ~476,58 tok/s | stop
    repair:          1,63 s | 488 tokens | ~316,53 tok/s | stop

A resposta final manteve apenas os oito blocos citados e removeu o claim final sem fonte.

Status:

- `GroqProvider`: verificado em runtime;
- `openai/gpt-oss-120b`: verificado para geração RAG oficial;
- normalização `【n】 -> [n]`: verificada em runtime;
- repair localizado: implementado, mas insuficiente sozinho no caso observado;
- pós-processamento determinístico D022: verificado em runtime;
- grounding estrutural final: verificado com `coverage=1.000`;
- grounding semântico/entailment de cada claim para a fonte citada: ainda não verificado automaticamente.

O Groq pode ser usado como provider principal de desenvolvimento enquanto o Gemini estiver limitado, mantendo a seleção explícita e sem fallback automático. CHATSCM continua proibido em providers externos antes da revisão manual de privacidade.


### D023 — otimização de cota validada em CI

Três testes reais com fontes oficiais distintas passaram com grounded=true: direitos_saude, vacinacao/idoso e gestacao/saude bucal. Nos três houve citation_retry_count=1.

Foi implementado postprocess antes do repair apenas quando a resposta inicial tem sintaxe válida, exatamente um claim sem citação, pelo menos um claim citado e cobertura >= 0,80. A poda é aceita somente após revalidação em 100%; caso contrário, o repair normal continua.

TDD confirmado: o novo teste falhou primeiro com duas chamadas ao LLM. Após a implementação, CI verde com 109 testes aprovados e 4 warnings.

Próxima ação: rebuildar e repetir um único teste real com Groq. Esperado no padrão conhecido: grounded=true e citation_retry_count=0. Não reindexar Qdrant.


### D023 — validação real concluída

O reteste real de direitos_saude após a otimização observou:

    grounded=true
    citation_ids=[1,2]
    citation_retry_count=0

A resposta final manteve os oito direitos citados e não precisou de uma segunda geração Groq. Isso confirma a execução sem repair externo, mas o JSON da API não expõe citation_validation_attempts; portanto, não distingue se a geração inicial já estava totalmente válida ou se o postprocess-before-repair foi acionado. A lógica da D023 permanece verificada por TDD/CI; o caminho interno específico ainda não foi observado diretamente em runtime.

Status da 0.5.19: grounding estrutural, normalização de citações, repair localizado, postprocess determinístico e otimização de cota estão implementados e verificados em CI; os fluxos principais foram validados em runtime com fontes oficiais de direitos_saude, vacinacao/idoso e gestacao/saude bucal. Grounding semântico/entailment automático continua fora do escopo validado desta versão.


### Auditoria final do PR #13 — proteção contra poda excessiva

A auditoria identificou que o caminho pós-repair ainda aceitava poda com qualquer cobertura, desde que existisse ao menos um claim citado. Um teste novo reproduziu um caso de 25% de cobertura que era reduzido a um único claim e aceito como grounded=true.

Correção final:

- a regra conservadora passa a valer antes e depois do repair;
- sintaxe de citação válida;
- exatamente 1 claim uncited;
- pelo menos 1 claim citado;
- cobertura >= 0,80;
- revalidação obrigatória em 100%;
- fora dessas condições, o fluxo segue para repair ou fallback.

TDD: RED com 1 falha e 109 testes passando; GREEN após correção com Ruff verde e 110 testes aprovados, 4 warnings.

A auditoria também confirmou que o PR #13 não altera data/source, corpus, OCR, chunks, embeddings ou a collection Qdrant. README e metadados do pacote foram atualizados para refletir Groq, múltiplos providers e o fluxo final da 0.5.19.


### Início da 0.5.20 — observabilidade de cota Groq

Branch: `feature/groq-rate-limits-0.5.20`  
PR: #14 (draft)

Escopo inicial:

- preservar headers oficiais de rate limit no GroqProvider;
- capturar os mesmos dados também em HTTP 429;
- exibir RPD/TPM e resets no ragtest-chat;
- não introduzir fallback automático ainda;
- não alterar corpus, retrieval, embeddings ou Qdrant.

TDD observado:

1. RED: GroqProvider não possuía `rate_limits` — 1 falha / 110 passes;
2. GREEN: captura em resposta normal — 111 passes;
3. RED do CLI: formatter inexistente — 1 falha / 111 passes;
4. GREEN do CLI — 112 passes;
5. RED 429: snapshot permanecia None — 1 falha / 112 passes;
6. GREEN 429 — 113 passes.

Semântica dos headers:

- requests: RPD;
- tokens: TPM;
- resets preservados como texto retornado pela Groq;
- TPD diário não é fornecido por esses headers.

Próxima validação: rebuild local e uma única chamada real com Groq para confirmar que o CLI mostra os headers recebidos do serviço.


### 0.5.20 — rate limits verificados em runtime

Validação real com Groq/GPT-OSS 120B:

    app_version: 0.5.20
    python_package_ragtest: 0.5.20
    llm_provider: groq
    llm_model: openai/gpt-oss-120b
    llm_max_output_tokens: 1024

Grounding observado:

    initial: coverage=0.875, blocks=7/8
    postprocess: coverage=1.000, blocks=7/7
    citation_retry_count=0
    grounded=yes

Isso fornece evidência direta em runtime de que o caminho initial -> postprocess da D023 foi acionado sem segunda geração externa.

Rate limits observados:

    requests_rpd: 999/1000 reset=1m26.4s
    tokens_tpm: 6069/8000 reset=14.482s

A captura de headers da D024 está, portanto, verificada em runtime. Os resets são preservados exatamente como retornados pela Groq; não são reinterpretados localmente. TPD diário continua não disponível nesses headers.


## Diretriz oficial do TCC — escopo alinhado ao e-mail do orientador

### Título da proposta

Desenvolvimento de Módulo Conversacional Baseado em RAG para Apoio ao Letramento em Saúde e Acesso a Serviços no Aplicativo "Se Cuida Mulher".

### Interpretação arquitetural consolidada

O artefato central do TCC é um módulo conversacional RAG reutilizável e independente da interface cliente. O backend, pipeline de ingestão, recuperação, grounding, auditoria e integração com provedores de LLM não devem depender especificamente do aplicativo Se Cuida Mulher nem de um único chatbot/front-end.

O Se Cuida Mulher é o sistema-alvo de integração previsto pela proposta. Antes dessa integração, o projeto pode e deve possuir uma interface de demonstração própria para validar funcionalmente o módulo conversacional, apresentar o artefato na banca e exercitar o contrato da API. Essa interface é um cliente do módulo, não parte inseparável do núcleo RAG.

Arquitetura desejada:

    Cliente de chat multiplataforma
        -> REST (inicialmente) / WebSocket apenas se necessário
        -> FastAPI
        -> Orquestração RAG
        -> Retrieval / Grounding / Auditoria
        -> Qdrant
        -> Provider de LLM configurável

Essa separação deve permitir substituir o cliente de demonstração pelo Se Cuida Mulher ou por outro chatbot sem reescrever o núcleo do RAG.

### Objetivo geral oficial

Desenvolver e integrar um módulo de chat inteligente baseado em arquitetura RAG para o aplicativo Se Cuida Mulher, atuando como ferramenta de suporte ao letramento informacional e orientação de agendamento de serviços de saúde.

### Objetivos específicos e situação atual

1. Pipeline de ingestão e processamento: extração, limpeza, chunking e vetorização de documentos do SUS, bulários e fluxogramas. O RagTest já possui pipeline funcional, OCR, chunking, embeddings e ingestão no Qdrant.

2. Orquestração de recuperação e contexto: busca vetorial por intenção da usuária e recuperação de trechos normativos. O projeto já possui retrieval dense-rerank, sparse/BM25 disponível, multi-query e filtros por metadados.

3. Resiliência e segurança: mitigação de alucinações e logs/auditoria estruturados. O projeto já possui grounding estrutural por citações, repair controlado, postprocess determinístico, fallback seguro, métricas de provider e rate limits. Segurança, privacidade/LGPD e auditoria persistente ainda precisam de uma fase própria.

4. Interface de conversação reativa: ainda é a principal lacuna funcional do artefato. Deve suportar chat fluido, responsividade, rich-text, fontes/links e futuramente gatilhos de lembrete/agendamento quando o contrato de integração estiver definido.

### Stack tecnológica alinhada à proposta

- Backend: Python + FastAPI.
- Banco vetorial: Qdrant.
- Orquestração RAG: implementação própria em Python, utilizando componentes do ecossistema LangChain quando aplicável; não reescrever o backend apenas para aumentar dependência de framework.
- Front-end/aplicativo: cliente multiplataforma desacoplado do backend; React Native/Expo ou Flutter são compatíveis com a proposta. A decisão deve priorizar reaproveitamento e integração futura.
- Comunicação inicial: REST/JSON usando o contrato já existente em /v1/chat. WebSocket fica reservado para uma necessidade real de streaming ou comunicação bidirecional contínua.
- Infraestrutura: Docker e Docker Compose para backend, Qdrant e serviços aplicáveis; o cliente mobile pode usar seu fluxo nativo de build/desenvolvimento.

### Fases da proposta e mapeamento do projeto

Fase 1 — levantamento e domínio: parcialmente concluída para o corpus técnico atual; fluxos locais de agendamento ainda precisam ser modelados quando as fontes institucionais correspondentes estiverem disponíveis.

Fase 2 — pipeline de dados e RAG: estágio avançado e funcional. Retrieval, ingestão, embeddings, Qdrant, avaliação e grounding foram implementados e testados.

Fase 3 — API e integração com chat: API /v1/chat funcional; falta evoluir o contrato conversacional para sessões/histórico apenas se isso for necessário ao protótipo e à integração final.

Fase 4 — interface e testes funcionais: próxima prioridade prática. Construir um cliente demonstrável independente, validar UX e fluxos e só depois adaptar/integrar ao Se Cuida Mulher oficial.

### Entregáveis oficiais

- Artefato de software funcional em ambiente simulado ou homologado.
- Repositório GitHub com backend RAG, ingestão, testes automatizados e cliente de demonstração/integracão.
- Monografia descrevendo arquitetura, decisões de engenharia, métricas de retrieval, grounding, desempenho, limitações e contribuição tecnológica.

### Regra de escopo para próximas versões

O RagTest deve continuar funcionando de forma independente de qualquer frontend específico. Interfaces futuras devem consumir contratos públicos da API. Nenhuma regra de negócio do RAG deve depender de componentes visuais, navegação ou estado do Se Cuida Mulher. A integração oficial deve ocorrer como adaptação do cliente/contrato, não como reescrita do backend.


## Protocolo de continuidade entre chats

Este arquivo deve ser mantido como fonte principal de retomada do projeto. Ao concluir uma etapa relevante, atualizar sempre:

1. estado atual da versão/branch/PR;
2. o que foi implementado;
3. o que foi verificado por CI/runtime;
4. o que permanece hipótese ou aguardando validação;
5. próximo passo exato;
6. posição atual no roadmap geral;
7. decisões arquiteturais e dificuldades novas;
8. comandos de validação necessários para o usuário, quando houver.

### Padrão de status usado nas conversas

- implementado: código/documentação já alterados;
- aguardando validação: alteração feita, mas falta CI ou runtime;
- verificado: existe evidência de CI, teste automatizado ou runtime real;
- hipótese: explicação ainda não confirmada por evidência.

### Fluxo de trabalho preferido

    alteração
        -> comandos/testes
        -> usuário executa quando runtime local é necessário
        -> logs retornam ao chat
        -> análise
        -> próxima alteração

Não declarar sucesso sem evidência. Mudanças funcionais devem seguir TDD RED -> GREEN sempre que aplicável. Evitar vários comandos/blocos independentes ao mesmo tempo quando o próximo passo depende do resultado anterior.

### Regra de comunicação de progresso

Após cada avanço relevante, informar explicitamente ao usuário:

- versão atual;
- etapa atual;
- percentual/posição qualitativa no roadmap quando isso ajudar;
- o que acabou de ser concluído;
- o que vem imediatamente depois;
- se há algo aguardando ação do usuário.

## Roadmap consolidado do TCC

### Estado atual

Versão integrada em main: 0.5.22.
Versão em desenvolvimento: 0.5.23.
Branch atual de trabalho: `feature/richtext-sources-0.5.23`.
PR atual: #18 draft.

A prioridade da 0.5.21 foi redefinida após alinhamento com o e-mail completo do orientador. O scaffold Next.js criado inicialmente no PR #16 foi substituído por React Native + Expo + TypeScript. O frontend demonstrativo agora segue a linha multiplataforma sugerida no TCC e continua desacoplado do backend.

### Roadmap

    0.5.21  Scaffold React Native + Expo + TypeScript + CI + contrato /v1/chat [CONCLUÍDA]
       ->
    0.5.22  Chat funcional consumindo FastAPI por REST [CONCLUÍDA]
       ->
    0.5.23  Rich-text, citações, fontes e links [ATUAL]
       ->
    0.5.24  UX mobile, loading, erros, estados de grounding/fallback
       ->
    0.6.x   Sessões conversacionais controladas
       ->
    0.7.x   Auditoria estruturada, privacidade/LGPD e segurança
       ->
    0.8.x   Fluxos institucionais de serviços/agendamento + lembretes
       ->
    0.9.x   Avaliação experimental e testes de usabilidade
       ->
    1.0     Artefato funcional/documentado pronto para apresentação
       ->
    etapa posterior: integração no Se Cuida Mulher oficial

### Posição atual no roadmap

O núcleo RAG/backend está em estágio avançado e funcional. A 0.5.22 já conectou e validou o cliente Expo ponta a ponta com o `/v1/chat`. A prioridade atual da 0.5.23 é melhorar a apresentação: renderizar Markdown, mostrar cartões de fontes citadas e preservar a distinção entre fontes recuperadas e fontes realmente citadas.

## Comportamento atual para novos documentos no corpus

O diretório configurado por `SOURCE_DIR` (em Docker, `/app/data/source`; no repositório, `data/source`) é a origem do corpus. O loader descobre recursivamente arquivos `.pdf` e `.docx` em qualquer subpasta suportada.

Adicionar um arquivo ao diretório NÃO o torna consultável imediatamente. O chat consulta apenas os chunks já indexados na collection Qdrant. Portanto, após adicionar, alterar ou remover arquivos, é necessário sincronizar o corpus com o índice.

Fluxo seguro atual:

    1. colocar/remover/alterar PDF ou DOCX em data/source/<categoria>/...
    2. executar `ragtest-plan-ingestion-sync` ou `ragtest-sync-ingestion` sem --apply para dry-run
    3. revisar missing/stale/orphan sources e erros de carregamento
    4. executar `ragtest-sync-ingestion --apply`
    5. o sistema faz upsert dos chunks novos/alterados antes de excluir pontos obsoletos
    6. o próprio comando revalida a collection e exige estado final em sync
    7. somente depois disso o novo conteúdo fica disponível para retrieval e chat

Proteções atuais: recusa corpus vazio; recusa escrita se houver erro de carregamento; não usa recreate; IDs são determinísticos; exclusões ocorrem apenas após upsert de substituições; verificação final é obrigatória.

Metadados: a primeira pasta relativa abaixo de `data/source` vira `category`; alguns públicos são inferidos pelo caminho/nome do arquivo (por exemplo gestante, idoso, adulto). Arquivos soltos diretamente na raiz recebem category `uncategorized`.

Não existe atualmente watcher/daemon que monitore automaticamente a pasta e faça ingestão ao detectar novos arquivos. Automatizar isso pode ser uma evolução futura, mas deve preservar o mesmo fluxo de planejamento, validação e auditoria antes de mutar Qdrant.


### Checkpoint da 0.5.21 — scaffold Expo e contrato REST

Estado da versão: 100% concluída e verificada.

Implementado:

- Expo SDK 57 estável;
- React Native 0.86 / React 19.2;
- TypeScript;
- app multiplataforma Android/iOS/web;
- primeira tela do Assistente de Saúde;
- campo de pergunta e botão Enviar;
- contrato TypeScript equivalente ao schema FastAPI;
- suporte opcional a min_score;
- sendChatMessage para POST /v1/chat;
- Jest + jest-expo + React Native Testing Library;
- typecheck TypeScript integrado à CI;
- versão do repositório/backend/frontend alinhada em 0.5.21;
- documentação do frontend atualizada;
- decisões D025 e D026 registradas.

TDD observado:

1. RED da tela: App inexistente; teste de contrato existente passou;
2. GREEN da tela: 2 suites / 2 testes passaram;
3. RED do cliente REST: sendChatMessage inexistente; App permaneceu verde;
4. GREEN do cliente REST: 2 suites / 3 testes passaram.

Última CI funcional antes do bump final de versão:

    frontend: 2 suites, 3 testes aprovados
    frontend typecheck: success
    backend: 113 passed, 4 warnings
    Ruff: All checks passed!

Verificado:

- CI final após alinhamento da versão 0.5.21;
- frontend: 2 suites / 3 testes aprovados;
- TypeScript typecheck: success;
- backend: 113 passed, 4 warnings;
- Ruff: All checks passed!.

Verificação de runtime local concluída:

- `npm install`: concluído;
- `npm test`: 2 suites / 3 testes aprovados;
- `npm run typecheck`: concluído sem erros;
- `npm run web`: Metro Bundler iniciado com sucesso;
- Expo Web disponível em `http://localhost:8081`;
- interface visual abriu corretamente no navegador;
- campo de pergunta e botão Enviar renderizados;
- comportamento esperado confirmado: botão ainda não chama o backend nesta versão.

Observação de segurança do ambiente local:

- o npm reportou 10 vulnerabilidades de severidade moderada em dependências;
- não executar `npm audit fix --force` automaticamente;
- classificar dependências diretas/transitivas antes de qualquer correção;
- revisão fica registrada para a fase de segurança/produção, sem bloquear o protótipo atual.

Próximo passo exato:

1. fechar a 0.5.21 no PR #16;
2. após merge autorizado, abrir a 0.5.22 em branch limpa;
3. conectar o botão Enviar ao cliente `sendChatMessage`;
4. configurar a URL do FastAPI por ambiente;
5. renderizar pergunta, loading e resposta real do `POST /v1/chat`;
6. validar o fluxo ponta a ponta com o backend local.

Observação de dependências:

O npm install da CI reportou vulnerabilidades transitivas moderadas no ecossistema do frontend. Não executar npm audit fix --force automaticamente. A análise de segurança das dependências será feita de forma deliberada antes da versão de apresentação/produção; nenhuma vulnerabilidade de severidade alta foi usada como evidência de bloqueio nesta etapa.

Posição no roadmap:

    0.5.20  observabilidade Groq ............ concluída/merged
    0.5.21  scaffold Expo + contrato REST ... em validação final
    0.5.22  chat real -> FastAPI ............ próximo
    0.5.23  rich-text/fontes/citações ....... futuro
    0.5.24  UX/erros/grounding .............. futuro
    0.6.x   sessões .......................... futuro
    0.7.x   auditoria/LGPD/segurança ........ futuro
    0.8.x   agendamento/lembretes ........... futuro
    0.9.x   avaliação/usabilidade ........... futuro
    1.0     artefato de apresentação ........ futuro


### 0.5.21 — runtime local do cliente Expo verificado

Data da validação: 2026-09-21.

Ambiente do usuário:

    Windows
    branch: feature/chatbot-demo-frontend-0.5.21

Comandos executados:

    npm install
    npm test
    npm run typecheck
    npm run web

Resultados:

    Test Suites: 2 passed, 2 total
    Tests:       3 passed, 3 total
    TypeScript:  tsc --noEmit sem erros
    Metro:       iniciado com sucesso
    Web:         http://localhost:8081
    bundle web:  concluído

A interface foi observada visualmente no navegador e exibiu:

- identificação RagTest;
- título Assistente de Saúde;
- texto introdutório;
- card inicial "Olá! Como posso ajudar?";
- campo "Digite sua pergunta...";
- botão "Enviar".

O botão ainda não envia perguntas ao backend por desenho da versão. A conexão com FastAPI é escopo da 0.5.22.

Status final da 0.5.21:

    scaffold Expo/React Native ........ verificado
    TypeScript ........................ verificado
    contrato REST tipado .............. verificado por teste
    cliente sendChatMessage ........... verificado por teste
    primeira tela ..................... verificada em runtime
    backend ........................... inalterado
    corpus/Qdrant ..................... inalterados
    integração tela -> FastAPI ........ próxima versão (0.5.22)


### Início e checkpoint da 0.5.22 — integração Expo -> FastAPI

Base da versão:

    main validada/mesclada: 0.5.21
    merge 0.5.21: f369db053761b31175588d22ac586c56d4670746
    branch: feature/frontend-fastapi-0.5.22
    PR: #17 draft

Objetivo da 0.5.22:

Conectar a interface Expo ao backend real por REST, sem mover regras de RAG para o frontend e sem alterar corpus, embeddings ou Qdrant.

Implementado até este checkpoint:

- CORS configurável no FastAPI;
- origens padrão restritas a localhost:8081 e 127.0.0.1:8081;
- teste confirma preflight permitido e origem desconhecida não liberada;
- URL do backend configurável por EXPO_PUBLIC_RAG_API_BASE_URL;
- padrão de desenvolvimento web: http://localhost:8000;
- botão Enviar conectado a sendChatMessage;
- pergunta da usuária renderizada na tela;
- loading "Buscando resposta...";
- resposta textual da API renderizada;
- botão desabilitado para pergunta com menos de 2 caracteres;
- envio desabilitado durante chamada em andamento;
- erro de rede mostrado de forma amigável;
- ChatApiError criado para HTTP não-2xx com status e detail;
- exemplos de URL para web, Android emulator e dispositivo físico;
- backend/frontend/versionamento alinhados para 0.5.22;
- Dificuldade #28 registrada;
- D027 registrada.

TDD/CI observado:

1. RED CORS:
       OPTIONS /v1/chat -> 405
       1 failed, 114 passed, 6 warnings

2. GREEN CORS:
       115 passed, 6 warnings
       frontend 3/3
       Ruff verde

3. RED integração da tela:
       pergunta não aparecia após Enviar

4. implementação da tela:
       testes funcionais passaram, mas o teste usava eventos síncronos incompatíveis com RNTL 14;
       correção do teste para await fireEvent.changeText / await fireEvent.press.

5. typecheck:
       lógica funcional 4/4 passou;
       TS2591 em process.env;
       corrigido com @types/node + types node.

6. RED erro HTTP:
       Promise resolveu em HTTP 503 quando deveria rejeitar.

7. GREEN erro HTTP:
       ChatApiError implementado.

Decisão de compatibilidade:

- Expo Web no mesmo PC usa http://localhost:8000 por padrão;
- Android Emulator usa normalmente http://10.0.2.2:8000;
- dispositivo físico precisa apontar para o IP LAN da máquina;
- CORS só afeta clientes web em navegador; origens adicionais precisam ser explicitamente autorizadas;
- não usar allow_origins=["*"] como atalho.

Estado da 0.5.22: 100% concluída e verificada.

Aguardando:

- CI final do head consolidado;
- validação local ponta a ponta com Docker/FastAPI + Expo Web;
- confirmação visual de pergunta, loading e resposta RAG real.

Próximo passo exato:

1. confirmar CI final;
2. usuário atualizar branch feature/frontend-fastapi-0.5.22;
3. rebuildar/subir backend Docker sem recriar Qdrant;
4. iniciar Expo Web;
5. fazer uma pergunta oficial pela tela;
6. confirmar que a resposta real do /v1/chat aparece na interface;
7. registrar runtime e, se estiver tudo correto, fechar/mesclar 0.5.22.

Roadmap após este checkpoint:

    0.5.21  Expo + contrato REST ............ concluída/merged
    0.5.22  tela -> FastAPI real ............ atual (~85%)
    0.5.23  rich-text + fontes + citações ... próxima
    0.5.24  UX + erros + grounding .......... futura
    0.6.x   sessões .......................... futura
    0.7.x   auditoria/LGPD/segurança ........ futura
    0.8.x   agendamento/lembretes ........... futura
    0.9.x   avaliação/usabilidade ........... futura
    1.0     artefato final do TCC ........... futura


### Validação local 0.5.22 — tentativa não válida por branch local desatualizada

Data: 2026-09-21.

A primeira tentativa de runtime ponta a ponta não valida a 0.5.22.

Evidências do terminal:

    git switch feature/frontend-fastapi-0.5.22
    -> abortado por alteração local em frontend/tsconfig.json

    git pull --ff-only origin feature/frontend-fastapi-0.5.22
    -> abortado pelo mesmo arquivo

    npm test
    -> ragtest-frontend@0.5.21

    npm run web
    -> ragtest-frontend@0.5.21

A interface abriu, mas o botão Enviar não executou a chamada. Esse comportamento é esperado na 0.5.21 e não constitui falha do código 0.5.22.

Também foi observado:

    curl http://localhost:8000/health -> Empty reply from server
    curl http://localhost:8000/ready  -> Empty reply from server

Esses resultados foram obtidos antes de corrigir a branch local e, portanto, não devem ser usados para concluir falha do backend 0.5.22. Se persistirem após a atualização correta da branch, investigar com docker compose ps e logs da API.

Hipótese confirmada para o bloqueio de checkout: o Expo havia alterado localmente frontend/tsconfig.json em execução anterior. A próxima ação é inspecionar/descartar apenas essa alteração local, trocar para a branch 0.5.22 e confirmar a versão antes de qualquer novo teste.

Status da 0.5.22 permanece:

    implementação remota ............ verificada em CI
    runtime local ponta a ponta ..... aguardando validação válida
    PR #17 .......................... draft


### 0.5.22 — backend verificado em runtime local

Data: 2026-09-21.

Após corrigir a branch local, o backend 0.5.22 foi rebuildado e iniciado sem recriar volumes ou Qdrant.

Resultados observados:

    docker compose ps
    api: Up (healthy)
    qdrant: Up

    GET /health
    {"status":"ok","service":"RagTest API","version":"0.5.22","environment":"development"}

    GET /ready
    {"status":"ready","dependencies":{"qdrant":"ok"}}

Logs da API confirmaram:

    Application startup complete
    Uvicorn running on http://0.0.0.0:8000
    GET /health -> 200
    GET /ready -> 200

Status atualizado da 0.5.22:

    implementação remota ............ verificada em CI
    backend runtime 0.5.22 .......... verificado
    Qdrant/ready .................... verificado
    Expo -> FastAPI -> RAG .......... aguardando validação final

Estado aproximado da 0.5.22: 95%.

Próximo passo exato:

1. validar preflight CORS local para Origin http://localhost:8081;
2. iniciar frontend Expo 0.5.22;
3. confirmar npm test = 6 testes e typecheck verde;
4. enviar uma pergunta pela tela;
5. confirmar POST /v1/chat nos logs da API;
6. confirmar resposta RAG real renderizada;
7. registrar runtime final e fechar a 0.5.22 para merge.


### 0.5.22 — fluxo ponta a ponta verificado em runtime

Data: 2026-09-21.

Validação executada com a branch correta `feature/frontend-fastapi-0.5.22`.

Evidências locais:

    frontend/package.json
    version: 0.5.22

    CORS preflight:
    OPTIONS /v1/chat -> HTTP 200
    access-control-allow-origin: http://localhost:8081

    npm test:
    Test Suites: 2 passed, 2 total
    Tests: 6 passed, 6 total

    npm run typecheck:
    concluído sem erros

    Expo Web:
    http://localhost:8081
    bundle concluído

Fluxo funcional observado visualmente:

    pergunta digitada na interface
        ->
    botão Enviar
        ->
    FastAPI /v1/chat
        ->
    retrieval/Qdrant/LLM/grounding
        ->
    resposta real renderizada no cliente Expo

Pergunta usada:

    Quais vacinas são recomendadas para pessoas idosas?

A interface mostrou a pergunta da usuária e uma resposta real do assistente com citações numéricas no texto.

Limitações visuais observadas e deliberadamente deixadas para a próxima versão:

- Markdown ainda aparece como texto cru, por exemplo `**negrito**`;
- fontes/citações ainda não possuem cartões visuais;
- metadados de grounding/modelo ainda não são mostrados na interface;
- refinamentos de UX pertencem à 0.5.23/0.5.24.

Status final da 0.5.22:

    CORS Expo Web ...................... verificado
    backend 0.5.22 .................... verificado
    Qdrant/ready ...................... verificado
    cliente REST ...................... verificado
    tela -> FastAPI -> RAG ............ verificado
    resposta renderizada .............. verificada
    testes frontend ................... 6/6
    typecheck ......................... verificado
    backend tests ..................... 115 passed
    Ruff .............................. verificado
    corpus/embeddings/Qdrant .......... inalterados

Roadmap após validação:

    0.5.21  Expo + contrato REST ............ concluída/merged
    0.5.22  tela -> FastAPI real ............ concluída/aguardando merge
    0.5.23  rich-text + fontes + citações ... próxima
    0.5.24  UX + grounding/refinamentos ..... futura
    0.6.x   sessões .......................... futura
    0.7.x   auditoria/LGPD/segurança ........ futura
    0.8.x   agendamento/lembretes ........... futura
    0.9.x   avaliação/usabilidade ........... futura
    1.0     artefato final do TCC ........... futura

Próximo passo exato:

1. manter PR #17 aberto até autorização explícita de merge;
2. após merge, abrir a 0.5.23 em branch limpa;
3. implementar renderização rich-text/Markdown;
4. transformar `sources` em cartões de fontes com documento/página;
5. expor citações de forma navegável/legível na interface;
6. manter grounding e metadados técnicos disponíveis sem poluir a experiência principal.


### Início e checkpoint da 0.5.23 — rich-text e fontes citadas

Base da versão:

    main validada/mesclada: 0.5.22
    merge 0.5.22: f012ebbfe4ebf6f27c26cf7d7e85e79ab1809606
    branch: feature/richtext-sources-0.5.23
    PR: #18 draft

Objetivo da 0.5.23:

Melhorar a apresentação da resposta sem alterar backend, retrieval ou contrato REST: Markdown deve ser renderizado corretamente e a interface principal deve mostrar somente as fontes efetivamente citadas pela resposta.

Implementado:

- renderer Markdown JS-only `@ronradtke/react-native-markdown-display` 9.0.3;
- resposta do assistente renderizada como rich-text;
- cartões de fontes com `[citation_id]`, nome do documento, página e excerpt;
- normalização visual do nome do arquivo a partir do path da fonte;
- filtro por `citation_ids`: fontes recuperadas mas não citadas não aparecem na seção principal;
- Jest configurado para transpilar explicitamente o renderer Markdown;
- versões backend/frontend alinhadas em 0.5.23;
- D028 registrada;
- Dificuldade #30 registrada;
- backend/corpus/embeddings/Qdrant inalterados.

TDD/CI observado:

1. RED rich-text/fontes:
       resposta ainda mostrava `**Vacina contra Influenza**` cru;
       seção Fontes consultadas inexistente;
       1 failed, 6 passed.

2. primeira implementação:
       renderer Markdown + cartões de fontes.

3. falha de infraestrutura de teste:
       Jest encontrou `SyntaxError: Unexpected token '<'` dentro do renderer;
       corrigido com `transformIgnorePatterns` conforme mecanismo do jest-expo.

4. GREEN rich-text/fontes:
       frontend 7/7;
       typecheck verde;
       backend 115 passed;
       Ruff verde.

5. RED semântico de fontes:
       fonte recuperada mas não citada apareceu na interface;
       1 failed, 7 passed.

6. GREEN semântico:
       cartões filtrados por `citation_ids`;
       frontend 8/8;
       typecheck verde;
       backend/Ruff verdes.

Estado aproximado da 0.5.23: 95%.

Aguardando validação:

- CI final do head consolidado: verificada (frontend 8/8, typecheck, backend 115 passed, Ruff verde);
- runtime visual local no Expo Web usando resposta RAG real;
- confirmação de que Markdown não aparece cru;
- confirmação de que os cartões de fontes citadas mostram documento/página/trecho.

Próximo passo exato:

1. confirmar CI final;
2. usuário atualizar para `feature/richtext-sources-0.5.23`;
3. executar `npm install`, testes e typecheck;
4. iniciar Expo Web com backend já ativo;
5. fazer uma pergunta oficial;
6. confirmar visualmente rich-text + fontes citadas;
7. registrar runtime final e fechar a 0.5.23 para merge.

Roadmap após este checkpoint:

    0.5.21  Expo + contrato REST ............ concluída/merged
    0.5.22  tela -> FastAPI real ............ concluída/merged
    0.5.23  rich-text + fontes + citações ... atual (~90%)
    0.5.24  UX + grounding/refinamentos ..... próxima
    0.6.x   sessões .......................... futura
    0.7.x   auditoria/LGPD/segurança ........ futura
    0.8.x   agendamento/lembretes ........... futura
    0.9.x   avaliação/usabilidade ........... futura
    1.0     artefato final do TCC ........... futura


### 0.5.23 — CI final do código consolidado

Head validado:

    bb5dc40784a2a69c11d436acee38e2cc43c51a64

Resultados:

    frontend: 2 suites / 8 testes aprovados
    TypeScript typecheck: success
    backend: 115 passed, 6 warnings
    Ruff: All checks passed!

O `frontend/tsconfig.json` também foi alinhado ao formato que o Expo SDK 57 estava gerando automaticamente, preservando os tipos `jest` e `node` e evitando que apenas iniciar `expo start` deixe o repositório local modificado.

Status:

    implementação 0.5.23 .............. verificada em CI
    runtime visual rich-text/fontes ... aguardando validação local
    PR #18 ............................ draft / mergeable


### Validação runtime final da 0.5.23 — 2026-09-21

Status: verificado localmente.

Evidências observadas no ambiente Windows do projeto:

- `GET /health` respondeu `200` com versão `0.5.23`;
- `GET /ready` respondeu `200` com Qdrant `ok`;
- retrieval sem filtros para `Quais vacinas são recomendadas para pessoas idosas?` retornou somente `pessoa_idosa/caderneta_saude_pessoa_idosa_5ed_1re.pdf`, página 34, sem fonte `chatscm/`;
- Expo Web enviou `POST /v1/chat` e recebeu `200 OK`;
- Markdown foi renderizado visualmente: negrito e lista não apareceram como marcadores crus;
- a seção `Fontes consultadas` foi exibida;
- o cartão de fonte mostrou `[1]`, nome do documento, página 34 e excerpt;
- as citações `[1]` da resposta ficaram coerentes com o `citation_id` exibido;
- `git status --short` permaneceu limpo após a execução local.

Observação:

O warning do FastEmbed sobre mudança de pooling em versões posteriores permanece apenas como aviso de runtime e não interrompeu retrieval nem a chamada do chat. A baseline do projeto continua preservando FastEmbed 0.8.0 conforme documentação existente.

Fechamento da versão:

    implementação 0.5.23 .............. verificada
    CI ................................ verificada
    runtime FastAPI/Qdrant ............ verificado
    runtime Expo Web .................. verificado
    rich-text/fontes/citações ......... verificados
    corpus/embeddings/Qdrant .......... inalterados
    PR #18 ............................ draft
    merge em main ..................... não realizado

Pendência antes do merge do PR #18 para `main`:

A reconciliação da branch com `main` foi realizada por merge de sincronização autorizado e a CI do head reconciliado foi verificada com sucesso. Resta apenas a autorização explícita do usuário para o merge do PR #18.

Roadmap:

    0.5.23  rich-text + fontes + citações ... implementação/runtime concluídos
    0.5.24  UX + grounding/refinamentos ..... próxima


### CI pós-reconciliação da 0.5.23

Head reconciliado verificado:

    fc391ca5b88753953b5ca4e6bc7042cb4f8d2f7d

GitHub Actions:

    workflow: CI
    run: #290
    lint: success
    backend test: success
    frontend tests: success
    frontend typecheck: success

Estado do PR #18 após a reconciliação:

    base: main
    behind_by: 0
    mergeable: true
    draft: true
    merge em main: não realizado

Status da 0.5.23:

    implementação ...................... verificada
    runtime local ...................... verificado
    CI pós-reconciliação ............... verificada
    compatibilidade com main ........... verificada
    decisão de merge ................... aguardando autorização explícita


### Checkpoint 0.5.24 — UX de grounding

Objetivo do primeiro recorte:

Corrigir a diferença entre **fonte citada** e **fonte apenas recuperada** quando o backend retorna `grounded=false`, além de tornar o estado do grounding compreensível na interface sem prometer correção clínica ou entailment semântico.

Comportamentos implementados:

- `grounded=true`:
  - exibe `Citações verificadas`;
  - explica que as afirmações informativas estão acompanhadas de referências do corpus;
  - mantém `Fontes consultadas` apenas com IDs presentes em `citation_ids`.

- `grounded=false` com `sources`:
  - exibe `Citações não verificadas`;
  - orienta a consultar as fontes recuperadas;
  - mostra `Fontes recuperadas para consulta`;
  - não exibe `[citation_id]` nesses cartões, evitando representá-los como citações efetivamente usadas.

- `grounded=false` sem `sources`:
  - exibe `Sem base documental suficiente`;
  - não cria uma seção de fontes vazia.

Motivação concreta observada na 0.5.23:

O fallback de grounding do backend diz `Consulte as fontes retornadas antes de usar a informação`, mas a UI 0.5.23 filtrava todas as fontes por `citation_ids`. Como o fallback usa `citation_ids=[]`, as fontes recuperadas ficavam invisíveis. A 0.5.24 separa semanticamente essas fontes sem tratá-las como citações.

TDD observado:

    RED — commit d4f9a7e2feca6f57ec16afc9b9765249cbf7bf5b
    CI run #293
    backend test: success
    lint: success
    frontend tests: failure esperado
    frontend typecheck: skipped após falha dos testes

    GREEN — head 182219d8a272b92785c83f4fa99b1ee4c978ae95
    CI run #297
    backend test: success
    lint: success
    frontend tests: success
    frontend typecheck: success

Arquitetura:

- contrato `POST /v1/chat`: inalterado;
- backend de grounding: inalterado;
- corpus/embeddings/Qdrant: inalterados;
- mudança concentrada na interpretação/apresentação do contrato no cliente Expo;
- versões backend/frontend alinhadas em 0.5.24.

Status:

    implementação primeiro recorte .......... verificada em CI
    runtime visual Expo Web grounded=true ... verificado
    PR #19 .................................. draft


### Validação visual local da 0.5.24 — 2026-09-21

Status: verificado para o cenário `grounded=true`.

Evidências observadas:

- checkout em `feature/ux-grounding-0.5.24`, head `756d149aa5d971c72236569a73041432633cbe4c`;
- frontend local: 2 suites / 11 testes aprovados;
- `npm run typecheck`: concluído sem erros;
- `GET /health`: versão `0.5.24`;
- `GET /ready`: Qdrant `ok`;
- retrieval local para `Quais vacinas são recomendadas para pessoas idosas?` retornou apenas `pessoa_idosa/caderneta_saude_pessoa_idosa_5ed_1re.pdf`, página 34, sem `chatscm/`;
- `POST /v1/chat` executado pela interface Expo Web retornou uma resposta `grounded=true`;
- a interface exibiu `Citações verificadas` e o texto sobre referências do corpus;
- a seção `Fontes consultadas` exibiu `[1]`, o documento da Caderneta da Pessoa Idosa e a página 34;
- Markdown/lista foram renderizados sem marcadores crus;
- os cenários `grounded=false` não foram provocados artificialmente e permanecem cobertos pelos testes determinísticos.

Ambiente e dados:

- API foi reconstruída para a 0.5.24 sem recriar volumes;
- a collection `ragtest_documents`, o corpus, embeddings e os 767 pontos não foram alterados;
- nenhum conteúdo `chatscm/` foi enviado ao provider externo.

Próximo passo: definir e aprovar um refinamento pequeno e isolado para continuar a 0.5.24, mantendo TDD e o PR #19 em draft.


### Segundo recorte da 0.5.24 — indisponibilidade temporária na interface

Problema concreto:

O cliente REST já preservava o status HTTP em `ChatApiError`, mas `App.tsx` tratava HTTP 503, falhas de rede e demais erros com a mesma mensagem genérica. Assim, uma indisponibilidade temporária do provider não era distinguida de um problema de conexão local.

Comportamento implementado:

- `ChatApiError` com `status=503` mostra `O serviço de geração está temporariamente indisponível. Tente novamente em alguns instantes.`;
- detalhes técnicos retornados pelo provider não são exibidos à usuária;
- falhas de rede e erros não classificados continuam usando a mensagem genérica anterior;
- backend, contrato REST, corpus, retrieval, embeddings e Qdrant permanecem inalterados.

TDD local observado:

    RED: teste direcionado com 1 falha esperada e 8 testes aprovados
    causa observada: App.tsx ainda exibia a mensagem genérica para ChatApiError(503)

    GREEN: teste direcionado 9/9
    suíte frontend completa 12/12
    TypeScript typecheck: success

Status:

    tratamento específico de HTTP 503 .... implementado e verificado localmente
    documentação .......................... atualizada
    CI do commit d207b89 .................. success (run 35641533624)
    lint .................................. success (38 s)
    backend test .......................... success (39 s)
    frontend-test + typecheck ............. success (1 min 35 s)
    PR #19 ................................ draft

Avisos não bloqueantes observados na CI:

- o GitHub passou a forçar actions baseadas em Node.js 20 a executar em Node.js 24;
- o rótulo `ubuntu-latest` tem migração para Ubuntu 26 anunciada para 2026-10-19;
- esses avisos não causaram falha e não alteram o escopo funcional deste recorte, mas ficam registrados para manutenção futura do workflow.


### Terceiro recorte da 0.5.24 — retry manual da última pergunta

Problema concreto:

Depois de uma falha, inclusive HTTP 503, a interface orientava a tentar novamente, mas limpava o campo de entrada e não oferecia uma ação para repetir a pergunta anterior. A usuária precisava digitar novamente o mesmo conteúdo.

Comportamento implementado:

- o cartão de erro apresenta o botão acessível `Tentar novamente`;
- o acionamento reenvia explicitamente a última pergunta usando o mesmo contrato `POST /v1/chat`;
- erro e resposta anterior são limpos antes da nova tentativa, e o loading normal é reutilizado;
- não existe retry automático nem chamada silenciosa ao provider;
- backend, contrato REST, providers, corpus, retrieval, embeddings e Qdrant permanecem inalterados.

TDD local observado:

    RED: teste direcionado com 1 falha esperada e 9 testes aprovados
    causa observada: botão acessível Tentar novamente ainda não existia

    GREEN: teste direcionado 10/10
    suíte frontend completa 13/13
    TypeScript typecheck: success

Status:

    retry manual da última pergunta ........ implementado e verificado em CI
    documentação ........................... atualizada
    CI do commit 69d7868 ................... success (run 35643606329)
    lint ................................... success (36 s)
    backend test ........................... success (46 s)
    frontend-test + typecheck .............. success (1 min 20 s)
    validação visual Expo Web .............. verificada sem provider externo
    CI do ajuste visual b8aed87 ............ success (run 35645801364)
    lint final ............................. success (42 s)
    backend test final ..................... success (40 s)
    frontend-test final .................... success (1 min 37 s)
    PR #19 ................................. draft

Validação visual segura:

- Expo Web apontou para `http://127.0.0.1:65534`, porta local sem serviço, sem acessar provider, corpus ou Qdrant;
- a primeira captura revelou que o cartão crescia além da viewport rolável e deixava parte do botão sob o limite do composer;
- o histórico passou a executar `scrollToEnd` quando loading, resposta ou erro mudam;
- após reiniciar o Metro com bundle novo, o botão ficou totalmente visível: `y=247–286` dentro da viewport rolável que termina em `y=330`;
- o navegador registrou exatamente duas chamadas `POST /v1/chat`: envio inicial e retry explícito;
- a Dificuldade #31 registra o recorte visual e o cuidado com bundle congelado no Expo em modo CI.


### Merge da 0.5.24 — 2026-09-21

- PR #19 `Refina UX de grounding e fontes na 0.5.24`: merged;
- head final da feature: `534e1c5334424a57e7cd0adb56f6ea763c20b4ec`;
- merge commit em `main`: `28edf6a51bf29a4aa62ff56a74efbffb640e728f`;
- CI pré-merge: run `35677374957`, todos os jobs em success;
- CI pós-merge da `main`: run `35677503800`, todos os jobs em success;
- corpus, embeddings, Qdrant e os 767 pontos permaneceram inalterados;
- nenhum conteúdo `chatscm/` foi enviado a provider externo durante as validações deste recorte.

O marco seguinte era desenhar o primeiro recorte da 0.6.x; ele foi concluído posteriormente e está consolidado no handoff autoritativo do início deste documento.

### Implementação das sessões 0.6.0 — 2026-09-22

- branch: `feature/sessions-0.6.0`;
- commits funcionais: `dc9796d`, `aa58e4d`, `ec531a1`, `0d4a33a`, `453d3ad`, `6d72909`;
- contratos, SQLite, contexto seguro, serviço conversacional, API REST e integração opcional do chat concluídos;
- suíte local: 149 testes aprovados; Ruff aprovado;
- SQLite de sessões separado do Qdrant; corpus, embeddings e Expo não foram alterados;
- versão do backend atualizada para `0.6.0`;
- validação manual concluída em Docker: `health=ok`, `ready=ready`, API reiniciada sem perder
  a sessão criada e uma pergunta real ao Groq retornou `grounded=true` com 5 fontes;
- a sessão de teste foi removida após a validação; nenhum dado pessoal real foi usado;
- permanece pendente somente a decisão de integração/merge, que exige autorização explícita.


### Design da 0.6.0 — 2026-09-21

- prioridade oficial confirmada: módulo RAG completo, lapidado, desacoplado e implementável em outros sistemas;
- frontend Expo mantido apenas como cliente demonstrativo, sem nova prioridade de estilização;
- arquitetura de sessões persistentes aprovada com `SessionStore` abstrato e SQLite padrão;
- modo stateless do `POST /v1/chat` preservado;
- histórico definido como contexto não confiável, nunca como evidência documental;
- especificação consolidada em `docs/superpowers/specs/2026-09-21-sessoes-conversacionais-0.6.0-design.md`;
- branch criada: `feature/sessions-0.6.0`;
- design escrito aprovado pelo usuário em 2026-09-22;
- próximo passo: revisar o plano TDD antes de iniciar qualquer código funcional.

## Atualização de continuidade — sidequest Demo M4 (2026-09-23)

Esta seção registra o estado da implementação do Laboratório experimental de retrieval. Ela
complementa M1–M3.6 e não reclassifica intenções, benchmarks históricos ou testes automatizados
como validação de produção.

### Estado implementado

- O frontend da branch `sidequest/ragtest-demo` agora possui Laboratório com Dense,
  Dense + rerank, Hybrid, seleção de Top K real (`limit` 3/5/10), pergunta livre, exemplos,
  execução single e comparação de todos os perfis.
- A interface usa somente `POST /v1/demo/retrieval`: uma execução single gera uma requisição;
  comparação gera três requisições sequenciais. Não há chamada a `/v1/demo/run`, LLM, cache
  persistente ou mutação de configuração global.
- Respostas são validadas por consulta, modo, limite, máximo de 10 fontes e ordem contígua;
  campos nulos são exibidos como `Não disponível`. Erros parciais preservam os cartões que
  tiveram sucesso e oferecem retry explícito para o perfil com falha.
- Multi-query/decomposição é explicitamente marcado como indisponível no contrato do laboratório.
  Métricas de comparação são descritivas (contagens, documentos únicos, sobreposições,
  exclusividades e mudanças de posição); scores não são tratados como diretamente comparáveis
  nem usados para declarar vencedor.

### Evidências verificadas

- Suíte frontend: **99 testes Jest em 11 suites aprovados**; `npm run typecheck`, Ruff e
  `git diff --check` aprovados após a implementação.
- Runtime local/controlado: FastAPI em `127.0.0.1:8001`, CORS local e allowlist pública,
  Qdrant local preservando **767 pontos**. A pergunta pública de vacinação de pessoas idosas
  retornou respostas para Dense, Dense + rerank e Hybrid, sem envio de conteúdo `CHATSCM` ou
  dados pessoais a provider externo. Os tempos observados foram aproximadamente 11,9 s, 47 ms
  e 1,9 s respectivamente nessa execução; são evidência de funcionamento local, não de
  superioridade de desempenho.
- Expo Web carregou o Laboratório e exibiu a superfície de execução, descrições de perfis,
  benchmark histórico DEV/HOLDOUT, definições de métricas e aviso de privacidade. A cobertura
  automatizada inclui single/compare, retry e tratamento parcial. Na validação visual com
  override real do viewport, `1366x768` e `1024x600` mantiveram `flexDirection=row`, enquanto
  `390x844` e `360x800` usaram `flexDirection=column`; em todos os quatro casos
  `scrollWidth == viewport`, sem overflow horizontal. As capturas confirmaram três colunas no
  desktop e cartões empilhados no mobile. Network/console continuam não observáveis diretamente
  no IAB.

### Decisões e limites

- O M4 mantém o backend M1 e as decisões D006–D008: os perfis são comparados como alternativas
  instrumentais e os benchmarks DEV/HOLDOUT (`2026-09-20-v1`) permanecem evidência histórica,
  não resultado da pergunta atual nem prova universal de qualidade.
- A tela mostra apenas perguntas públicas e não autoriza nomes, prontuários ou outros dados
  pessoais. Corpus, embeddings, collection Qdrant, providers, `.env` e configuração de agentes
  não foram alterados.
- Uso externo/produção continua **BLOCKED** por ausência de autenticação/rate limiting e pelos
  riscos documentados de logs preexistentes de providers e prompt injection. Os quatro viewports
  foram verificados visualmente e não apresentaram overflow horizontal; o tema claro continua
  sem observação manual nesta sessão. Não se deve inferir comportamento do tema claro a partir
  dos testes ou da captura em tema escuro.

**Decisão:** `M4 VALIDATED — LOCAL/CONTROLADO`. O tema claro e a inspeção direta de
Network/console permanecem limitações observacionais; elas não alteram a validação controlada
registrada acima. Uso externo/produção continua bloqueado, e M5 permanece fora do escopo desta
sidequest.
