# Avaliação do Retrieval

## Experimentos antes da correção de ingestão

| Versão | Estratégia | HitRate@5 | MRR@5 |
| --- | --- | ---: | ---: |
| 0.5.1 | dense | 0.857 | 0.714 |
| 0.5.2 | dense + reranking lexical | 0.857 | 0.786 |
| 0.5.3 | dense + BM25 + RRF | 0.714 | 0.607 |
| 0.5.4 | BM25 enriquecido com metadados | 0.857 | 0.690 |

Esses resultados foram obtidos quando a Carta dos Direitos e Deveres tinha 0 chunks e não devem ser comparados diretamente com experimentos posteriores como se o corpus fosse idêntico.

## 0.5.5 — diagnóstico da cobertura

A auditoria identificou a Carta dos Direitos e Deveres com 28 páginas, 0 páginas com texto, 0 caracteres e 0 chunks.

## 0.5.6 — corpus corrigido por OCR seletivo

Resultados observados em 2026-09-19:

- Carta dos Direitos e Deveres: 28/28 páginas recuperadas por OCR;
- 41.237 caracteres extraídos;
- 62 chunks gerados somente para esse documento;
- corpus total: 767 chunks, contra 699 antes do OCR;
- caderneta da gestante: 50/50 páginas com texto, incluindo 3 páginas recuperadas por OCR;
- HitRate@5: 1.000 (7/7);
- MRR@5: 0.821.

A consulta de direitos/deveres passou a recuperar a carta esperada no rank 1.

Este resultado é a primeira baseline pós-correção de cobertura, mas usa a estratégia híbrida da 0.5.4. Para separar o efeito do OCR do efeito da estratégia de retrieval, a 0.5.7 compara várias estratégias sobre exatamente a mesma collection de 767 chunks.

## 0.5.7 — benchmark no mesmo corpus

Perfis avaliados:

- dense: sem BM25 e sem boost lexical;
- dense-rerank: dense + reranking lexical;
- hybrid: dense + BM25 + RRF + reranking lexical.

Todos rodam sobre o mesmo corpus já corrigido por OCR.

Executar:

    docker compose run --rm api ragtest-evaluate-retrieval

Ou um perfil isolado:

    docker compose run --rm api ragtest-evaluate-retrieval --mode dense
    docker compose run --rm api ragtest-evaluate-retrieval --mode dense-rerank
    docker compose run --rm api ragtest-evaluate-retrieval --mode hybrid

A comparação 0.5.7 é metodologicamente mais adequada para decidir a estratégia de retrieval, pois mantém o corpus constante.
