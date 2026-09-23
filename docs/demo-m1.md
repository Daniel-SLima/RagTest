# Demo segura M1

Status: implementado nesta sidequest; aguardando validação independente do QA.

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
