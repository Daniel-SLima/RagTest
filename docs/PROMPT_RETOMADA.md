# Prompt de retomada — RagTest / Se Cuida Mulher

Use este texto ao iniciar um novo chat para continuar o desenvolvimento sem reconstruir o contexto manualmente.

---

Estou continuando o projeto privado GitHub `Daniel-SLima/RagTest`, referente ao TCC:

**“Desenvolvimento de Módulo Conversacional Baseado em RAG para Apoio ao Letramento em Saúde e Acesso a Serviços no Aplicativo Se Cuida Mulher”.**

Quero que você continue o desenvolvimento **exatamente de onde paramos**, sem reinventar arquitetura, mudar corpus, recriar Qdrant ou refazer decisões já validadas.

## Antes de alterar qualquer código

Use o GitHub conectado e leia, nesta ordem:

1. `docs/CONTEXTO_CONTINUIDADE.md`
2. `docs/decisoes-tecnicas.md`
3. `docs/dificuldades-tcc.md`
4. `docs/frontend-demo.md`
5. `README.md`
6. `docs/runtime-baseline-0.5.15.md`
7. `docs/docx-structure-audit-0.5.17.md`

No `CONTEXTO_CONTINUIDADE.md`, a seção:

**HANDOFF AUTORITATIVO ATUAL — 2026-09-21 DESIGN DA 0.6.0**

prevalece sobre qualquer trecho histórico conflitante abaixo dela.

## Estado atual que deve ser confirmado no GitHub

- `main` contém a versão **0.5.24** validada e mesclada.
- PR #19 foi **merged**.
- Merge commit da 0.5.24: `28edf6a51bf29a4aa62ff56a74efbffb640e728f`.
- Head final da feature antes do merge: `534e1c5334424a57e7cd0adb56f6ea763c20b4ec`.
- CI final pré-merge: run `35677374957`, com todos os jobs em success.
- CI pós-merge da `main`: run `35677503800`, com todos os jobs em success.
- Runtime local Expo Web da 0.5.24 foi validado para grounding e retry manual.
- Corpus, embeddings e Qdrant permaneceram inalterados.
- Branch atual: `feature/sessions-0.6.0`.
- A arquitetura da **0.6.0 — sessões conversacionais portáveis** foi aprovada em conversa.
- A especificação escrita está em `docs/superpowers/specs/2026-09-21-sessoes-conversacionais-0.6.0-design.md` e foi aprovada em 2026-09-22.
- O plano TDD está em `docs/superpowers/plans/2026-09-22-sessoes-conversacionais-0.6.0.md` e foi executado de forma nativa.
- As Tasks 1–7 estão implementadas; a suíte local tem 150 testes aprovados.
- Primeiro recorte de grounding validado em CI e visualmente no Expo Web.
- Segundo recorte implementado por TDD: mensagem específica para HTTP 503 sem exposição do detalhe técnico do provider.
- Terceiro recorte implementado por TDD: retry manual da última pergunta após erro, sem chamadas automáticas.
- Retry manual validado visualmente no Expo Web com falha de rede exclusivamente local; botão visível e duas chamadas explícitas observadas.
- Antes de continuar, leia a especificação, o plano e o estado real da branch; não faça merge sem autorização explícita.

## Prioridade oficial do produto

- O entregável principal é um módulo RAG completo, lapidado e integrável a qualquer sistema com baixo esforço.
- O Expo é apenas um cliente demonstrativo; estilização fica depois da conclusão do núcleo funcional.
- Sessões, contexto, auditoria, segurança e ações de integração pertencem ao backend e a contratos públicos.
- A troca de Gemini, Groq, Ollama ou outro provider não deve afetar API, sessões, retrieval ou clientes.
- Sem acesso ao agendamento real do Se Cuida Mulher, gatilhos futuros devem ser ações estruturadas neutras para o sistema integrador executar.

## 0.5.24 — estado atual

- `grounded=true`: mostra `Citações verificadas` e somente fontes citadas;
- `grounded=false` com fontes: mostra `Citações não verificadas` e fontes recuperadas sem badge de citação;
- `grounded=false` sem fontes: mostra `Sem base documental suficiente` e nenhuma seção vazia;
- HTTP 503: mostra indisponibilidade temporária em linguagem amigável;
- falha de rede/outro erro: preserva a mensagem genérica;
- detalhes técnicos de provider não são exibidos à usuária;
- erros apresentam `Tentar novamente`, que reenvia manualmente a última pergunta;
- o histórico rola para o fim após mudanças de loading, resposta ou erro, evitando que o botão fique cortado em viewports baixas;
- suíte frontend local após o terceiro recorte: 13/13 e typecheck verde;
- CI do terceiro recorte no commit `69d7868`: run `35643606329`, com lint, backend test e frontend-test/typecheck em success;
- ajuste visual final no commit `b8aed87`: run `35645801364`, com lint, backend test e frontend-test/typecheck em success;
- CI do commit funcional `d207b89`: run `35641533624`, com lint, backend test e frontend-test/typecheck em success;
- avisos não bloqueantes da CI: actions Node.js 20 forçadas para Node.js 24 e migração futura de `ubuntu-latest` para Ubuntu 26;
- corpus, embeddings e Qdrant permanecem inalterados em 767 pontos.

## 0.5.23 — estado verificado

A 0.5.23 implementa rich-text + fontes + citações no cliente Expo sem mudar o contrato público do backend.

Verificado:

