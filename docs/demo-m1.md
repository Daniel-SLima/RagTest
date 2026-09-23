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

Evidências do fechamento pelo orquestrador: 85 testes Jest em 9 suites, `npm run typecheck`,
Ruff via `.venv\\Scripts\\ruff.exe` e `git diff --check` aprovados, além do bundle Expo Web
offline. O QA anterior registrou 84 testes e não executou Ruff porque o executável não estava
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

### M3.5 — validação de runtime local controlado

Status: **RUNTIME VALIDATED somente em ambiente local/controlado**, no HEAD funcional
`7015db8` (`fix: theme demo answer presentation`). Esta validação não transforma a demo em
serviço operacional externo e não autoriza M4. Os commits documentais anteriores permanecem
`c90822b` e `824cbc0`.

#### Ambiente e controle negativo

O cenário validado usou FastAPI em `127.0.0.1:8001`, sem alterar `.env`, com
`DEMO_ENABLED=true`, allowlist pública, Qdrant local em `localhost:6333` contendo os 767 pontos
preservados, Ollama local com `qwen3:8b` e CORS restrito ao cliente local. Nenhuma transmissão
externa foi realizada e nenhum conteúdo `CHATSCM` ou dado pessoal foi usado.

Como controle negativo, a composição na porta 8000 com `DEMO_ENABLED=false` manteve o runtime
demo indisponível: `GET /v1/demo/runtime` respondeu `404`, como esperado quando as rotas demo não
são registradas.

#### Evidências observadas

- `GET /health`, `GET /ready` e `GET /v1/demo/runtime`: `200` no cenário habilitado;
- `POST /v1/demo/retrieval`: `200`, uma fonte pública da página 34 e scores retornados;
- `POST /v1/demo/run`: `200`, `grounded=true`, uma citação correlacionada à fonte e timings
  monotônicos;
- Expo Web em `8082`: runtime disponível, resposta Markdown renderizada, fontes e grounding
  visíveis, com navegação observada entre `Chat` e `Como funciona`;
- o tema escuro foi corrigido no `7015db8` e a apresentação observada permaneceu legível.

Essas evidências comprovam somente o cenário local descrito. Não comprovam disponibilidade
externa, segurança de produção, entailment clínico ou operação com provider remoto.

#### Comportamento de requisições e estados

Foi observado loading durante a execução; o runtime é consultado uma vez por montagem e uma
execução `POST` ocorre mediante ação explícita. Não foram observados novos runs ao trocar abas,
abrir o pipeline, alternar `Automático`, `Apresentação`, `Próximo` ou `Anterior`. No controle
negativo, o erro `404` foi apresentado de forma amigável e o retry manual foi observado.

#### Pendências importantes

- os quatro viewports (`1366x768`, `1024x600`, `390x844`, `360x800`) não foram observados
  individualmente;
- o tema claro não foi validado manualmente;
- retry live independente não foi demonstrado fora do controle observado;
- inspeção direta de Network/console do DevTools permanece pendente.

#### Segurança e fronteira de autorização

A validação de segurança é **PASS local** e **BLOCKED para uso externo/produção**: permanecem
logs crus preexistentes de Groq/Ollama, ausência de autenticação e rate limiting e risco
residual de prompt injection. Manter `DEMO_ENABLED=false` fora de ambiente local controlado e
nunca usar dados pessoais ou `CHATSCM`. M4 não está autorizado; o Laboratório, seus controles e
qualquer expansão de backend continuam apenas planejados.

### M3.6 — fechamento visual e retry live local

Status: **PASS local/controlado**, com HEAD inicial documental `d24c76a` e correção funcional
`62a2983` para títulos longos no viewport de 360 px. Esta validação não autoriza operação
externa/produção nem M4.

#### Viewports e tema

Após a correção de títulos longos, foram observados como **PASS** os quatro viewports-alvo:
`1366x768`, `1024x600`, `390x844` e `360x800`. O tema claro não foi observado manualmente nesta
sessão: o IAB/OS permaneceu em tema escuro e não havia emulação disponível; portanto essa
evidência continua **pendente**, sem ser convertida em sucesso.

#### Retry e contagem de requests

Com a API interrompida, a interface exibiu erro amigável; após a restauração, um único retry
explícito gerou um segundo `POST`, obteve sucesso e não produziu duplicação. A tentativa feita
com a API parada não chegou ao backend. No fluxo observado, houve um `GET /v1/demo/runtime` por
montagem, o primeiro `POST` com preflight `OPTIONS` e o segundo `POST` do retry.

O pipeline exibiu 11 etapas correspondentes ao novo run. A navegação, os modos de apresentação e
as abas não iniciaram execuções adicionais.

#### Observabilidade e segurança

DevTools Network/Console não foram observáveis diretamente: o IAB não ofereceu CDP e o Chrome
estava indisponível. A inspeção estática do frontend e o comportamento sanitizado observado
permanecem **PASS** dentro desse limite.

A segurança para uso externo/produção continua **BLOCKED** por logs crus preexistentes de
Groq/Ollama, ausência de autenticação/rate limiting e risco residual de prompt injection. M4
continua não autorizado; não foram alterados código adicional, corpus, Qdrant, providers ou
`.env` nesta etapa.

## M4 — Laboratório experimental de retrieval (2026-09-23)

### Escopo e classificação

O M4 foi implementado na branch isolada `sidequest/ragtest-demo` como uma superfície de
comparação de retrieval no Expo Web. A interface usa exclusivamente `POST /v1/demo/retrieval`
e os três perfis já existentes (`dense`, `dense-rerank` e `hybrid`); não chama
`POST /v1/demo/run`, não gera resposta por LLM e não altera o perfil global do backend.
`Top K` é enviado como `limit` real, restrito a 3, 5 ou 10 na interface. A seleção é por
execução: uma estratégia faz uma requisição e `Comparar todas` faz exatamente três requisições
sequenciais, na ordem Dense, Dense + rerank e Hybrid.

O estado da interface foi classificado como **implementado e validado em LOCAL/CONTROLADO**. O contrato do cliente também
rejeita resposta com mais de 10 fontes, consulta ou modo divergentes e ordenação inválida;
campos nulos, inclusive scores e `generation_ms` no retrieval-only, são apresentados como
`Não disponível`. Exemplos apenas preenchem a pergunta. Multi-query/decomposição aparece como
indisponível no contrato do laboratório, sem simulação.

### Evidências automatizadas e de runtime

- 99 testes Jest aprovados em 11 suites, `npm run typecheck`, Ruff e `git diff --check`
  aprovados após a implementação M4;
- testes direcionados cobrem modelo de comparação, execução single/all, limite real, validação
  de resposta, erro parcial e retry sem apagar resultados já bem-sucedidos;
- no ambiente local/controlado, FastAPI em `127.0.0.1:8001` respondeu aos três modos com a
  pergunta pública sobre vacinação de pessoas idosas, usando Qdrant local com **767 pontos**;
  as respostas retornaram apenas fontes públicas allowlisted e nenhum conteúdo `CHATSCM`;
- os tempos observados foram variáveis por modo (aproximadamente 11,9 s em Dense, 47 ms em
  Dense + rerank e 1,9 s em Hybrid nessa execução), portanto não são ranking de desempenho;
- a UI do Laboratório foi carregada no Expo Web com runtime local disponível. A superfície
  vazia, controles single/compare, descrições dos perfis, métricas históricas e aviso de
  privacidade foram observados. Na validação visual por override real do navegador, os viewports
  `1366x768` e `1024x600` mantiveram três colunas (`flexDirection=row`), enquanto `390x844` e
  `360x800` empilharam os cartões (`flexDirection=column`); `scrollWidth == viewport` em todos,
  sem overflow horizontal. A inspeção direta de Network/console permanece limitada pelo IAB;
  retry e comparação parcial têm evidência automatizada.

As métricas históricas DEV/HOLDOUT são apresentadas separadamente como evidência de benchmark
(`HitRate`, `MRR`, `SourceRecall` e `SourceNDCG`, dataset `2026-09-20-v1`), com as definições e
fontes documentais indicadas na interface. Elas não são resultado da pergunta corrente, não
produzem vencedor numérico e não autorizam afirmar superioridade universal de uma estratégia.
Os tempos também são apenas descritivos e sujeitos à variabilidade do ambiente local.

### Privacidade, limites e pendências

O laboratório exibe aviso para usar somente perguntas públicas e não enviar nomes, prontuários
ou dados pessoais. Não houve alteração de corpus, embeddings, collection Qdrant, providers,
`.env` ou backend funcional; não há cache persistente. O cenário externo/produção continua
**BLOCKED**: permanecem fora deste M4 autenticação, rate limiting, revisão dos logs preexistentes
de providers e qualquer autorização para uso com dados privados ou exposição pública.

Os quatro viewports-alvo foram observados e não apresentaram overflow horizontal. O tema claro
continua sem validação manual nesta sessão; ausência dessa observação não é evidência de sucesso.
O M4 não transforma os benchmarks em validação clínica nem transforma `grounded` ou scores de
retrieval em prova de verdade.

## M5 — Visão rastreável do produto (2026-09-23)

### Estado e fotografia

Status: **M5 VALIDATED para uso LOCAL/CONTROLADO**. A entrega ficou restrita à branch
`sidequest/ragtest-demo`, sem alteração de backend, contrato de chat, retrieval, corpus,
embeddings, coleção Qdrant, providers ou replay. A fotografia versionada no catálogo é:

- branch: `sidequest/ragtest-demo`;
- commit-base: `75c924c`;
- versão: `M5`;
- data: `2026-09-23`.

O commit-base identifica o estado de entrada da sidequest. Cada item também conserva a versão
histórica que sustenta sua evidência; isso não significa que todo item histórico tenha sido
implementado no commit M5.

### Catálogo evidence-based

O catálogo TypeScript versionado tem **12 itens em 12 áreas**, sem parsing de Markdown em runtime,
com os quatro status oficiais e contagens calculadas por funções puras:

- Implementado: **6**;
- Parcial / em desenvolvimento: **2**;
- Planejado: **3**;
- Em estudo: **1**.

As áreas são Núcleo RAG e API, Retrieval e avaliação, Grounding estrutural, Demo Expo, Laboratório
experimental, Sessões e contexto, Base documental e sincronização, Segurança e produção,
Privacidade e LGPD, Avaliação especializada e usabilidade, Integração Se Cuida Mulher e Auditoria
e observabilidade. Cada item mantém explicação simples, detalhe técnico, importância, limitações,
dependências, origem e evidências relativas.

O item obsoleto `m3-replay` foi removido: não havia requisito M5 aprovado para replay e a
especificação determina que ele permaneça fora do escopo. O Laboratório M4 foi corrigido para
**Implementado**, sustentado pela validação local/controlada anterior; avaliação especializada e
usabilidade foi classificada como **Planejado**, pois ainda depende de definição futura. Nenhum
item sem evidência foi convertido em roadmap por inferência.

### Visão apresentada

A aba `O que ainda falta` agora separa `VISÃO GERAL`, `Arquitetura atual` e `Visão planejada`.
Exibe a fotografia do projeto, cards de área com contagens do catálogo, filtros por status e área,
resultado vazio honesto e accordions acessíveis. Cada detalhe mostra texto simples, técnica,
importância, limitações, dependências, evidências e origem; `Por que ainda falta?` só aparece
quando o item possui lacuna registrada. Não são exibidas porcentagens.

A arquitetura atual fica descrita como Demo/Expo → FastAPI → RAG/retrieval/grounding → Qdrant +
provider, mantendo o cliente demonstrativo separado do núcleo RAG. A visão planejada trata a
integração ao Se Cuida Mulher como alvo documentado, não como integração oficial pronta. Saúde,
privacidade/LGPD, autenticação, rate limiting, auditoria, logs sanitizados e prompt injection
continuam limites explícitos; `grounded=true` permanece apenas cobertura estrutural de citações.

### Evidências e gates

O desenvolvimento multiagente registrou: catálogo com 6 testes direcionados e typecheck; tela
com 9 testes direcionados; revisão do Task 1 com PASS; revisão do Task 2 com PASS CONDICIONAL
apenas enquanto faltava a inspeção visual; QA com PASS após a correção mínima das asserções M2
obsoletas no commit `884d265`. O fechamento automatizado ficou em **13 suites / 114 testes**,
`npm run typecheck` e `git diff --check` aprovados.

Na inspeção Expo Web sem backend, os viewports `1366x768`, `1024x600`, `390x844` e `360x800`
mantiveram `scrollWidth == viewport`; os dois primeiros preservaram a composição horizontal e os
dois últimos refluíram para colunas. Fotografia, filtros, cards e a abertura do accordion foram
observados. O tema claro, leitor de tela nativo, Dynamic Type e Network/Console do DevTools não
foram observados nesta sessão; o IAB não expôs CDP, portanto essas ausências permanecem
limitações, não sucessos presumidos.

### Fronteira M6

M6 fica somente proposto como continuação futura: validação externa autorizada, autenticação,
rate limiting, auditoria e observabilidade sanitizadas, revisão de privacidade/LGPD e eventual
integração formal ao Se Cuida Mulher. Nenhum desses trabalhos foi iniciado nesta sidequest; replay
continua fora do escopo.
