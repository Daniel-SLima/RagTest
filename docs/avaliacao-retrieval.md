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

### Resultado verificado da 0.5.7

| Modo | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| dense | 1.000 (7/7) | 0.857 |
| dense-rerank | 1.000 (7/7) | 0.929 |
| hybrid | 1.000 (7/7) | 0.821 |

Todos os perfis recuperaram pelo menos uma fonte esperada no top 5. A diferença observada ficou na ordenação.

No conjunto atual de sete consultas, `dense-rerank` obteve o maior MRR@5. Exemplos:

- vacinação durante a gestação: fonte esperada foi de rank 2 no dense para rank 1 no dense-rerank;
- direitos e deveres: fonte esperada permaneceu em rank 1;
- implante contraceptivo: fonte esperada ficou em rank 2 no dense-rerank e rank 4 no hybrid.

Conclusão experimental: `dense-rerank` é a estratégia com melhor resultado medido neste benchmark controlado. Isso ainda não deve ser generalizado como superioridade definitiva, pois o conjunto de avaliação possui apenas sete consultas e os julgamentos de relevância ainda são majoritariamente por fonte esperada.


## 0.5.8 — consolidação do perfil padrão

A 0.5.8 não cria uma nova hipótese de ranking. Ela transforma o perfil `dense-rerank`, que obteve o maior MRR@5 no benchmark 0.5.7, em candidato padrão do runtime.

Mudanças:

- `RETRIEVAL_MODE=dense-rerank` como padrão;
- parâmetros de cada perfil ficam versionados em código;
- busca e chat usam o perfil selecionado;
- `dense` e `hybrid` permanecem disponíveis para benchmark/diagnóstico;
- collection permanece com dense + sparse, portanto não há reindexação.

Status: validado localmente. A busca padrão informou `Mode: dense-rerank`, a consulta de vacinação na gestação manteve a fonte esperada no rank 1 e o benchmark reproduziu exatamente: dense 1.000/0.857, dense-rerank 1.000/0.929 e hybrid 1.000/0.821 (HitRate@5/MRR@5).
