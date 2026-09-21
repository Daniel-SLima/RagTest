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

Correção: corrigir as 8 violações atuais; documentar com `noqa: BLE001` apenas os dois catches amplos que são deliberadamente resilientes; fixar Ruff em 0.16.8 e declarar explicitamente as regras do gate; separar `lint` e `test` em jobs independentes; ignorar alterações exclusivamente documentais para evitar execuções desnecessárias. A correção foi validada no GitHub Actions: `ruff check .` retornou `All checks passed!` e o job de testes passou independentemente.

Aprendizado técnico: um gate de qualidade deve tornar lint e testes independentes e reproduzíveis; caso contrário, uma falha de estilo pode ocultar regressões funcionais e upgrades silenciosos de ferramentas podem alterar o comportamento da CI.

## 14. Teste de health tinha versão inicial hardcoded

Planejado: após liberar o pytest na CI, executar toda a suíte e usar o resultado como gate funcional da 0.5.14.

Observado: o job de lint passou, e o pytest finalmente executou: 50 testes passaram e 1 falhou. A falha foi `tests/test_health.py::test_health_returns_api_status`, que ainda esperava `"0.1.0"` enquanto a aplicação retornava corretamente `"0.5.14"`.

Diagnóstico: o teste de health carregava uma versão fixa da fase inicial do projeto. Como a suíte vinha sendo bloqueada anteriormente pelo lint, essa expectativa obsoleta permaneceu sem ser detectada.

Correção: fazer o teste comparar a versão retornada com `get_settings().app_version`, validando que o endpoint reflete a configuração corrente sem exigir edição manual do teste a cada release. A correção foi validada no rerun da CI: a suíte terminou com 51 testes aprovados e 4 warnings não bloqueantes.

Aprendizado técnico: testes de contratos que incluem metadados evolutivos devem validar a fonte de configuração correspondente, e não duplicar valores que mudam a cada versão.

## 15. Gemini ficou indisponível por alta demanda no teste real do gate de grounding

Planejado: validar o novo gate de cobertura de citações em uma pergunta real restrita à categoria oficial `direitos_saude`.

Observado: os self-checks determinísticos de grounding e cobertura passaram, mas a chamada real ao Gemini inicialmente terminou antes da validação do gate com `503 UNAVAILABLE`. Em retestes posteriores o Gemini voltou a responder após retry, porém novas execuções retornaram `429` em todas as três tentativas (chamada inicial + 2 retries), terminando em `LLMServiceUnavailableError`. Isso confirma que a disponibilidade externa continua oscilando entre indisponibilidade de capacidade e limite/cota.

Diagnóstico: retrieval e validação estrutural não chegaram a falhar; a exceção ocorreu na dependência externa de geração. O SDK já executa sua política interna de retry, mas ainda propagou o 503 após esgotá-la. O provider do RagTest não possuía uma política de resiliência de aplicação nem convertia indisponibilidade transitória em erro de domínio amigável.

Correção: adicionar retries de aplicação limitados para códigos transitórios 429/500/502/503/504, com backoff exponencial curto e configurável. Após esgotar os retries, converter a falha em `LLMServiceUnavailableError`; o endpoint responde HTTP 503 e o CLI encerra com mensagem curta em vez de traceback completo. Erros não transitórios continuam sem retry.

Aprendizado técnico: mesmo quando retrieval e grounding estão corretos, um RAG depende da disponibilidade do provedor de geração. Resiliência de produção exige distinguir erros transitórios de erros permanentes e limitar retries para evitar loops, latência imprevisível e tempestades de requisições.

## 16. Qwen3 4B expôs reasoning mesmo com thinking desativado

Planejado: usar `qwen3:4b` local no Ollama com `think=false` para gerar somente a resposta final do RAG.

Observado: tanto no CLI quanto na API, o modelo incluiu o raciocínio interno no conteúdo textual e terminou o bloco com `</think>`, apesar de `think=false` e do teste adicional com `/no_think`.

Diagnóstico: na combinação local validada de Ollama 0.34.2 + `qwen3:4b`, a desativação de thinking não produziu o contrato de saída necessário ao gate estrutural do RagTest. Esse conteúdo extra poderia ser interpretado como blocos informativos sem citação.

Correção: testar `qwen3:8b` no mesmo ambiente. O 8B respeitou `think=false` tanto no CLI quanto na API. O modelo foi validado com contexto 8192 e acesso a partir do container Docker; o provider local passa a usar `qwen3:8b` como padrão e rejeita explicitamente vazamento de `</think>` quando thinking está desativado.

Aprendizado técnico: modelos da mesma família podem apresentar contratos de saída diferentes no mesmo runtime. Antes de integrar um LLM a guardrails estruturais, é necessário validar o payload real da API e não apenas a capacidade declarada do modelo.


## 17. Qwen3 8B local ficou lento e falhou no gate de citações no primeiro chat RAG real

Planejado: validar o `OllamaProvider` com `qwen3:8b` na pergunta oficial "Quais são os direitos da pessoa usuária da saúde?", usando `dense-rerank`, `--category direitos_saude` e `--no-decompose`, preservando corpus, Qdrant e retrieval.

Observado: `/health` retornou 0.5.19; `ragtest-runtime-info --skip-qdrant` confirmou `LLM_PROVIDER=ollama`, `qwen3:8b`, contexto 8192 e `think=false`; os self-checks de grounding e cobertura passaram. No chat real com `LLM_MAX_OUTPUT_TOKENS=4096`, o retrieval retornou cinco páginas da fonte oficial, mas a execução levou aproximadamente seis minutos, realizou um retry de citação (`citation_retry_count=1`) e terminou em fallback seguro com `grounded=false` e sem `citation_ids`. Um segundo teste, alterando somente `LLM_MAX_OUTPUT_TOKENS` para 512, preservou o mesmo retrieval e a mesma falha do gate, mas reduziu o tempo total para 158,5 s.

Diagnóstico: o retrieval não é o ponto de falha observado, porque os cinco resultados foram recuperados normalmente e os validadores determinísticos passaram. Um teste isolado do `qwen3:8b` com `think=false`, contexto 8192 e `num_predict=512` respondeu 254 tokens em 28,68 s de parede, com `prompt_eval_duration` de aproximadamente 0,21 s e `eval_duration` de aproximadamente 28,42 s, equivalente a 8,94 tokens/s. Isso mostra que, no teste curto, a maior parte do tempo ficou na geração de saída e não no carregamento ou avaliação do prompt. O fluxo RAG executou uma geração inicial e, após falha do gate, uma segunda geração completa; com `LLM_MAX_OUTPUT_TOKENS=4096`, duas saídas longas nessa taxa são uma explicação plausível para vários minutos, mas o número real de tokens das duas chamadas RAG ainda não foi observado. O `OllamaProvider` atual descarta metadados de execução retornados pelo Ollama e o fallback não preserva as respostas rejeitadas para diagnóstico; portanto, ainda não sabemos se a reprovação ocorreu por ausência de citações, cobertura incompleta, formato da resposta ou outra característica da geração.

Correção: o teste controlado com 512 confirmou que reduzir o orçamento de saída reduz substancialmente a latência, mas não resolve a falha de grounding. Foi adicionada instrumentação sem alterar o comportamento: o `OllamaProvider` agora preserva métricas de cada geração (`total_duration`, `load_duration`, tokens e duração de prompt/saída, taxa de geração e `done_reason`), e o CLI mostra também validade, sintaxe, cobertura e motivo de cada tentativa do gate. A CI dessa instrumentação passou com Ruff verde e `92 passed, 4 warnings`. A validação real com Qwen permanece pendente.

Aprendizado técnico: self-checks do gate validam a lógica determinística do RagTest, mas não validam automaticamente a aderência de um modelo local ao contrato de saída nem sua latência sob o prompt RAG real. Providers locais precisam expor métricas de geração e motivos de reprovação para que desempenho e groundedness sejam diagnosticados separadamente.


## 18. O mesmo gate de grounding falhou com Gemini após recuperação de um 503

Planejado: verificar se o Gemini 3.6 Flash havia voltado a responder no mesmo cenário oficial de `direitos_saude`, mantendo a pergunta, retrieval, corpus e `--no-decompose`.

Observado: a primeira tentativa ao Gemini recebeu erro transitório 503; o retry de aplicação foi acionado após 1 segundo e a execução conseguiu prosseguir. O retrieval retornou as mesmas cinco páginas da Carta oficial, porém o chat terminou com `grounded=false`, sem `citation_ids` e com `citation_retry_count=1`, exatamente como no teste anterior com Qwen3 8B.

Diagnóstico: o Gemini voltou a estar acessível, mas ainda apresentou indisponibilidade transitória. Como dois providers diferentes chegaram ao mesmo fallback estrutural sobre o mesmo contexto recuperado, a hipótese de que a reprovação seja específica do Qwen ficou enfraquecida. A causa exata do gate ainda não está identificada porque esse teste usou uma imagem anterior à instrumentação que expõe validade, sintaxe, cobertura e motivo por tentativa.

Correção: nenhuma mudança funcional ainda. Atualizar/rebuildar a imagem com a instrumentação já implementada e repetir o mesmo teste com Gemini para observar o motivo preciso da reprovação antes de alterar prompt ou regras do gate. O Gemini pode voltar a ser usado como provider principal de desenvolvimento, mantendo o Ollama como contingência manual enquanto a disponibilidade externa oscilar.

Aprendizado técnico: disponibilidade do provider e groundedness são dimensões independentes. Um retry pode recuperar uma falha 503 e ainda assim a resposta subsequente ser rejeitada pelo gate; além disso, quando o mesmo comportamento aparece em providers diferentes, a investigação deve priorizar o contrato compartilhado de prompt/validação antes de atribuir o problema ao modelo.


## 19. Gate estrutural tratava heading Markdown como afirmação e retry regenerava do zero

Planejado: usar o gate de cobertura da 0.5.19 para exigir citação em cada parágrafo ou item informativo e, em caso de falha, reparar a resposta uma única vez.

Observado: no teste real com Gemini, a primeira resposta teve sintaxe de citações válida, mas cobertura de 0,786 (22/28 blocos); o retry caiu para 0,767 (23/30 blocos). A inspeção do classificador mostrou que um heading Markdown como `## Direitos da pessoa usuária` era normalizado para texto comum e contado como claim por ter três ou mais palavras. O self-check existente cobria apenas heading curto terminado em dois-pontos. Também foi verificado que o prompt de reparo não recebia a resposta anterior: ele apenas informava que a tentativa falhou e solicitava uma nova geração.

Diagnóstico: há um falso positivo estrutural confirmado para headings Markdown sem dois-pontos. Separadamente, o retry não era um reparo direcionado; ele regenerava a resposta a partir do contexto, o que permite mudar quantidade e estrutura dos blocos e explica por que a cobertura pode piorar. Ainda é necessário retestar em runtime para medir quanto desses dois pontos explica os seis ou sete blocos não citados observados no Gemini.

Correção: headings Markdown iniciados por `#` deixam de ser considerados claim blocks. O prompt de reparo passa a receber a resposta anterior e o motivo da validação, pedindo revisão do texto existente sem acrescentar novas afirmações. A exigência de citação continua inalterada para parágrafos e itens informativos. Foram adicionados testes específicos para heading Markdown e para reaproveitamento da resposta anterior. A correção passou na CI com Ruff `All checks passed!` e pytest `94 passed, 4 warnings`; permanece aguardando apenas validação real com Gemini.

Aprendizado técnico: guardrails estruturais precisam distinguir conteúdo semântico de elementos de apresentação; caso contrário, podem produzir falsos negativos de groundedness. Um retry de reparo também precisa receber o artefato que falhou e o motivo da falha, em vez de simplesmente repetir a geração.


## 20. Groq foi bloqueada pelo Cloudflare 1010 devido à assinatura HTTP do urllib

Planejado: validar o novo `GroqProvider` com `openai/gpt-oss-120b` usando a categoria oficial `direitos_saude`, primeiro com saída limitada a 512 tokens e depois com a pergunta completa.

Observado: o `runtime-info` confirmou `llm_provider=groq`, modelo `openai/gpt-oss-120b`, endpoint correto e `reasoning_effort=low`. Porém as duas chamadas reais ao chat falharam antes da geração com `HTTP 403 Forbidden` e corpo `error code: 1010`. O traceback mostrou que a requisição era feita por `urllib.request.urlopen`.

Diagnóstico: o erro 1010 é um bloqueio de assinatura de cliente na camada Cloudflare, não um erro de retrieval nem evidência de chave inválida. O provider usava o `User-Agent` padrão do `urllib`, assinatura que pode ser classificada como cliente automatizado/bot pelo Browser Integrity Check. A requisição foi rejeitada antes de chegar ao modelo e antes de qualquer validação de grounding.

Correção: adicionar cabeçalhos HTTP explícitos ao `GroqProvider`, incluindo `Accept: application/json` e um `User-Agent` compatível com navegador identificando o RagTest. Foi adicionado teste de regressão para impedir que o provider volte a usar o `User-Agent` padrão do `urllib`. A correção passou na CI com Ruff verde e `102 passed, 4 warnings` e foi validada em runtime: o erro 403/1010 desapareceu e o GPT-OSS 120B respondeu normalmente.

Aprendizado técnico: uma integração pode passar em testes unitários e ainda falhar na borda do provedor por políticas de WAF/anti-bot. Para providers protegidos por Cloudflare, o cliente HTTP real e seus cabeçalhos fazem parte do contrato de integração e precisam ser validados no ambiente de execução.


## 21. GPT-OSS 120B respondeu rapidamente, mas não produziu citações verificáveis

Planejado: após corrigir o bloqueio Cloudflare 1010, validar o `openai/gpt-oss-120b` com uma pergunta curta sobre direitos da pessoa usuária da saúde, duas fontes oficiais e limite de 512 tokens.

Observado: a chamada chegou ao modelo e o provider funcionou. A primeira geração levou 1,12 s, processou 1121 tokens de prompt e gerou exatamente 512 tokens a aproximadamente 478,05 tokens/s, terminando por `length`. O gate encontrou 0/9 blocos citados e nenhuma citação verificável. O repair foi executado; a segunda geração levou 0,94 s, processou 1719 tokens de prompt, gerou 409 tokens a aproximadamente 478,22 tokens/s e terminou por `stop`, mas novamente apresentou 0/9 blocos citados e nenhuma citação `[n]`. O resultado final foi o fallback seguro com `grounded=false`.

Diagnóstico: a integração de transporte e autenticação Groq está funcionando e a latência é muito inferior à do Qwen3 8B local. A primeira falha foi parcialmente influenciada pelo teto de 512 tokens, mas a captura da geração RAG bruta isolou a causa estrutural principal: o modelo produziu dez direitos acompanhados por referências `【1】` e `【2】`. O parser do RagTest procurava somente o padrão ASCII `[n]`, por isso reportava `syntax_valid=false` e cobertura 0 mesmo quando as referências estavam semanticamente presentes e dentro do intervalo de fontes. A falha era de normalização de markup, não ausência de citações.

Correção: a chamada direta ao mesmo `GroqProvider`, sem retrieval e com limite de 256 tokens, retornou exatamente `Direito teste [1].`. Em seguida, a geração RAG bruta mostrou que o GPT-OSS citava corretamente os IDs das fontes, porém usando a variante Unicode `【1】`/`【2】`, enquanto o parser aceitava apenas `[1]`/`[2]`. Foi adicionada normalização canônica estrita `【n】 -> [n]` antes da validação, do repair e da resposta final; somente marcadores numéricos nessa forma são normalizados, sem aceitar IDs inválidos nem blocos sem fonte. Testes de regressão reproduzem o caso real e a CI passou com Ruff verde e `105 passed, 4 warnings`. A correção funcional ainda aguarda validação real no chat Groq.

Aprendizado técnico: alta velocidade e conclusão normal da geração não garantem aderência ao contrato estrutural exigido pelo RAG. Desempenho do provider e groundedness devem continuar sendo medidos separadamente.

## Como registrar novos casos

Usar sempre exatamente estes campos:

Planejado:

Observado:

Diagnóstico:

Correção:

Aprendizado técnico:
