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

## 10. pyproject inválido bloqueou o build Docker da 0.5.11

Planejado: adicionar o comando `ragtest-check-grounding` ao bloco `[project.scripts]` e reconstruir a imagem Docker da versão 0.5.11.

Observado: o build falhou em `RUN pip install --no-cache-dir .` com `TOMLDecodeError: Expected newline or end of document after a statement (at line 41, column 63)`.

Diagnóstico: o `pyproject.toml` continha os dois scripts na mesma linha com os caracteres literais `\n` entre eles, em vez de uma quebra de linha TOML real.

Correção: separar `ragtest-evaluate-retrieval` e `ragtest-check-grounding` em duas linhas válidas dentro de `[project.scripts]`. A correção foi validada em runtime: o build Docker concluiu, a API 0.5.11 subiu e o self-check de groundedness passou.

Aprendizado técnico: alterações automatizadas em arquivos declarativos devem preservar a sintaxe do formato e ser validadas antes de considerar a imagem pronta para build.

## 11. Consulta composta recuperou direitos, mas não detalhou deveres

Planejado: responder à pergunta composta "Quais são os direitos e deveres da pessoa usuária da saúde?" usando três fontes recuperadas da categoria `direitos_saude`.

Observado: a resposta real passou pela validação de citações, apresentou vários direitos com fontes válidas, mas informou que o contexto recuperado não era suficiente para detalhar os deveres. Os três resultados retornados eram páginas 10, 4 e 27 da mesma Carta.

Diagnóstico: o guardrail de groundedness funcionou corretamente ao não inventar deveres ausentes do contexto. A busca isolada por deveres recuperou a página 13 da Carta em rank 1, confirmando que os trechos estão extraídos, indexados e recuperáveis. Na consulta composta, a mesma página não apareceu no top 5 e só surgiu em rank 10. Portanto, o problema não é ausência no corpus nem apenas um corte top 3: a subintenção "deveres" é fortemente diluída quando combinada com "direitos".

Correção: não aumentar simplesmente o contexto global para 10 resultados, pois isso elevaria custo e ruído para todas as perguntas. Levar o caso para uma fase própria de decomposição/multi-query, preservando o `dense-rerank` como retrieval base para cada subconsulta.

Aprendizado técnico: uma resposta pode ter citações válidas e ainda ser incompleta quando o retrieval não cobre todas as subintenções de uma pergunta composta; validação de citações e cobertura semântica são dimensões distintas.

## 12. RRF reforçou a intenção dominante quando a pergunta original foi fundida com as subconsultas

Planejado: executar a pergunta original junto com as subconsultas de direitos e deveres e usar RRF para trazer a página 13 de deveres de volta ao top 5.

Observado: o self-check da fusão passou, mas no experimento real a página 13 continuou fora do top 5. A consulta original e a subconsulta de direitos retornaram praticamente o mesmo ranking, enquanto a página 13 apareceu apenas na subconsulta de deveres.

Diagnóstico: o RRF somou votos de rankings redundantes. Como a pergunta original e a subconsulta de direitos reforçaram as mesmas páginas, a intenção dominante recebeu peso duplicado e superou resultados exclusivos da subintenção de deveres. O problema não era a implementação matemática do RRF, mas a composição das consultas usadas na fusão.

Correção: quando subconsultas explícitas existirem, fundir apenas as subconsultas por padrão. A pergunta original permanece disponível como referência e pode ser incluída com `--include-original` somente para diagnóstico. A correção foi validada em runtime: a página 13 de deveres, que estava fora do top 5 na primeira fusão, passou para rank 2 no resultado final.

Aprendizado técnico: técnicas de fusão como RRF pressupõem diversidade útil entre os rankings; consultas semanticamente redundantes podem amplificar a intenção dominante e reduzir a cobertura de subintenções minoritárias.

## 13. CI bloqueava o pytest por falhas de lint

Planejado: usar o workflow de CI como gate automático para lint e testes em pushes e Pull Requests.

Observado: após o merge da 0.5.13, o job instalou o projeto com sucesso, mas `ruff check .` falhou com 8 violações e a etapa `pytest` foi marcada como skipped. O mesmo padrão já ocorria em execuções anteriores.

Diagnóstico: havia dívida de lint acumulada em imports, ordenação de `__all__` e dois `except Exception` intencionais sem anotação explícita. Além disso, lint e testes estavam no mesmo job sequencial, então uma falha de estilo impedia qualquer execução da suíte. A versão do Ruff também era definida por faixa ampla, tornando o conjunto efetivo de regras dependente da versão instalada no momento.

Correção: corrigir as 8 violações atuais; documentar com `noqa: BLE001` apenas os dois catches amplos que são deliberadamente resilientes; fixar Ruff em 0.16.8 e declarar explicitamente as regras do gate; separar `lint` e `test` em jobs independentes; ignorar alterações exclusivamente documentais para evitar execuções desnecessárias.

Aprendizado técnico: um gate de qualidade deve tornar lint e testes independentes e reproduzíveis; caso contrário, uma falha de estilo pode ocultar regressões funcionais e upgrades silenciosos de ferramentas podem alterar o comportamento da CI.

## 14. Teste de health tinha versão inicial hardcoded

Planejado: após liberar o pytest na CI, executar toda a suíte e usar o resultado como gate funcional da 0.5.14.

Observado: o job de lint passou, e o pytest finalmente executou: 50 testes passaram e 1 falhou. A falha foi `tests/test_health.py::test_health_returns_api_status`, que ainda esperava `"0.1.0"` enquanto a aplicação retornava corretamente `"0.5.14"`.

Diagnóstico: o teste de health carregava uma versão fixa da fase inicial do projeto. Como a suíte vinha sendo bloqueada anteriormente pelo lint, essa expectativa obsoleta permaneceu sem ser detectada.

Correção: fazer o teste comparar a versão retornada com `get_settings().app_version`, validando que o endpoint reflete a configuração corrente sem exigir edição manual do teste a cada release.

Aprendizado técnico: testes de contratos que incluem metadados evolutivos devem validar a fonte de configuração correspondente, e não duplicar valores que mudam a cada versão.

## Como registrar novos casos

Usar sempre exatamente estes campos:

Planejado:

Observado:

Diagnóstico:

Correção:

Aprendizado técnico:
