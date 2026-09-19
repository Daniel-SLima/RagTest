# Dificuldades TCC

Registro de situações em que uma hipótese, configuração ou decisão planejada não funcionou como esperado na primeira tentativa.

## 1. Filtro de categoria reduziu a qualidade da recuperação

Planejado: restringir a busca a category=vacinacao.

Observado: o filtro excluiu a Caderneta da Pessoa Idosa e piorou os resultados.

Diagnóstico: categoria documental e público-alvo são dimensões diferentes.

Correção: inclusão de audience e filtros por público.

Aprendizado: metadados de domínio influenciam diretamente a precisão do retrieval.

## 2. Limite de saída do Gemini interrompeu a primeira resposta

Planejado: gerar a resposta após recuperar os melhores chunks.

Observado: a primeira resposta terminou após uma frase introdutória.

Diagnóstico: a geração atingiu o limite de tokens.

Correção: aumento do orçamento e retry automático em MAX_TOKENS.

Aprendizado: um RAG pode recuperar corretamente e ainda falhar na etapa de geração.

## 3. Avaliação do retrieval falhou dentro do container

Planejado: executar ragtest-evaluate-retrieval no container.

Observado: FileNotFoundError para tests/evaluation/retrieval_cases.json.

Diagnóstico: o runtime dependia de um arquivo excluído da imagem Docker.

Correção: casos padrão empacotados em app/evaluation/cases.py.

Aprendizado: recursos de runtime não devem depender acidentalmente da estrutura de testes.

## 4. Busca densa não recuperou a carta de direitos e deveres no top 5

Planejado: recuperar direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf.

Observado: na baseline 0.5.1 o documento não apareceu no top 5.

Diagnóstico inicial: similaridade vetorial densa poderia estar perdendo correspondências lexicais explícitas.

Correção experimental: reranking por metadados e conteúdo.

Aprendizado: a causa de uma falha de retrieval precisa ser isolada antes de aumentar a complexidade do ranking.

## 5. Reranking melhorou o MRR, mas não resolveu a falha de recall

Planejado: o reranking lexical 0.5.2 deveria promover a carta de direitos e deveres.

Observado: HitRate@5 ficou em 0.857; MRR@5 subiu para 0.786; a fonte esperada continuou ausente.

Diagnóstico: reranking só reorganiza candidatos já recuperados.

Correção experimental: retrieval híbrido dense + BM25 com RRF.

Aprendizado: ranking e recall são problemas distintos.

## 6. Retrieval híbrido inicial piorou as métricas

Planejado: dense + BM25 deveria aumentar o recall sem perder os casos já corretos.

Observado: a 0.5.3 caiu para HitRate@5=0.714 e MRR@5=0.607.

Diagnóstico: o BM25 não usava metadados e o corte relativo 0.22 foi aplicado em uma nova escala de score.

Correção experimental: enriquecer BM25 com metadados, neutralizar pesos e retirar o corte relativo.

Aprendizado: parâmetros de score não são transferíveis automaticamente entre estratégias.

## 7. BM25 enriquecido recuperou a baseline, mas não a fonte problemática

Planejado: a 0.5.4 deveria aumentar o recall lexical da carta de direitos/deveres por meio de source e filename.

Observado: HitRate@5 voltou a 0.857, mas MRR@5 caiu para 0.690 e a fonte esperada continuou ausente.

Diagnóstico: como nem o BM25 enriquecido com o próprio nome do arquivo trouxe a fonte, a investigação precisa voltar uma etapa. A hipótese a verificar é se esse PDF realmente produz texto extraível e chunks indexáveis.

Correção em investigação: adicionar auditoria de cobertura do corpus antes de qualquer novo ajuste de retrieval.

Aprendizado: quando várias estratégias de ranking falham para a mesma fonte, é necessário validar a qualidade de ingestão antes de continuar calibrando o mecanismo de busca.

## Como registrar novos casos

Registrar sempre: planejado, observado, diagnóstico, correção e aprendizado para a monografia.
