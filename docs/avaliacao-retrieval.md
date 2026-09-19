# Avaliação do Retrieval

## Baseline 0.5.1 — 2026-09-19

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.714

## Experimento 0.5.2 — reranking lexical

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.786

O reranking melhorou a posição de algumas fontes, incluindo vacinação na gestação de rank 2 para rank 1, mas não recuperou a carta de direitos e deveres no top 5.

## Experimento 0.5.3 — retrieval híbrido

Hipótese: o problema restante está na primeira etapa de recall. Se o documento correto não entra no conjunto denso de candidatos, reranking posterior não consegue recuperá-lo.

A 0.5.3 adiciona BM25 em português como vetor esparso e combina:

- dense embedding multilíngue;
- BM25 sparse retrieval;
- Reciprocal Rank Fusion;
- agrupamento por página;
- reranking lexical já existente.

Depois da reindexação híbrida, executar:

    docker compose run --rm api ragtest-evaluate-retrieval

Registrar HitRate@5 e MRR@5 para comparar com 0.5.1 e 0.5.2.
