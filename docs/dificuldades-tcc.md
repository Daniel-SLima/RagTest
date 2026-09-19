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

Diagnóstico: similaridade vetorial densa pode perder correspondências lexicais explícitas.

Correção experimental: reranking por metadados e conteúdo.

Aprendizado: retrieval puramente denso pode falhar em consultas com terminologia exata.

## 5. Reranking melhorou o MRR, mas não resolveu a falha de recall

Planejado: o reranking lexical 0.5.2 deveria promover a carta de direitos e deveres.

Observado: HitRate@5 ficou em 0.857; MRR@5 subiu de 0.714 para 0.786; a fonte esperada continuou ausente.

Diagnóstico: reranking só reorganiza candidatos já recuperados.

Correção experimental: retrieval híbrido dense + BM25 com RRF.

Aprendizado: ranking e recall são problemas distintos.

## 6. Retrieval híbrido inicial piorou as métricas

Planejado: dense + BM25 deveria aumentar o recall sem perder os casos já corretos.

Observado: a 0.5.3 caiu para HitRate@5=0.714 e MRR@5=0.607. A vacinação na gestação passou a falhar e a carta de direitos/deveres continuou ausente.

Diagnóstico: o BM25 indexava apenas o texto dos chunks, portanto o nome do arquivo não ajudava o recall. Além disso, o corte relativo 0.22, calibrado para score cosseno, foi aplicado após RRF, cuja escala é diferente. Isso eliminou candidatos úteis.

Correção experimental: enriquecer o texto esparso com metadados, equilibrar pesos dense/sparse em 1.0/1.0 e desativar o corte relativo no modo híbrido.

Aprendizado: parâmetros de score não são transferíveis automaticamente entre estratégias de recuperação. Uma mudança de função de ranking exige nova calibração e nova medição.

## Como registrar novos casos

Registrar sempre: planejado, observado, diagnóstico, correção e aprendizado para a monografia.
