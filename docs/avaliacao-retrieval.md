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


## 0.5.9 — suite holdout congelada

A 0.5.9 amplia a avaliação sem alterar os parâmetros dos perfis de retrieval.

Dataset versionado:

    2026-09-20-v1

Divisão:

- dev: 7 consultas já utilizadas ao longo do desenvolvimento;
- holdout: 15 consultas novas, congeladas antes da primeira execução;
- all: 22 consultas.

Objetivo metodológico: medir generalização e reduzir o risco de concluir qualidade com base apenas nos mesmos casos usados para orientar os ajustes anteriores.

O primeiro teste deve ser:

    docker compose run --rm api ragtest-evaluate-retrieval --suite holdout --mode dense-rerank

Em seguida:

    docker compose run --rm api ragtest-evaluate-retrieval --suite holdout --mode all

E a regressão histórica:

    docker compose run --rm api ragtest-evaluate-retrieval --suite dev --mode all

Regra experimental: a primeira execução do holdout deve ser preservada. Se forem observadas falhas, elas podem orientar novos experimentos, mas o mesmo holdout deixa de ser considerado totalmente não visto para uma nova alegação de validação independente.


### Primeira execução do holdout — resultado preservado

Modo avaliado primeiro, antes de comparar com alternativas:

    dense-rerank

Resultado:

    HitRate@5: 1.000 (15/15)
    MRR@5: 0.933

Distribuição dos primeiros ranks esperados:

- 13 casos em rank 1;
- 2 casos em rank 2;
- 0 falhas no top 5.

Casos em rank 2:

1. `holdout-caderneta-gestante`: a Caderneta da Gestante apareceu em rank 2, atrás de `gestacao/cartilha_saude_bucal_gestante.pdf`.
2. `holdout-vacinas-gestante-parafrase`: a Caderneta da Gestante apareceu em rank 2 e o calendário nacional da gestante em rank 5; `chatscm/chatscm_gestante.docx` ficou em rank 1.

Interpretação: o perfil padrão mostrou boa recuperação no primeiro holdout congelado, sem casos FAIL. A métrica é source-level e permite múltiplas fontes esperadas, portanto um PASS não implica que o documento mais específico esteja sempre no primeiro lugar. O conjunto ainda é pequeno e foi construído dentro do corpus conhecido, então o resultado deve ser tratado como evidência positiva de generalização, não como prova definitiva.

Próximos comandos:

    docker compose run --rm api ragtest-evaluate-retrieval --suite holdout --mode all
    docker compose run --rm api ragtest-evaluate-retrieval --suite dev --mode all


### Comparação completa no holdout

Resultado verificado:

| Modo | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| dense | 1.000 (15/15) | 0.889 |
| dense-rerank | 1.000 (15/15) | 0.933 |
| hybrid | 1.000 (15/15) | 0.878 |

Os três modos mantiveram recall de fonte esperado no top 5 para todos os 15 casos, mas `dense-rerank` obteve a melhor ordenação segundo MRR.

A suite dev também foi executada novamente e reproduziu exatamente a baseline histórica:

| Modo | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| dense | 1.000 (7/7) | 0.857 |
| dense-rerank | 1.000 (7/7) | 0.929 |
| hybrid | 1.000 (7/7) | 0.821 |

Interpretação: a infraestrutura 0.5.9 não alterou os resultados anteriores e o perfil `dense-rerank` manteve o maior MRR tanto no desenvolvimento quanto no primeiro holdout congelado.

Limitação importante: a métrica atual usa a primeira fonte esperada e não diferencia relevância preferencial entre várias fontes plausíveis. Em especial, consultas de gestação podem promover documentos CHATSCM ou cadernetas antes de calendários oficiais, mesmo quando todas são semanticamente relacionadas.


## 0.5.10 — métricas source-level complementares

A 0.5.10 não altera o retrieval nem o dataset. Ela mantém as métricas históricas e adiciona:

- `SourceRecall@k`: fração das fontes esperadas distintas que aparecem entre os k resultados;
- `SourceNDCG@k`: qualidade da ordenação das fontes esperadas, contando uma mesma fonte apenas uma vez como relevante;
- `unique_sources` por caso: quantidade de fontes distintas nos k resultados.

HitRate@k e MRR@k continuam sendo calculados com a semântica histórica para que os resultados anteriores permaneçam comparáveis.

Essa fase deve ser validada primeiro sobre `holdout` e `dev` sem alterar parâmetros de retrieval e sem reindexar o corpus.


### Resultado verificado da 0.5.10

As métricas históricas foram reproduzidas e as novas métricas source-level foram calculadas com sucesso.

Holdout (15 casos):

| Modo | HitRate@5 | MRR@5 | SourceRecall@5 | SourceNDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| dense | 1.000 | 0.889 | 1.000 | 0.917 |
| dense-rerank | 1.000 | 0.933 | 1.000 | 0.941 |
| hybrid | 1.000 | 0.878 | 0.967 | 0.885 |

Suite dev (7 casos):

| Modo | HitRate@5 | MRR@5 | SourceRecall@5 | SourceNDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| dense | 1.000 | 0.857 | 1.000 | 0.903 |
| dense-rerank | 1.000 | 0.929 | 1.000 | 0.936 |
| hybrid | 1.000 | 0.821 | 1.000 | 0.869 |

A nova métrica revelou algo que HitRate não mostrava: no holdout, o modo hybrid continuou com HitRate@5=1.000, mas SourceRecall@5 caiu para 0.967 porque, em `holdout-vacinas-gestante-parafrase`, apenas uma das duas fontes esperadas apareceu no top 5.

O perfil `dense-rerank` manteve o maior SourceNDCG tanto no holdout quanto na suite dev, reforçando a decisão de mantê-lo como padrão.

Os testes unitários adicionados para as funções de métricas ainda não foram executados em CI/container de desenvolvimento; a validação atual é de runtime pelo avaliador.


## 0.5.18 — semântica explícita dos rótulos

A auditoria do dataset congelado `2026-09-20-v1` confirmou:

- 22 casos legados;
- 5 casos com múltiplas `expected_sources`;
- 0 casos com semântica explícita.

Isso preserva a interpretação histórica: os resultados de `HitRate`, `MRR`, `SourceRecall` e `SourceNDCG` continuam válidos como métricas calculadas pelo contrato antigo, mas as cinco listas multi-source não devem ser descritas como julgamentos manuais completos de relevância.

Para datasets novos, o contrato passa a ser:

    acceptable_sources -> alternativas OR
    required_sources   -> cobertura AND

Métricas explícitas:

- `PassRate@k`: caso satisfaz todas as condições declaradas;
- `MRR@k`: posição da primeira fonte relevante declarada;
- `AcceptableHitRate@k`: pelo menos uma alternativa aceitável recuperada;
- `RequiredRecall@k`: fração das fontes obrigatórias recuperadas;
- `RequiredNDCG@k`: ordenação das fontes obrigatórias recuperadas.

O arquivo `docs/evaluation-v2-template.json` é apenas um template de esquema, não um dataset rotulado nem um holdout.
