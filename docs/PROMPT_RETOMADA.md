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

**HANDOFF AUTORITATIVO ATUAL — 2026-09-21 APÓS MERGE DA 0.5.22**

prevalece sobre qualquer trecho histórico conflitante abaixo dela.

Depois, antes de editar a 0.5.23, inspecione também:

- `frontend/App.tsx`
- `frontend/src/lib/chat-api.ts`
- `frontend/src/__tests__/app.test.tsx`
- `frontend/src/lib/chat-api.test.ts`
- `frontend/package.json`
- `frontend/app.json`
- `app/schemas/chat.py`
- `app/api/routes/chat.py`
- `app/main.py`
- `app/core/config.py`
- `.env.example`
- `frontend/.env.example`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `pyproject.toml`

## Estado atual que deve ser confirmado no GitHub

- `main` contém a versão **0.5.22** validada e mesclada.
- PR #17 foi merged.
- Merge da 0.5.22: `f012ebbfe4ebf6f27c26cf7d7e85e79ab1809606`.
- Depois do merge houve um commit documental de handoff na `main`: `718f946c228dfc34702cde44aa1035bd67ba19a5`.
- Portanto a `main` atual deve estar em ou depois de `718f946c...`.
- Neste checkpoint ainda não existe branch 0.5.23 criada.
- Próxima branch sugerida: `feature/richtext-sources-0.5.23`.

## O que já funciona e está verificado

Backend:
- Python 3.12 + FastAPI;
- Qdrant 1.19.1;
- FastEmbed 0.8.0;
- dense embedding multilingual MiniLM 384;
- BM25 sparse em português;
- retrieval padrão `dense-rerank`;
- OCR seletivo;
- ingestão incremental/sincronização segura;
- retrieval, multi-query, grounded citations, repair, postprocess conservador;
- providers explícitos Groq/Gemini/Ollama;
- observabilidade de rate limits Groq;
- API `/health`, `/ready`, `/v1/search`, `/v1/chat`.

Frontend:
- Expo SDK 57;
- React Native 0.86;
- React 19.2;
- TypeScript;
- Jest + React Native Testing Library;
- cliente REST desacoplado;
- CORS configurável;
- URL do backend por `EXPO_PUBLIC_RAG_API_BASE_URL`;
- pergunta, loading, resposta e erro renderizados.

A 0.5.22 foi validada ponta a ponta:

```text
Expo Web
  -> CORS
  -> POST /v1/chat
  -> FastAPI
  -> retrieval/Qdrant
  -> LLM
  -> grounding
  -> resposta JSON
  -> resposta na tela
```

Pergunta real usada:
`Quais vacinas são recomendadas para pessoas idosas?`

Validação final:
- frontend: 6 testes aprovados;
- TypeScript typecheck aprovado;
- backend: 115 testes aprovados;
- Ruff verde;
- `/health` versão 0.5.22;
- `/ready` Qdrant ok;
- CORS de `http://localhost:8081` validado;
- resposta real exibida visualmente no Expo Web.

## Limitação visual atual

A resposta ainda aparece como texto simples.

Exemplo observado:
`**Vacina contra Influenza**`

aparece com os asteriscos crus.

Também:
- `sources` ainda não aparecem em cartões;
- citações `[1]`, `[2]` ainda não têm UX própria;
- grounding/modelo não aparecem na UI;
- refinamentos de UX ficam para 0.5.24.

## Próximo objetivo: 0.5.23

A 0.5.23 deve focar em:

1. rich-text / Markdown seguro;
2. fontes;
3. citações;
4. apresentação clara de documento/página;
5. manter o backend desacoplado;
6. não mexer no corpus ou Qdrant se o contrato atual já for suficiente.

Comece criando `feature/richtext-sources-0.5.23` a partir da `main` atual e abra um PR draft após o primeiro commit.

Use TDD:
`RED -> GREEN -> refactor`.

O primeiro RED deve provar uma necessidade visual concreta, por exemplo:
- Markdown em negrito deve ser renderizado sem mostrar `**`;
- uma resposta com `sources` deve renderizar uma seção “Fontes” com citação, documento e página.

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
eu executo quando runtime local for necessário
↓
envio os logs
↓
você analisa
↓
próxima alteração
```

Sempre informe:
- versão atual;
- onde estamos no roadmap;
- o que acabou de ser concluído;
- o que falta;
- se depende de ação minha.

Não declare sucesso sem evidência.

Não faça merge sem minha autorização explícita.

Prefira comandos Windows CMD.

## Regras críticas que não podem ser quebradas

Não usar:
- `ragtest-ingest --recreate`;
- `docker compose down -v`.

Não recriar:
- corpus;
- embeddings;
- collection Qdrant;
- 767 pontos/chunks atuais;

sem autorização explícita.

Corpus atual:
- 18 arquivos;
- 767 chunks/pontos;
- collection `ragtest_documents`.

Se novos PDF/DOCX forem adicionados:
- primeiro dry-run com `ragtest-plan-ingestion-sync` ou `ragtest-sync-ingestion` sem `--apply`;
- revisar;
- somente então `ragtest-sync-ingestion --apply`.

## Privacidade

Não envie conteúdo `chatscm/*.docx` para Groq, Gemini ou outro provider externo antes da revisão manual de privacidade.

Para testes externos, use fontes oficiais.

Nunca peça nem reproduza API keys.

## Grounding

`grounded=true` é validação estrutural de citações, não prova automática de entailment semântico.

Preserve:
- normalização de citações;
- cobertura por bloco;
- postprocess conservador;
- um repair;
- fallback seguro.

## Providers

Seleção explícita; sem fallback automático.

Baseline atual de desenvolvimento:
- Groq;
- `openai/gpt-oss-120b`;
- reasoning effort low;
- `LLM_MAX_OUTPUT_TOKENS=1024`.

## Cuidado com Expo no Windows

Depois de executar Expo, antes de trocar branch:
- verificar `git status --short`;
- Expo pode alterar `frontend/tsconfig.json`;
- `npm install` pode gerar `frontend/package-lock.json` local não versionado;
- não descartar mudanças desconhecidas automaticamente;
- inspecionar o diff antes de restaurar arquivos.

## Roadmap atual

```text
0.5.20  observabilidade Groq ................ ✅ merged
0.5.21  Expo + contrato REST ............... ✅ merged
0.5.22  Expo -> FastAPI -> RAG ............. ✅ merged
0.5.23  rich-text + fontes + citações ...... ⏭️ AGORA
0.5.24  UX + grounding + refinamentos ...... futuro
0.6.x   sessões ............................. futuro
0.7.x   auditoria/LGPD/segurança ........... futuro
0.8.x   agendamento/lembretes ............... futuro
0.9.x   avaliação/usabilidade ............... futuro
1.0     artefato final do TCC ............... futuro
depois   integração no Se Cuida Mulher ...... posterior
```

Não me peça para repetir informações que estejam nesses arquivos. Leia-os e continue do estado real do repositório.

Ao final de cada avanço relevante, atualize `docs/CONTEXTO_CONTINUIDADE.md`; registre decisões em `docs/decisoes-tecnicas.md` e falhas reais em `docs/dificuldades-tcc.md`.
