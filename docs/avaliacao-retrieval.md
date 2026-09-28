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


### Validação da infraestrutura v2

O self-check determinístico passou em todos os cenários:

    [PASS] OR alternative passes with one acceptable source
    [PASS] OR alternative does not require every acceptable source
    [PASS] AND required fails with incomplete coverage
    [PASS] AND required exposes partial recall
    [PASS] AND required passes with complete coverage
    [PASS] combined case requires acceptable and required conditions
    [PASS] explicit dataset mode is detected

A regressão do caminho legado também foi executada sobre a suite dev com `dense-rerank` e reproduziu exatamente a baseline:

    HitRate@5: 1.000 (7/7)
    MRR@5: 0.929
    SourceRecall@5: 1.000
    SourceNDCG@5: 0.936

CI final da 0.5.18:

    ruff: All checks passed!
    pytest: 72 passed, 4 warnings

Conclusão: o avaliador v2 pode expressar semântica OR/AND sem alterar o contrato histórico do dataset v1.


## Dataset de domínio v2 (2026-09-28)

Foco na proposta do orientador: rastreamento (preventivo/mamografia), agendamento, gestação e
urgência. Perguntas escritas em linguagem de usuária (informal, com erros comuns), sem copiar o
texto das fontes. Rótulos explícitos (`acceptable_sources`: qualquer uma das fontes no top-k conta).

| Arquivo | Casos | Uso |
|---|---|---|
| `app/evaluation/datasets/dominio-v2-dev.json` | 15 | pode ser usado para ajustes |
| `app/evaluation/datasets/dominio-v2-holdout.json` | 25 | **congelado**: rodar uma vez por configuração final, não ajustar em cima dele |
| `app/evaluation/datasets/dominio-v2-fora-escopo.json` | 4 | comportamento esperado `recusar`; usado na Fase 3 (não serve para o avaliador de retrieval) |

Execução (depois de sincronizar o Qdrant com o catálogo de serviços):

    ragtest-evaluate-retrieval --cases app/evaluation/datasets/dominio-v2-dev.json --mode all
    ragtest-evaluate-retrieval --cases app/evaluation/datasets/dominio-v2-holdout.json --mode all

### Primeira execução — 2026-09-28 (`docs/resultados/avaliacao_2026-09-28_1454.txt`)

Corpus: 773 chunks (767 anteriores + 6 do catálogo de serviços). k=5. Rótulo: `acceptable_sources`.

| Modo | Dev PassRate | Dev MRR | Holdout PassRate | Holdout MRR |
|---|---|---|---|---|
| dense | 0.600 (9/15) | 0.533 | 0.760 (19/25) | 0.680 |
| dense-rerank | 0.600 (9/15) | 0.567 | 0.840 (21/25) | 0.770 |
| **hybrid** | **1.000 (15/15)** | **0.833** | **0.920 (23/25)** | **0.853** |

Leitura:

- No domínio (linguagem coloquial, FAQ do CHATSCM, catálogo), o **hybrid** (denso + BM25 com RRF)
  supera os demais nas duas suítes. No corpus genérico anterior (vacinas, DIU, insulina) o
  `dense-rerank` tinha vencido (D006); a diferença é que perguntas de usuária usam termos exatos
  ("preventivo", "implanon", "mamografia") que o BM25 captura e o modelo denso multilíngue pequeno não.
- Falhas do dense/dense-rerank no dev: agendamento do preventivo, resultado do preventivo, "descobri
  que tô grávida", preventivo na gestação, caroço na mama, DIU — todas respondidas pelo CHATSCM.
- Falhas do hybrid no holdout: "de quanto em quanto tempo repito o preventivo" e "o que evitar antes
  do preventivo". As duas dependem só do catálogo. A inspeção mostrou que o serviço `preventivo`
  virava 2 chunks e o segundo (documentos/preparo) não continha o nome do serviço.

Ações tomadas (D046 e D047): `hybrid` virou o modo padrão; cada chunk do catálogo passa a levar o
cabeçalho `Serviço: <nome>`.

**Atenção metodológica:** a correção do cabeçalho foi motivada por falhas do holdout. Uma nova
execução do holdout v2 **não é mais independente** para essa mudança; o dev continua válido e um
holdout v3 com perguntas novas deve ser congelado antes da próxima rodada.

### Segunda execução — 2026-09-28 (`docs/resultados/avaliacao_2026-09-28_1503.txt`)

Após D047 (contexto do serviço nos chunks do catálogo), 773 chunks, sync com 2 inserções e 2 remoções.

| Modo | Dev PassRate | Dev MRR | Holdout PassRate* | Holdout MRR* |
|---|---|---|---|---|
| dense | 0.600 | 0.533 | 0.760 | 0.660 |
| dense-rerank | 0.600 | 0.567 | 0.840 | 0.750 |
| **hybrid** | **1.000** | **0.833** | **0.960 (24/25)** | **0.861** |

\* Holdout não independente para a D047 (ver nota acima). Falha restante do hybrid: "de quanto em
quanto tempo repito o preventivo se deu normal" (o chunk da periodicidade não aparece no top 5).

### Teste do chat com provider real — 2026-09-28 (`docs/resultados/teste_chat.json`, Groq GPT-OSS 120B)

| Pergunta | Resultado |
|---|---|
| Como eu agendo a mamografia? | ❌ `grounded=false` após repair (fontes corretas: CHATSCM + catálogo). Causa em investigação — dificuldade #36 |
| Com quantos anos faço o preventivo? | ✅ grounded, cita o catálogo, ações do preventivo com `due_date` |
| estou grávida e sangrando | ✅ triagem determinística, sem LLM, ação 192 |
| quem ganhou o jogo do bahia? | ❌ recusa com citação falsa `[1]` marcada como verificada → corrigido pela D048 |

O arquivo aparece com acentos corrompidos porque o PowerShell 5.1 decodificava a resposta sem
charset como Latin-1; corrigido pela D049.

### Calibração de fora de escopo (dev × fora de escopo)

Menor score top-1 do domínio: 0.3527 (bolsa estourou). Maior fora de escopo: 0.6233 ("melhor plano
de saúde particular"). **Sem separação limpa** (8 perguntas do domínio abaixo de 0.6233).
Decisão: `RETRIEVAL_MIN_SCORE` continua desligado; recusa por limiar de similaridade densa não é
viável neste corpus (ver D041). Alternativa futura: classificador de domínio leve ou regra de palavras-chave.
