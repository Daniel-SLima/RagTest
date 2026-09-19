# Avaliação do Retrieval

## Baseline 0.5.1 — 2026-09-19

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.714

## Experimento 0.5.2 — reranking lexical

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.786

O reranking melhorou a posição de algumas fontes, mas não recuperou a carta de direitos e deveres no top 5.

## Experimento 0.5.3 — dense + BM25 + RRF

- HitRate@5: 0.714 (5/7)
- MRR@5: 0.607

O experimento piorou as duas métricas. A consulta sobre vacinação na gestação deixou de encontrar a fonte esperada no top 5 e a carta de direitos/deveres continuou ausente.

Dois fatores foram identificados:

1. O BM25 indexava apenas o conteúdo do chunk, não os metadados documentais. Assim, correspondências explícitas no nome do arquivo não participavam do recall esparso.
2. O corte relativo de 0.22 foi reaproveitado depois da fusão RRF. A escala do score fusionado é diferente da similaridade cosseno usada anteriormente, então o mesmo corte eliminou candidatos úteis e em alguns casos reduziu a lista final a apenas um resultado.

## Experimento 0.5.4 — BM25 enriquecido com metadados

Hipótese:

- indexar source, filename, category e audience junto com o conteúdo no BM25 aumenta o recall lexical;
- usar pesos neutros dense=1.0 e sparse=1.0 evita favorecer prematuramente o BM25;
- desativar o corte relativo na etapa híbrida evita aplicar um threshold calibrado em outra escala de score.

Parâmetros:

    HYBRID_DENSE_WEIGHT=1.0
    HYBRID_SPARSE_WEIGHT=1.0
    RETRIEVAL_SCORE_MARGIN=0.0

Após reindexar, executar:

    docker compose run --rm api ragtest-evaluate-retrieval

Comparar diretamente com 0.5.1, 0.5.2 e 0.5.3.
