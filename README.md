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


## Fase 0.5.15 — fingerprint e reprodutibilidade do runtime

Antes de fixar novas versões de FastEmbed e da imagem Qdrant, a 0.5.15 registra o ambiente efetivamente validado.

Novo comando:

    ragtest-runtime-info

Ele mostra:

- versão do RagTest e dos principais pacotes;
- versão/commit do servidor Qdrant;
- modelos dense/sparse configurados;
- estratégia de retrieval;
- chunk size/overlap;
- nome, schema, metadata e contagem da collection.

O comando é somente diagnóstico: não escreve na collection e não exige reindexação.


### Baseline observada e pinning da 0.5.15

O fingerprint local confirmou:

    fastembed: 0.8.0
    qdrant-client: 1.19.1
    qdrant_server: 1.19.1
    qdrant_commit: 6ab21cac18ebb6f4ae29102c7f8f5cc11affd5de
    dense: 384 / Cosine
    sparse: idf
    points: 767
    indexed_vectors: 767

Com base nessa combinação já validada, a segunda etapa da 0.5.15 fixa:

    fastembed==0.8.0
    qdrant-client==1.19.1
    qdrant/qdrant:v1.19.1

A baseline completa está em `docs/runtime-baseline-0.5.15.md`.

A aplicação desses pins não exige reindexação; o próximo teste deve confirmar que o fingerprint continua igual após rebuild.


### Validação pós-pinning da 0.5.15

Após rebuild com as versões exatas:

    fastembed: 0.8.0
    qdrant-client: 1.19.1
    qdrant_server: 1.19.1
    qdrant_commit: 6ab21cac18ebb6f4ae29102c7f8f5cc11affd5de
    points_count: 767
    indexed_vectors_count: 767

A CI também passou:

    ruff: All checks passed!
    pytest: 53 passed, 4 warnings

Portanto, o pinning não alterou o runtime nem a collection existente.


## Fase 0.5.16 — sincronização segura da ingestão

O primeiro passo da 0.5.16 trata uma limitação da ingestão incremental: IDs determinísticos permitem upsert, mas chunks antigos podem permanecer quando documentos são editados ou removidos.

Novo comando somente leitura:

    ragtest-plan-ingestion-sync

Ele compara o corpus atual com a collection e informa:

- chunks atuais;
- pontos indexados;
- pontos que faltam no índice;
- pontos obsoletos;
- fontes órfãs que não existem mais no diretório;
- diferenças por fonte.

Nesta primeira etapa o comando não grava nem remove nada no Qdrant. A exclusão sincronizada só será habilitada depois de validar o plano contra a collection atual.


### Etapa 2 — aplicação controlada da sincronização

A prévia somente leitura foi validada sobre a collection real:

    Source files       : 18
    Files loaded       : 18/18
    Current chunks     : 767
    Indexed points     : 767
    Missing points     : 0
    Stale points       : 0
    Orphan sources     : 0
    In sync            : yes

A 0.5.16 agora adiciona:

    ragtest-sync-ingestion
    ragtest-check-ingestion-sync

`ragtest-sync-ingestion` é dry-run por padrão. Para aplicar uma diferença é obrigatório usar:

    ragtest-sync-ingestion --apply

Proteções:

- recusa sincronização se nenhum arquivo fonte for encontrado;
- recusa escrita quando houver erro de carregamento;
- insere/reindexa os novos chunks antes de remover os antigos;
- verifica novamente a collection após aplicar;
- se já estiver sincronizado, `--apply` faz no-op e não altera pontos.


### Etapa 3 — self-check de escrita/exclusão em collection isolada

A validação da collection principal confirmou que `--apply` faz no-op quando não há diferenças e preserva 767/767 pontos.

Para testar o caminho destrutivo sem tocar na collection real, a 0.5.16 adiciona:

    ragtest-check-ingestion-sync-qdrant

O comando cria uma collection temporária exclusiva, simula um documento alterado, um adicionado e um removido, executa upsert + delete por ID, valida que o estado final fica sincronizado e apaga a collection temporária ao final.

A collection `ragtest_documents` não é modificada por esse self-check.


### Validação completa da sincronização 0.5.16

O caminho destrutivo foi validado em uma collection Qdrant temporária isolada:

    [PASS] initial plan detects 2 missing
    [PASS] initial plan detects 2 stale
    [PASS] removed source is orphan
    [PASS] final collection has 2 points
    [PASS] final plan has no missing points
    [PASS] final plan has no stale points
    [PASS] final plan has no orphan sources
    [PASS] final plan is in sync

    All Qdrant ingestion sync integration self-checks passed.
    Main application collection was not touched.

Após o teste, o fingerprint da collection principal continuou:

    points_count: 767
    indexed_vectors_count: 767

CI final da branch:

    ruff: All checks passed!
    pytest: 58 passed, 4 warnings

Com isso, a sincronização incremental ficou validada nos três cenários: planejamento read-only, no-op seguro na collection real e insert/delete real em collection temporária.


## Fase 0.5.17 — auditoria estrutural de DOCX

O loader atual extrai apenas parágrafos do corpo do DOCX. Antes de incluir tabelas, cabeçalhos ou rodapés e alterar o corpus, a 0.5.17 mede a estrutura real dos arquivos.

Novo comando:

    ragtest-audit-docx-structure

A auditoria informa apenas contagens estruturais:

- parágrafos do corpo;
- tabelas, linhas e células;
- células não vazias;
- seções;
- parágrafos/tabelas em cabeçalhos;
- parágrafos/tabelas em rodapés.

Por privacidade, o comando não imprime o conteúdo dos documentos. Ele não modifica Qdrant e não exige reindexação.


### Resultado da auditoria DOCX 0.5.17

A auditoria local encontrou 3 DOCX e confirmou que nenhum possui conteúdo estrutural relevante fora dos parágrafos do corpo:

    chatscm.docx
      body paragraphs: 145/208 non-empty
      body tables: 0
      headers with text: 0
      footers with text: 0

    chatscm_gestante.docx
      body paragraphs: 89/115 non-empty
      body tables: 0
      headers with text: 0
      footers with text: 0

    chatscm_gestante_parte_2.docx
      body paragraphs: 53/75 non-empty
      body tables: 0
      headers with text: 0
      footers with text: 0

    Files with structural content outside body paragraphs: 0

Conclusão: para o corpus atual, não há benefício observado em ampliar o loader para tabelas/cabeçalhos/rodapés. O corpus e a collection permanecem inalterados em 767 chunks/pontos.

Resultado detalhado: `docs/docx-structure-audit-0.5.17.md`.


## Fase 0.5.18 — semântica explícita dos rótulos de avaliação

O dataset `2026-09-20-v1` permanece congelado. Seus casos usam `expected_sources`, um campo histórico que não distingue entre:

- fontes alternativas aceitáveis; e
- fontes que precisam aparecer conjuntamente para considerar a cobertura completa.

A 0.5.18 não altera os resultados históricos. Ela adiciona o contrato para datasets futuros:

    acceptable_sources  -> alternativas OR
    required_sources    -> todas são deliberadamente exigidas

Novo comando:

    ragtest-audit-evaluation-labels

Ele audita somente a estrutura dos rótulos e ajuda a evitar interpretações excessivas de SourceRecall/SourceNDCG no dataset legado.


### Base da avaliação v2 na 0.5.18

A auditoria local confirmou a hipótese metodológica:

    Total cases             : 22
    Legacy expected_sources : 22
    Legacy multi-source     : 5
    Explicit semantic cases : 0

A segunda etapa da 0.5.18 permite que o avaliador processe arquivos JSON externos com rótulos explícitos:

    acceptable_sources -> OR
    required_sources   -> AND

E introduz:

    PassRate@k
    AcceptableHitRate@k
    RequiredRecall@k
    RequiredNDCG@k

Self-check determinístico:

    ragtest-check-evaluation-v2

O template `docs/evaluation-v2-template.json` demonstra o formato, mas não é um novo holdout nem contém julgamentos reais.
