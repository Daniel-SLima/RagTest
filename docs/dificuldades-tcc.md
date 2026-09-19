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

Observado: a fonte não apareceu.

Diagnóstico inicial: poderia ser uma limitação do retrieval denso.

Correção experimental: reranking e depois busca híbrida.

Aprendizado: a causa de uma falha de retrieval precisa ser isolada antes de aumentar a complexidade.

## 5. Reranking melhorou o MRR, mas não resolveu a falha de recall

Planejado: o reranking lexical deveria promover a carta.

Observado: MRR melhorou, mas a fonte continuou ausente.

Diagnóstico: reranking só reorganiza candidatos já recuperados.

Aprendizado: ranking e recall são problemas distintos.

## 6. Retrieval híbrido inicial piorou as métricas

Planejado: dense + BM25 deveria aumentar o recall.

Observado: HitRate@5 caiu para 0.714 e MRR@5 para 0.607.

Diagnóstico: BM25 sem metadados e threshold reaproveitado em uma escala de score diferente.

Aprendizado: parâmetros de score não são transferíveis automaticamente entre estratégias.

## 7. BM25 enriquecido recuperou a baseline, mas não a fonte problemática

Planejado: source e filename no BM25 deveriam recuperar a carta.

Observado: HitRate@5 voltou a 0.857, mas a carta continuou ausente.

Diagnóstico: a investigação precisou retornar à etapa de ingestão.

Aprendizado: quando várias estratégias falham para a mesma fonte, a cobertura do corpus deve ser auditada.

## 8. A fonte esperada tinha zero texto e zero chunks

Planejado: usar a carta de direitos e deveres como fonte esperada na avaliação do retrieval.

Observado: a auditoria 0.5.5 mostrou 28 páginas, 0 páginas com texto extraído, 0 caracteres e 0 chunks.

Diagnóstico: o PDF não possui uma camada de texto utilizável pelo extrator atual; portanto ele nunca participou do índice vetorial ou esparso. A falha observada nas versões anteriores não poderia ser corrigida apenas por ranking.

Correção: OCR seletivo local com Tesseract nas páginas sem texto, mantendo a extração normal quando ela funciona.

Aprendizado: métricas de retrieval só são interpretáveis se as fontes esperadas realmente estiverem presentes no índice. A validação do corpus deve anteceder a avaliação do mecanismo de recuperação.

## Como registrar novos casos

Registrar sempre: planejado, observado, diagnóstico, correção e aprendizado para a monografia.
