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

Status: implementado no commit `ea14f8c` e verificado após QA pelos gates registrados no
handoff desta sidequest. Esta etapa adiciona somente a fundação visual da Demo Técnica no
frontend Expo: quatro abas (`Chat`, `Como funciona`, `Laboratório` e `O que ainda falta`),
estados vazios/neutros, catálogo de roadmap com referências verificáveis e contratos TypeScript
preparados para uso futuro. A narrativa `Como funciona` expõe 11 etapas, a aba Chat mantém
uma ação futura desabilitada e a identidade visual informa que esta não é a versão final do
produto Se Cuida Mulher. O Laboratório apresenta oito controles futuros desabilitados.

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

### Limites e fronteira M3

M2 não implementa requests, replay, execução demonstrativa, ranking, resposta gerada,
grounding ao vivo, telemetria ou integração de runtime. M3 só deve avançar após revisão dos
seguintes pontos: validação dos DTOs de runtime no cliente, allowlist de origem/base URL com
HTTPS quando aplicável, CORS/autenticação/privacidade e revisão dos exemplos, grounding e
telemetria antes de qualquer uso com dados ou provider.

Pendências são classificadas como **aguardando validação**; não há afirmação de que M3 esteja
implementado.
