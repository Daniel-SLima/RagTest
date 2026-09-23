# Demo segura M1 e fundação visual M2

Status M1: implementado e verificado separadamente no backend; a validação de runtime real
com provider externo e Qdrant continua fora desta sidequest.

Quando `DEMO_ENABLED=false` (padrão), as rotas `/v1/demo/run`, `/v1/demo/retrieval` e
`/v1/demo/runtime` não são registradas nem aparecem no OpenAPI. A aplicação principal e o
contrato de `/v1/chat`, `/v1/search`, `/v1/sessions`, `/health` e `/ready` permanecem separados.

Para habilitar a demonstração, a configuração deve declarar uma allowlist positiva em
`DEMO_ALLOWED_SOURCE_PREFIXES`, separada por vírgulas. A política falha fechada quando a lista
está vazia e rejeita sempre fontes `chatscm`, privadas ou sem prefixo aprovado. O endpoint de
execução usa o pipeline `answer_with_rag` existente; o endpoint de retrieval usa
`semantic_search` sem provider de geração. Nenhum modo demo altera `Settings.retrieval_mode`.

Os corpos de `/v1/demo/run` e `/v1/demo/retrieval` usam o campo textual `query`; o campo
`retrieval_mode` opcional aceita somente `dense`, `dense-rerank` ou `hybrid` e não altera a
configuração global.

As respostas demo expõem somente DTOs fechados, IDs determinísticos, documentos públicos,
excerpts sanitizados, scores disponíveis e os tempos monotônicos `retrieval_ms`,
`generation_ms` e `total_ms`; em retrieval-only, `generation_ms` é `null` porque não houve
geração. Metadata arbitrária, paths pessoais, prompts, tokens, segredos,
`.env` e detalhes crus de exceções ficam fora do contrato. A configuração e os testes não usam
providers externos nem Qdrant real.

O runtime demo informa apenas versão, rótulos sanitizados de provider/modelo/embedding/retrieval,
collection, habilitação e estado da política. UI, replay, corpus, embeddings, Qdrant e ingestão
estão fora do escopo M1.

## M2 — fundação visual opt-in no Expo

Status: implementado no commit `f675243` e verificado após QA pelos gates registrados no
handoff desta sidequest. Esta etapa adiciona somente a fundação visual da Demo Técnica no
frontend Expo: quatro abas (`Chat`, `Como funciona`, `Laboratório` e `O que ainda falta`),
estados vazios/neutros, catálogo de roadmap com referências verificáveis e contratos TypeScript
preparados para uso futuro. A narrativa `Como funciona` expõe 11 etapas, a aba Chat mantém
uma ação futura desabilitada e a identidade visual informa que esta não é a versão final do
produto Se Cuida Mulher. O Laboratório apresenta oito controles futuros desabilitados e é
explicitamente uma superfície reservada ao M4, não ao M3.

As etapas públicas do pipeline mostram o estado **aguardando execução**; internamente, o
enum estável `awaiting-execution` identifica esse estado sem simular uma execução ou fabricar
resposta, ranking, fonte ou timing.

O catálogo público usa apenas os statuses `Implementado`, `Parcial / em desenvolvimento`,
`Planejado` e `Em estudo`, sem converter intenção em evidência.

O frontend é habilitado de forma independente pelo flag
`EXPO_PUBLIC_RAG_DEMO_ENABLED`. Somente o valor `true`, depois de `trim().toLowerCase()`,
habilita a demo; valores ausentes, vazios, `false`, `1`, `yes` e outros preservam o app normal.
Esse flag não habilita o backend: `DEMO_ENABLED` e `DEMO_ALLOWED_SOURCE_PREFIXES` continuam
sendo uma configuração separada. A implementação M2 não faz requests durante construção,
renderização, troca de aba ou uso dos exemplos; não chama provider, Qdrant, `/v1/demo/run`,
`/v1/demo/retrieval` nem executa live run.

Para visualizar localmente sem depender do backend, use no PowerShell:

```powershell
cd frontend
$env:EXPO_PUBLIC_RAG_DEMO_ENABLED="true"
npm run web
```

O app nativo mantém `orientation: "portrait"`; no Expo Web, a validação usa landscape.
Os viewports-alvo são `1366x768`, `1024x600`, `390x844` e `360x800`. A implementação inclui
container responsivo, reflow/compactação das abas em telas estreitas, cards empilhados,
safe-area, foco visível na Web, alvos de toque, estados acessíveis, contraste para temas
claro/escuro e suporte a escala de fonte. Esses aspectos são estados implementados e foram
verificados pelos testes e pelo bundle Expo Web sem backend; uma nova validação visual manual
de runtime permanece uma pendência caso seja necessária para a entrega final.

Evidências do fechamento M2: 49 testes Jest aprovados, `npm run typecheck` aprovado, Ruff
aprovado, `git diff --check` aprovado e bundle Expo Web gerado sem backend. O catálogo usa
somente referências versionadas do próprio repositório; não incorpora respostas, excerpts,
scores, tempos, segredos, paths pessoais ou dados `CHATSCM`.

### M3 — integração live opt-in do cliente Expo

Status: **implementado no frontend**, no HEAD `c7925d7`; a operação live com provider externo,
Qdrant real e POST real permanece **aguardando validação**. M3 conecta a aba `Chat` ao endpoint
`POST /v1/demo/run` e apresenta a execução sanitizada na aba `Como funciona`. O backend M1, os
providers, o corpus, os embeddings e o Qdrant não foram alterados nesta etapa.

O fluxo autorizado é explícito: `GET /v1/demo/runtime` é consultado uma vez na montagem da demo;
`POST /v1/demo/run` só ocorre ao enviar uma pergunta ou ao acionar retry. Um reducer/estado
compartilhado mantém runtime e a última execução entre `Chat` e `Como funciona`, sem reexecução
ao trocar abas ou ao alternar a apresentação. O replay continua fora do M3.

O cliente valida DTOs fechados, tipos, valores finitos, monotonicidade dos tempos, correlação de
`citation_ids` com `source.order` e limites de conteúdo. A URL usa política de origem segura:
HTTP somente para loopback/RFC1918 e HTTPS somente para origens exatas configuradas em
`EXPO_PUBLIC_RAG_ALLOWED_HTTPS_ORIGINS`; wildcard, query/hash e origens arbitrárias são
rejeitados. Erros são reduzidos a códigos/status/mensagens allowlisted, sem expor corpo cru,
traceback, prompt, token, path ou segredo.

A resposta apresentada preserva texto, grounding estrutural, citações e fontes permitidas. Score
ausente aparece como **Não disponível**; `grounded=true` significa somente cobertura estrutural
das citações e nunca prova de verdade factual, clínica ou de entailment semântico. O indicador de
single-query é uma descrição estática da configuração desta versão; diagnósticos de multi-query,
decomposição, retry count, contexto final, dimensão de embedding e métricas pre/post-reranking
não fazem parte do DTO M1 e aparecem como indisponíveis, sem serem inventados.

A interface cobre vazio, loading, erro sanitizado, retry manual, fontes e grounding, além dos
modos de apresentação automático, `Anterior`, `Próximo` e `Ver tudo`. A troca de abas e esses
modos não fazem novas requisições. O Laboratório permanece uma superfície futura do M4.

Evidências registradas pelo QA: 84 testes Jest, `npm run typecheck`, `git diff --check` e bundle
Expo Web offline aprovados; Ruff não foi executado pelo QA porque o executável não estava
disponível naquele ambiente. Não foram executados runtime real com provider/Qdrant, POST live,
nem validação manual dos quatro viewports (`1366x768`, `1024x600`, `390x844`, `360x800`); esses
itens permanecem **aguardando validação**. A revisão de segurança aprovou o frontend de forma
condicionada, mas os logs crus preexistentes de Groq/Ollama continuam um bloqueio P1 para uso
externo/produção e estão fora do escopo autorizado do M3. Manter `DEMO_ENABLED=false` fora de
ambiente local controlado e não usar dados reais ou pessoais.

### Fronteira M4

M4 continua planejado como um Laboratório experimental para controles de Dense, Dense+rerank,
Hybrid, Top K, Multi-query e comparação, condicionado a contrato de runtime, privacidade,
autenticação, rate limiting e logs sanitizados. Replay e qualquer ampliação de backend são
futuros e não fazem parte desta implementação.
