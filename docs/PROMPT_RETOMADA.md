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

**HANDOFF AUTORITATIVO ATUAL — 2026-09-21 COM 0.5.24 EM DESENVOLVIMENTO**

prevalece sobre qualquer trecho histórico conflitante abaixo dela.

## Estado atual que deve ser confirmado no GitHub

- `main` contém a versão **0.5.23** validada e mesclada.
- PR #18 foi **merged**.
- Merge commit da 0.5.23: `402f27b48a8d7c97252782cd653a61a405638870`.
- Head validado da feature antes do merge: `74dd4ca58ef76401e5d9c6b1b05bd8729c17053b`.
- CI final da feature: run #291, com lint, backend test, frontend tests e frontend typecheck em success.
- Runtime local Expo Web da 0.5.23 foi validado.
- Corpus, embeddings e Qdrant permaneceram inalterados.
- Versão em desenvolvimento: **0.5.24 — UX + grounding/refinamentos**.
- Branch: `feature/ux-grounding-0.5.24`.
- PR #19: aberto, draft e sem autorização de merge.
- Primeiro recorte de grounding validado em CI e visualmente no Expo Web.
- Segundo recorte implementado por TDD: mensagem específica para HTTP 503 sem exposição do detalhe técnico do provider.
- Antes de continuar, confirme o head atual da feature, o estado da CI e o checkout local.

## 0.5.24 — estado atual

- `grounded=true`: mostra `Citações verificadas` e somente fontes citadas;
- `grounded=false` com fontes: mostra `Citações não verificadas` e fontes recuperadas sem badge de citação;
- `grounded=false` sem fontes: mostra `Sem base documental suficiente` e nenhuma seção vazia;
- HTTP 503: mostra indisponibilidade temporária em linguagem amigável;
- falha de rede/outro erro: preserva a mensagem genérica;
- detalhes técnicos de provider não são exibidos à usuária;
- suíte frontend local após o segundo recorte: 12/12 e typecheck verde;
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
0.5.24  UX + grounding/refinamentos ........ EM DESENVOLVIMENTO
0.6.x   sessões ............................. futura
0.7.x   auditoria/LGPD/segurança ........... futura
0.8.x   agendamento/lembretes .............. futura
0.9.x   avaliação/usabilidade .............. futura
1.0     artefato final do TCC .............. futura
depois  integração no Se Cuida Mulher ...... posterior
```

Não me peça para repetir informações que estejam nesses arquivos. Leia-os e continue do estado real do repositório.

Ao final de cada avanço relevante, atualize `docs/CONTEXTO_CONTINUIDADE.md`; registre decisões em `docs/decisoes-tecnicas.md` e falhas reais em `docs/dificuldades-tcc.md`.