- Markdown renderizado no React Native/Expo;
- negrito e listas não aparecem como marcadores crus;
- seção `Fontes consultadas`;
- cartões com `[citation_id]`, documento, página e excerpt;
- fontes recuperadas mas ausentes de `citation_ids` não aparecem na seção principal;
- frontend possuía 2 suites / 8 testes aprovados no checkpoint consolidado;
- TypeScript typecheck aprovado no checkpoint consolidado;
- backend possuía 115 testes aprovados e Ruff verde no checkpoint consolidado;
- runtime local Expo Web concluído;
- `POST /v1/chat` retornou 200;
- `GET /health` retornou versão 0.5.23;
- `GET /ready` retornou Qdrant ok;
- pergunta real usada: `Quais vacinas são recomendadas para pessoas idosas?`;
- retrieval sem filtros retornou `pessoa_idosa/caderneta_saude_pessoa_idosa_5ed_1re.pdf`, página 34, sem `chatscm/`;
- corpus, embeddings e Qdrant permaneceram inalterados.

A CI do **head final da feature** foi verificada: lint, backend test, frontend tests e frontend typecheck concluíram com sucesso. A 0.5.23 foi posteriormente mesclada em `main` pelo PR #18.

## Arquitetura que deve ser preservada

```text
Cliente Expo / futuro Se Cuida Mulher / outro cliente
    -> REST / JSON
    -> FastAPI
    -> RAG
    -> retrieval / grounding / auditoria
    -> Qdrant
    -> provider LLM configurável
```

O backend não depende do frontend.

Stack consolidada:

- Python 3.12 + FastAPI + Docker;
- Qdrant 1.19.1;
- FastEmbed 0.8.0;
- dense `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, dimensão 384;
- sparse `Qdrant/bm25` em português;
- retrieval padrão `dense-rerank`;
- providers explícitos Groq/Gemini/Ollama, sem fallback automático;
- Expo SDK 57 + React Native 0.86 + React 19.2 + TypeScript;
- REST/JSON via `POST /v1/chat`.

## Regras obrigatórias de trabalho

Use estes status:

- **implementado**
- **aguardando validação**
- **verificado**
- **hipótese**

Fluxo preferido:

```text
alteração
↓
comandos/testes
↓
usuário executa quando runtime local for necessário
↓
usuário envia logs
↓
analisar evidência
↓
próxima alteração
```

Sempre informe versão atual, etapa do roadmap, o que foi concluído, o que falta e se depende de ação do usuário. Não declare sucesso sem evidência. Não faça merge do PR para `main` sem autorização explícita. Prefira comandos Windows CMD.

## Regras críticas que não podem ser quebradas

Não usar:

- `ragtest-ingest --recreate`;
- `docker compose down -v`.

Não recriar sem autorização explícita:

- corpus;
- embeddings;
- collection Qdrant;
- 767 pontos/chunks atuais.

Corpus atual:

- 18 arquivos;
- 767 chunks/pontos;
- collection `ragtest_documents`.

Para novos PDF/DOCX: dry-run -> revisar -> `ragtest-sync-ingestion --apply` -> revalidar.

## Privacidade

Os arquivos `chatscm/*.docx` continuam sem revisão manual completa de privacidade para providers externos. Não enviar CHATSCM a Groq, Gemini ou outro provider externo antes dessa revisão. Para testes externos, usar fontes oficiais. Nunca pedir, reproduzir ou registrar API keys.

## Grounding

`grounded=true` representa validação estrutural de cobertura de citações sob o gate implementado; não é prova automática de entailment semântico.

Preservar:

- normalização de citações;
- cobertura por bloco informativo;
- postprocess conservador;
- uma tentativa de repair;
- fallback seguro.

## Providers

Seleção explícita, sem fallback automático.

Baseline externa de desenvolvimento:

- Groq;
- `openai/gpt-oss-120b`;
- reasoning effort low;
- `LLM_MAX_OUTPUT_TOKENS=1024`.

## Cuidado com Expo no Windows

Antes de trocar branch após executar Expo:

- `git status --short`;
- Expo pode modificar `frontend/tsconfig.json`;
- `npm install` pode gerar `frontend/package-lock.json` local;
- nunca descartar mudanças desconhecidas automaticamente;
- inspecionar o diff antes de restaurar arquivos.

## Roadmap

```text
0.5.20  observabilidade Groq ................ merged
0.5.21  Expo + contrato REST ............... merged
0.5.22  Expo -> FastAPI -> RAG ............. merged
0.5.23  rich-text + fontes + citações ...... merged
0.5.24  UX + grounding/refinamentos ........ merged
0.6.0   sessões portáveis .................. plano concluído
0.7.x   auditoria/LGPD/segurança ........... futura
0.8.x   agendamento/lembretes .............. futura
0.9.x   avaliação/usabilidade .............. futura
1.0     artefato final do TCC .............. futura
depois  integração no Se Cuida Mulher ...... posterior
```

Não me peça para repetir informações que estejam nesses arquivos. Leia-os e continue do estado real do repositório.

Estado atual da 0.6.0: a implementação backend está na branch `feature/sessions-0.6.0`. As
sessões REST e o `session_id` opcional do chat estão implementados, com 150 testes aprovados.
O Docker foi validado com `health=ok` e `ready=ready`; a sessão sobreviveu ao reinício da API;
uma pergunta real ao Groq retornou `grounded=true` com cinco fontes. A sessão de teste foi
removida. Não fazer merge sem autorização explícita.

Ao final de cada avanço relevante, atualize `docs/CONTEXTO_CONTINUIDADE.md`; registre decisões em `docs/decisoes-tecnicas.md` e falhas reais em `docs/dificuldades-tcc.md`.
