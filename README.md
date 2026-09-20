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

Cada consulta usa o perfil `dense-rerank` já validado. Os resultados por página são deduplicados e combinados por Reciprocal Rank Fusion (RRF).

Self-check determinístico:

    ragtest-check-multi-query

Nesta fase, o endpoint `/v1/chat` ainda não decompõe perguntas automaticamente. O objetivo é verificar primeiro se a fusão das subconsultas corrige a cobertura observada na Dificuldade TCC #11.
