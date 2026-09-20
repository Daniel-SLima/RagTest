# Dificuldades TCC

Registro de situações em que uma hipótese, configuração ou decisão planejada não funcionou como esperado na primeira tentativa.

## 1. Filtro de categoria reduziu a qualidade da recuperação

Planejado: restringir a busca a category=vacinacao.

Observado: o filtro excluiu a Caderneta da Pessoa Idosa e piorou os resultados.

Diagnóstico: categoria documental e público-alvo são dimensões diferentes.

Correção: inclusão de audience e filtros por público.

Aprendizado técnico: metadados de domínio influenciam diretamente a precisão do retrieval.

## 2. Limite de saída do Gemini interrompeu a primeira resposta

Planejado: gerar a resposta após recuperar os melhores chunks.

Observado: a primeira resposta terminou após uma frase introdutória.

Diagnóstico: a geração atingiu o limite de tokens.

Correção: aumento do orçamento e retry automático em MAX_TOKENS.

Aprendizado técnico: um RAG pode recuperar corretamente e ainda falhar na etapa de geração.

## 3. Avaliação do retrieval falhou dentro do container

Planejado: executar ragtest-evaluate-retrieval no container.

Observado: FileNotFoundError para tests/evaluation/retrieval_cases.json.

Diagnóstico: o runtime dependia de um arquivo excluído da imagem Docker.

Correção: casos padrão empacotados em app/evaluation/cases.py.

Aprendizado técnico: recursos de runtime não devem depender acidentalmente da estrutura de testes.

## 4. Busca densa não recuperou a carta de direitos e deveres no top 5

Planejado: recuperar direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf.

Observado: a fonte não apareceu.

Diagnóstico: inicialmente a falha parecia estar no retrieval denso; experimentos posteriores mostraram que a investigação precisava incluir a cobertura do corpus.

Correção: foram testados reranking e busca híbrida e, depois, a cobertura da fonte foi auditada diretamente.

Aprendizado técnico: a causa de uma falha de retrieval precisa ser isolada antes de aumentar a complexidade do ranking.

## 5. Reranking melhorou o MRR, mas não resolveu a falha de recall

Planejado: o reranking lexical deveria promover a carta.

Observado: MRR melhorou, mas a fonte continuou ausente.

Diagnóstico: reranking só reorganiza candidatos já recuperados.

Correção: a investigação saiu do reranking isolado e passou a testar geração de candidatos com BM25/retrieval híbrido.

Aprendizado técnico: ranking e recall de candidatos são problemas distintos.

## 6. Retrieval híbrido inicial piorou as métricas

Planejado: dense + BM25 deveria aumentar o recall.

Observado: HitRate@5 caiu para 0.714 e MRR@5 para 0.607.

Diagnóstico: BM25 sem metadados e threshold reaproveitado em uma escala de score diferente prejudicaram a combinação inicial.

Correção: o texto esparso foi enriquecido com metadados, os pesos foram reequilibrados e o score margin legado foi removido da configuração híbrida.

Aprendizado técnico: parâmetros de score não são transferíveis automaticamente entre estratégias de retrieval.

## 7. BM25 enriquecido recuperou a baseline, mas não a fonte problemática

Planejado: source e filename no BM25 deveriam recuperar a carta.

Observado: HitRate@5 voltou a 0.857, mas a carta continuou ausente.

Diagnóstico: sucessivas alterações de retrieval não resolviam a mesma fonte, indicando que o problema poderia estar antes do ranking.

Correção: o ajuste de ranking foi interrompido e foi criada uma auditoria de cobertura por documento/chunks.

Aprendizado técnico: quando várias estratégias falham para a mesma fonte, a cobertura do corpus deve ser auditada antes de novos ajustes de ranking.

## 8. A fonte esperada tinha zero texto e zero chunks

Planejado: usar a carta de direitos e deveres como fonte esperada na avaliação do retrieval.

Observado: a auditoria 0.5.5 mostrou 28 páginas, 0 páginas com texto extraído, 0 caracteres e 0 chunks.

Diagnóstico: o extrator PyPDF retornou texto vazio para todas as 28 páginas; portanto a fonte não gerava chunks e não participava do índice. Isso, por si só, não identifica de forma definitiva a construção interna do PDF.

Correção: OCR seletivo local com Tesseract nas páginas sem texto, mantendo a extração normal quando ela funciona.

Aprendizado técnico: métricas de retrieval só são interpretáveis se as fontes esperadas realmente estiverem presentes no índice; a cobertura do corpus deve ser validada antes de atribuir uma falha ao ranking.

## 9. Retrieval híbrido não superou o dense-rerank no mesmo corpus

Planejado: comparar dense, dense-rerank e hybrid no mesmo corpus pós-OCR para verificar se a busca híbrida traria vantagem mensurável quando a cobertura do índice fosse mantida constante.

Observado: os três modos obtiveram HitRate@5=1.000, mas os MRR@5 foram diferentes: dense=0.857, dense-rerank=0.929 e hybrid=0.821. O modo hybrid colocou a fonte esperada de implante contraceptivo no rank 4, enquanto dense-rerank a manteve no rank 2.

Diagnóstico: neste conjunto pequeno de consultas, o BM25 + RRF não trouxe ganho de recall porque todos os modos já encontraram as fontes esperadas. A fusão lexical alterou a ordenação e, em alguns casos, favoreceu documentos semanticamente relacionados porém menos alinhados à fonte esperada.

Correção: dense-rerank passou a ser o candidato padrão, mantendo hybrid disponível para comparação; depois a decisão foi validada em uma suite holdout congelada.

Aprendizado técnico: adicionar uma técnica mais complexa não garante melhor qualidade; a escolha da estratégia deve ser sustentada por benchmark controlado e replicável.

## Como registrar novos casos

Usar sempre exatamente estes campos:

Planejado:

Observado:

Diagnóstico:

Correção:

Aprendizado técnico:
