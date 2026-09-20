# RagTest

Módulo RAG reutilizável via API.

## Fase 0.5.9 — avaliação holdout

A 0.5.8 foi validada e mesclada. O modo padrão continua sendo `dense-rerank`.

A 0.5.9 amplia a avaliação sem alterar os parâmetros de retrieval:

- `dev`: 7 consultas já usadas durante o desenvolvimento;
- `holdout`: 15 consultas novas, congeladas antes da primeira execução;
- `all`: combinação das duas suites, totalizando 22 consultas.

Dataset:

    2026-09-20-v1

O objetivo é verificar generalização. O holdout não deve ser usado para ajustar pesos e depois ser apresentado como uma avaliação independente.

## Atualizar

    git fetch origin
    git switch --track origin/feature/holdout-evaluation-0.5.9
    docker compose down
    docker compose up --build -d
    curl http://localhost:8000/health
    curl http://localhost:8000/ready

Não recrie a collection. O corpus permanece com 767 chunks.

## Primeira execução do holdout — concluída

Resultado preservado do modo padrão:

    dense-rerank
    HitRate@5=1.000 (15/15)
    MRR@5=0.933

Foram 13 casos com fonte esperada em rank 1 e 2 casos em rank 2, sem falhas no top 5.

Comparação concluída:

    MODE            HITRATE@5   MRR@5
    dense             1.000      0.889
    dense-rerank      1.000      0.933
    hybrid            1.000      0.878

A regressão histórica da suite dev também foi confirmada:

    dense             1.000      0.857
    dense-rerank      1.000      0.929
    hybrid            1.000      0.821

A primeira saída do holdout deve ser preservada como resultado experimental. Se surgirem falhas, elas devem ser analisadas, mas não se deve recalibrar o perfil e reutilizar o mesmo holdout como se continuasse sendo um teste não visto.

## Segurança

Nunca versione GEMINI_API_KEY. Use apenas .env local.


## Documentação de decisões

Mudanças de arquitetura, comportamento padrão e metodologia são registradas em:

    docs/decisoes-tecnicas.md

Problemas e correções continuam sendo registrados separadamente em:

    docs/dificuldades-tcc.md


## Fase 0.5.10 — métricas source-level

A próxima evolução do avaliador mantém HitRate/MRR e acrescenta:

    SourceRecall@k
    SourceNDCG@k
    unique_sources por consulta

O retrieval não muda e a collection de 767 chunks não precisa ser recriada.


### Validação da 0.5.10

Runtime verificado:

    HOLDOUT
    dense         HitRate=1.000 MRR=0.889 SourceRecall=1.000 SourceNDCG=0.917
    dense-rerank  HitRate=1.000 MRR=0.933 SourceRecall=1.000 SourceNDCG=0.941
    hybrid        HitRate=1.000 MRR=0.878 SourceRecall=0.967 SourceNDCG=0.885

    DEV
    dense         HitRate=1.000 MRR=0.857 SourceRecall=1.000 SourceNDCG=0.903
    dense-rerank  HitRate=1.000 MRR=0.929 SourceRecall=1.000 SourceNDCG=0.936
    hybrid        HitRate=1.000 MRR=0.821 SourceRecall=1.000 SourceNDCG=0.869

A nova métrica mostrou uma perda de cobertura no modo hybrid que o HitRate isolado não evidenciava.


## Fase 0.5.11 — groundedness e citações verificáveis

A 0.5.11 reforça a etapa de geração sem alterar retrieval ou reindexar o corpus:

- remove score de retrieval do prompt enviado ao LLM;
- marca cada fonte recuperada como dado não confiável;
- instrui o modelo a ignorar comandos/prompt injection presentes nos documentos;
- valida citações `[n]` contra as fontes realmente retornadas;
- tenta reparar a geração uma vez quando a citação é inválida ou ausente;
- usa fallback seguro se a segunda tentativa também falhar;
- adiciona `grounded`, `citation_ids` e `citation_retry_count` à resposta do chat.

Self-check determinístico:

    ragtest-check-grounding

Não exige `ragtest-ingest --recreate`.


### Validação da 0.5.11

Verificado localmente:

    docker build: sucesso
    /health: version 0.5.11
    /ready: qdrant ok
    ragtest-check-grounding: todos os checks passaram
    /v1/chat: grounded=true
    citation_ids=[1,2,3]
    citation_retry_count=0

O teste real confirmou que as citações retornadas correspondem às fontes disponíveis. Também revelou uma limitação separada: uma pergunta composta sobre direitos e deveres recuperou contexto suficiente para direitos, mas não para detalhar deveres. Isso foi registrado como Dificuldade TCC #11 e será investigado sem alterar o retrieval nesta fase.


## Fase 0.5.12 — experimento controlado de multi-query

Antes de automatizar a decomposição de perguntas compostas, a 0.5.12 valida o mecanismo de recuperação com subconsultas explícitas.

Novo comando:

    ragtest-search-multi

Exemplo diagnóstico:

    ragtest-search-multi "Quais são os direitos e deveres da pessoa usuária da saúde?" --subquery "Quais são os direitos da pessoa usuária da saúde?" --subquery "Quais são os deveres da pessoa usuária da saúde?" --category direitos_saude --limit 5 --per-query-limit 5

Cada subconsulta usa o perfil `dense-rerank` já validado. Os resultados por página são deduplicados e combinados por Reciprocal Rank Fusion (RRF). Quando subconsultas são informadas, a pergunta original não participa da fusão por padrão para evitar duplicar a intenção dominante. Use `--include-original` apenas para comparação diagnóstica.

Self-check determinístico:

    ragtest-check-multi-query

Nesta fase, o endpoint `/v1/chat` ainda não decompõe perguntas automaticamente. O objetivo é verificar primeiro se a fusão das subconsultas corrige a cobertura observada na Dificuldade TCC #11.


### Ajuste após o primeiro experimento 0.5.12

O primeiro teste real mostrou que incluir a pergunta composta como terceiro voto de RRF reforçava as mesmas páginas da subconsulta de direitos. A página 13, recuperada em rank 1 pela subconsulta de deveres, ficou fora do top 5 fundido.

A correção mantém o RRF, mas funde somente as subconsultas explícitas por padrão. Isso foi registrado como Dificuldade TCC #12.


### Validação do experimento multi-query 0.5.12

Verificado localmente:

    /health: version 0.5.12
    ragtest-check-multi-query: todos os checks passaram
    fusion policy: subqueries only

Caso direitos + deveres:

    consulta composta original: página 13 em rank 10
    primeira fusão (original + subconsultas): página 13 fora do top 5
    fusão corrigida (subconsultas somente): página 13 em rank 2

A correção confirma que remover o voto redundante da pergunta original melhora a cobertura da subintenção minoritária sem aumentar o top-k global.


## Fase 0.5.13 — decomposição automática no chat

A 0.5.13 integra o mecanismo multi-query validado ao `/v1/chat`.

Fluxo:

    pergunta
      -> heurística conservadora de multi-intent
      -> planejador LLM apenas quando necessário
      -> 2-3 subconsultas
      -> dense-rerank por subconsulta
      -> RRF somente entre subconsultas
      -> contexto final
      -> resposta grounded com citações

Resiliência:

- pergunta simples: usa single-query e não chama o planejador;
- JSON inválido ou menos de duas subconsultas: fallback para single-query;
- pode ser desativado globalmente com `RETRIEVAL_AUTO_DECOMPOSE=false`;
- pode ser desativado por requisição com `"auto_decompose": false`.

Novos campos de resposta:

    multi_query_used
    retrieval_queries
    decomposition_status

Self-check:

    ragtest-check-decomposition

Não exige reindexação.


### Validação da 0.5.13

Verificado localmente:

    /health: version 0.5.13
    /ready: qdrant ok
    ragtest-check-decomposition: todos os checks passaram
    multi_query_used=true
    decomposition_status=multi-query
    retrieval_queries=[direitos..., deveres...]
    página 13 presente nas fontes
    grounded=true
    citation_retry_count=0

O caminho composto passou a responder direitos e deveres na mesma chamada. O caminho simples também foi validado no endpoint real: pergunta sobre vacinação de idosos retornou `multi_query_used=false`, `decomposition_status=not-needed`, uma única `retrieval_query`, `grounded=true` e `citation_retry_count=0`.


## Fase 0.5.14 — CI e execução real da suíte de testes

A 0.5.14 não altera retrieval, corpus ou geração. O objetivo é restaurar o gate de qualidade automatizado.

Mudanças:

- corrige as 8 violações Ruff observadas no workflow do `main`;
- mantém catches amplos apenas onde são intencionais e documentados;
- fixa Ruff em `0.16.8`;
- declara explicitamente as regras usadas no gate;
- separa lint e pytest em jobs independentes;
- evita CI para mudanças exclusivamente em documentação.

Não exige reindexação.


### Validação da CI 0.5.14

O gate automatizado foi validado no GitHub Actions:

    lint: All checks passed!
    pytest: 51 passed, 4 warnings

A primeira execução da suíte havia revelado uma expectativa obsoleta no teste de health (50 passed / 1 failed); após a correção para comparar com `get_settings().app_version`, todos os testes passaram.

Os warnings restantes são não bloqueantes e vêm de depreciação do TestClient/AnyIO e da verificação de compatibilidade do cliente Qdrant em testes sem servidor real.


### Validação local da 0.5.14

Após a CI verde, a imagem Docker foi reconstruída e validada localmente:

    /health: status=ok, version=0.5.14
    /ready: status=ready, qdrant=ok

Com isso, a 0.5.14 está validada tanto na suíte automatizada quanto no runtime local. Não houve mudança de corpus e nenhuma reindexação foi necessária.
