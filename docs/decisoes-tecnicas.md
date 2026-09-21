# Decisões Técnicas

Registro curto das decisões que alteram de forma relevante a arquitetura, o comportamento padrão ou a metodologia do RagTest.

Este arquivo não substitui `docs/dificuldades-tcc.md`: dificuldades registram problemas e aprendizados; aqui ficam as **decisões tomadas** e o motivo principal.

## D001 — Módulo RAG independente via API REST

**Data:** 2026-09  
**Mudança:** o RAG foi estruturado como backend independente em Python/FastAPI, em vez de ficar acoplado diretamente ao aplicativo mobile.  
**Motivo:** permitir testes isolados, reutilização e integração posterior com Flutter, React Native ou Web.  
**Impacto:** o aplicativo cliente consome o módulo por API e a evolução do RAG pode ocorrer separadamente da interface.

## D002 — Qdrant como banco vetorial e FastEmbed local para embeddings

**Data:** 2026-09  
**Mudança:** recuperação documental passou a usar Qdrant, com embeddings dense gerados localmente por FastEmbed.  
**Motivo:** manter a indexação e o retrieval independentes do provedor de LLM e reduzir envio desnecessário de conteúdo a serviços externos.  
**Impacto:** Gemini fica concentrado na etapa de geração; busca e indexação podem operar localmente.

## D003 — Público-alvo separado de categoria documental

**Data:** 2026-09  
**Mudança:** foi criado o metadado `audience` além de `category`.  
**Motivo:** filtrar apenas por categoria excluiu documentos relevantes de outros tipos, como a Caderneta da Pessoa Idosa em consultas de vacinação.  
**Impacto:** filtros passam a representar separadamente assunto/documento e público-alvo.

## D004 — Gemini 3.6 Flash como modelo padrão

**Data:** 2026-09  
**Mudança:** o modelo padrão passou de uma configuração baseada em Gemini 2.5 Flash para `gemini-3.6-flash`.  
**Motivo:** o modelo anterior não estava disponível no ambiente/API utilizado.  
**Impacto:** geração do chat usa Gemini 3.6 Flash; a arquitetura mantém interface de provider para futura substituição.

## D005 — OCR seletivo local para páginas sem texto extraído

**Data:** 2026-09-19  
**Mudança:** páginas de PDF sem texto retornado pelo extrator normal passam por OCR local com Tesseract.  
**Motivo:** a Carta dos Direitos e Deveres tinha 28 páginas e 0 chunks, tornando impossível recuperá-la no RAG.  
**Impacto:** o corpus passou de 699 para 767 chunks e documentos sem texto extraível passaram a participar do índice.

## D006 — Dense-rerank como estratégia padrão de retrieval

**Data:** 2026-09-20  
**Mudança:** o runtime deixou de usar o híbrido como estratégia principal e passou a usar `dense-rerank`.  
**Motivo:** no mesmo corpus de 767 chunks, `dense-rerank` apresentou o maior MRR tanto no conjunto dev quanto no primeiro holdout congelado.

Resultados observados:

| Suite | dense | dense-rerank | hybrid |
| --- | ---: | ---: | ---: |
| dev MRR@5 | 0.857 | 0.929 | 0.821 |
| holdout MRR@5 | 0.889 | 0.933 | 0.878 |

Todos tiveram HitRate@5=1.000 nas duas suites.

**Impacto:** `dense-rerank` é o modo padrão de busca/chat; `dense` e `hybrid` continuam disponíveis para benchmark e diagnóstico.

## D007 — Perfis de retrieval versionados no código

**Data:** 2026-09-20  
**Mudança:** parâmetros de `dense`, `dense-rerank` e `hybrid` passaram a ficar versionados em `app/rag/retrieval_profiles.py`.  
**Motivo:** evitar que um `.env` antigo altere silenciosamente o perfil que foi validado experimentalmente.  
**Impacto:** `RETRIEVAL_MODE` escolhe o perfil, mas os parâmetros do perfil validado são controlados pelo código/versionamento.

## D008 — Separação entre conjunto dev e holdout congelado

**Data:** 2026-09-20  
**Mudança:** a avaliação foi dividida em `dev` (7 consultas históricas) e `holdout` (15 consultas novas, congeladas antes da primeira execução).  
**Motivo:** reduzir o risco de avaliar apenas nas mesmas perguntas que orientaram os ajustes do sistema.  
**Impacto:** mudanças futuras não devem ser ajustadas no holdout e depois apresentadas como validação independente sobre o mesmo conjunto.

---

## Quando adicionar uma nova decisão

Adicionar uma entrada quando houver mudança relevante em:

- arquitetura;
- provider/modelo padrão;
- estratégia padrão de retrieval;
- banco/armazenamento;
- ingestão/OCR;
- segurança/privacidade;
- contratos de API;
- metodologia de avaliação;
- comportamento padrão do produto.

Formato recomendado:

```text
## D00N — Título curto

Data:
Mudança:
Motivo:
Impacto:
```


## D009 — Manter métricas históricas e adicionar métricas source-level

**Data:** 2026-09-20  
**Mudança:** a avaliação passa a manter HitRate@k e MRR@k para comparabilidade histórica e adiciona SourceRecall@k e SourceNDCG@k.  
**Motivo:** HitRate/MRR verificam a presença e a primeira posição de uma fonte esperada, mas não medem bem a cobertura quando há múltiplas fontes relevantes nem penalizam de forma explícita páginas duplicadas da mesma fonte.  
**Impacto:** novos experimentos passam a mostrar cobertura de fontes esperadas e qualidade de ordenação source-level sem invalidar as baselines antigas. A validação 0.5.10 mostrou o valor prático dessa decisão: no holdout, hybrid manteve HitRate@5=1.000, mas SourceRecall@5=0.967, revelando perda de uma fonte esperada que o HitRate sozinho não mostrava.


## D010 — Validar citações e tratar documentos recuperados como dados não confiáveis

**Data:** 2026-09-20  
**Mudança:** o chat passa a validar programaticamente citações `[n]`, repetir a geração uma vez quando a resposta usa citações inválidas/ausentes, remover scores de retrieval do prompt do LLM e delimitar os documentos recuperados como dados não confiáveis.  
**Motivo:** o prompt sozinho não garante que o LLM cite somente fontes existentes nem impede que instruções contidas em documentos sejam interpretadas como comandos. Scores internos de retrieval também não são necessários para a geração textual.  
**Impacto:** a API passa a expor `grounded`, `citation_ids` e `citation_retry_count`; respostas que continuam sem citações verificáveis após uma tentativa de reparo são substituídas por um fallback seguro. O conteúdo documental continua sendo enviado ao LLM apenas como contexto de dados, não como instrução.


## D011 — Tratar perguntas compostas com decomposição/multi-query em vez de aumentar o top-k global

**Data:** 2026-09-20  
**Mudança:** perguntas com múltiplas intenções relevantes devem ser candidatas a decomposição em subconsultas antes da recuperação, mantendo `dense-rerank` como estratégia base de cada busca.  
**Motivo:** na pergunta "Quais são os direitos e deveres da pessoa usuária da saúde?", a página com deveres ficou em rank 10; quando a intenção "deveres" foi consultada isoladamente, a mesma página ficou em rank 1. Aumentar o top-k global para 10 resolveria este caso às custas de mais contexto, ruído e custo para todas as perguntas.  
**Impacto:** a 0.5.11 permanece focada em groundedness/citações. A 0.5.12 inicia a validação controlada do mecanismo multi-query com subconsultas informadas explicitamente, antes de automatizar a decomposição. Após o primeiro experimento, ficou definido que, havendo subconsultas, a pergunta original não participa da fusão RRF por padrão, pois pode duplicar a intenção dominante; ela continua disponível via `--include-original` para diagnóstico. A validação confirmou o efeito esperado: a página 13 de deveres saiu de rank 10 na consulta composta original para rank 2 no resultado multi-query corrigido. Os pesos do `dense-rerank` e o corpus permanecem inalterados.


## D012 — Decomposição automática conservadora no chat com fallback para single-query

**Data:** 2026-09-20  
**Mudança:** o `/v1/chat` passa a detectar perguntas potencialmente compostas, solicitar ao LLM uma decomposição de no máximo três subconsultas e, quando houver pelo menos duas subintenções válidas, usar o multi-query/RRF validado na 0.5.12.  
**Motivo:** o experimento controlado mostrou que separar as intenções recuperou a página de deveres em rank 2, enquanto a consulta composta original a colocou em rank 10.  
**Impacto:** perguntas simples continuam no caminho single-query sem chamada de planejamento; perguntas potencialmente compostas podem gerar uma chamada adicional ao LLM. Saída inválida ou insuficiente do planejador não interrompe o chat: o sistema retorna automaticamente ao retrieval original. A API expõe `multi_query_used`, `retrieval_queries` e `decomposition_status` para auditoria. A validação real confirmou os dois caminhos: direitos+deveres ativou multi-query com duas subconsultas e recuperação da página 13; uma pergunta simples sobre vacinação de idosos permaneceu em single-query com `decomposition_status=not-needed`.


## D013 — Separar lint e testes na CI e fixar o contrato do Ruff

**Data:** 2026-09-20  
**Mudança:** lint e pytest passam a rodar em jobs independentes no GitHub Actions. O Ruff usado pela suite dev fica fixado em 0.16.8 e o conjunto de regras do gate é declarado explicitamente. Commits que alteram somente `docs/**` ou `README.md` não disparam CI.  
**Motivo:** o workflow anterior parava no lint, deixando o pytest como `skipped`; além disso, a faixa ampla de versão do Ruff deixava o gate sujeito a mudanças de comportamento da ferramenta.  
**Impacto:** regressões funcionais podem ser observadas mesmo quando houver falha de lint; a política de lint passa a ser reprodutível; atualizações futuras do Ruff tornam-se mudanças deliberadas.


## D014 — Medir o fingerprint real do runtime antes de pinning adicional

**Data:** 2026-09-20  
**Mudança:** antes de fixar novas versões de FastEmbed/Qdrant, a 0.5.15 adiciona um fingerprint reproduzível do ambiente com versões instaladas, versão do servidor Qdrant, modelos configurados, parâmetros de chunking e schema/contagem da collection.  
**Motivo:** o projeto já observou mudança de semântica de pooling no FastEmbed e ainda usa imagem Qdrant `latest`. Fixar versões sem registrar primeiro o ambiente realmente validado poderia cristalizar uma combinação diferente da que gerou os 767 chunks atuais.  
**Impacto:** o pinning foi baseado no runtime observado: FastEmbed 0.8.0, qdrant-client 1.19.1 e servidor Qdrant 1.19.1. A imagem padrão passa a `qdrant/qdrant:v1.19.1`; FastEmbed e qdrant-client passam a versões exatas no `pyproject.toml`. O comando `ragtest-runtime-info` não altera a collection e não exige reindexação.


## D015 — Planejar sincronização da ingestão antes de permitir exclusões

**Data:** 2026-09-20  
**Mudança:** a ingestão incremental passa a ser desenvolvida em duas etapas. Primeiro, um comando somente leitura compara os chunks atuais do corpus com os IDs determinísticos já indexados no Qdrant e identifica pontos ausentes, obsoletos e fontes órfãs. A exclusão automática só será adicionada depois dessa comparação ser validada.  
**Motivo:** o upsert atual adiciona/substitui IDs determinísticos, mas não remove chunks antigos quando um arquivo muda ou é excluído. Apagar automaticamente sem um plano auditável criaria risco desnecessário para a collection validada de 767 pontos.  
**Impacto:** `ragtest-plan-ingestion-sync` oferece uma prévia segura da sincronização e não altera o Qdrant. Após a prévia ter sido validada em 18/18 fontes e 767/767 pontos, a segunda etapa adiciona `ragtest-sync-ingestion --apply`. A aplicação recusa corpus vazio ou qualquer erro de carregamento, faz upsert dos pontos ausentes antes de remover pontos obsoletos e verifica novamente o estado final. Sem `--apply`, não há escrita.


## D016 — Auditar a estrutura dos DOCX antes de ampliar a extração

**Data:** 2026-09-20  
**Mudança:** antes de alterar o loader DOCX, a 0.5.17 adiciona uma auditoria estrutural que conta parágrafos, tabelas, células, cabeçalhos e rodapés sem imprimir o conteúdo textual.  
**Motivo:** o loader atual indexa somente `document.paragraphs`. Incluir tabelas/cabeçalhos/rodapés pode mudar o corpus e a contagem de chunks; a existência e a relevância estrutural desses elementos devem ser medidas primeiro.  
**Impacto:** `ragtest-audit-docx-structure` é somente leitura e não altera a collection. A auditoria real dos 3 DOCX encontrou 0 tabelas, 0 células, cabeçalhos sem texto e rodapés sem texto. Portanto, não há evidência de ganho ao ampliar o loader para tabelas/cabeçalhos/rodapés no corpus atual; o loader permanece inalterado e os 767 chunks são preservados. A revisão manual de privacidade dos CHATSCM continua pendente e é uma questão separada.


## D017 — Separar fontes aceitáveis de fontes obrigatórias na avaliação

**Data:** 2026-09-20  
**Mudança:** a 0.5.18 introduz um contrato explícito para rótulos de fonte em datasets futuros: `acceptable_sources` representa alternativas OR (qualquer uma pode satisfazer o caso), enquanto `required_sources` só deve ser usado quando todas as fontes listadas forem deliberadamente exigidas para cobertura. O campo histórico `expected_sources` permanece suportado, mas é marcado como semântica legada ambígua.  
**Motivo:** o dataset congelado 2026-09-20-v1 foi criado antes dessa distinção. Em casos com múltiplas `expected_sources`, as métricas SourceRecall/SourceNDCG tratam todas como conjuntamente relevantes, embora os rótulos não tenham sido produzidos como julgamentos completos de relevância.  
**Impacto:** as métricas históricas e o holdout v1 permanecem intocados e reproduzíveis. A 0.5.18 não reinterpreta nem reescreve resultados antigos. Para datasets explícitos, o avaliador passa a usar `AcceptableHitRate` para alternativas OR e `RequiredRecall`/`RequiredNDCG` para fontes AND. Um caso explícito só passa quando satisfaz todas as condições declaradas. Runs não podem misturar esquema legado e explícito.


## D018 — Medir cobertura de citações antes de introduzir um juiz semântico externo

**Data:** 2026-09-20  
**Mudança:** a 0.5.19 adiciona uma validação determinística de cobertura estrutural das citações por bloco informativo. Ela complementa a validação sintática já existente, que apenas verificava se havia ao menos uma citação válida e se os IDs estavam no intervalo disponível.  
**Motivo:** uma resposta pode passar na validação sintática mesmo contendo várias afirmações sem citação. Ao mesmo tempo, usar imediatamente um LLM externo como juiz de entailment poderia reenviar trechos recuperados, inclusive de fontes CHATSCM ainda não revisadas manualmente quanto à privacidade.  
**Impacto:** `ragtest-check-grounding-coverage` mede se cada bloco informativo contém ao menos uma citação válida, sem chamar LLM externo. Após o self-check determinístico passar, a segunda etapa promove essa cobertura a gate do runtime: uma resposta com citação válida em apenas parte dos blocos é reparada uma vez; se a segunda tentativa continuar com cobertura incompleta, o chat usa o fallback seguro e retorna `grounded=false`. Essa checagem continua estrutural e não prova que a fonte citada sustenta semanticamente a afirmação. Qualquer juiz semântico externo permanece adiado até existir política adequada de privacidade para os CHATSCM.


## D019 — Retry de aplicação somente para indisponibilidade transitória do LLM

**Data:** 2026-09-20  
**Mudança:** o provider Gemini passa a executar até 2 retries adicionais de aplicação, com backoff exponencial curto, somente para códigos transitórios 429/500/502/503/504.  
**Motivo:** no teste real da 0.5.19, o SDK propagou 503 UNAVAILABLE por alta demanda mesmo após sua política interna de retry.  
**Impacto:** falhas transitórias recebem uma segunda janela limitada de recuperação. Após esgotamento, o provider levanta `LLMServiceUnavailableError`; a API responde 503 e o CLI mostra mensagem amigável. Erros 4xx não transitórios não são repetidos. Os parâmetros são configuráveis por `LLM_SERVICE_RETRY_ATTEMPTS` e `LLM_SERVICE_RETRY_BASE_DELAY_SECONDS`. Essa mudança não altera retrieval, corpus ou Qdrant.


## D020 — Ollama como provider local explícito, sem fallback automático entre modelos

**Data:** 2026-09-20  
**Mudança:** adicionar `OllamaProvider` à interface existente de LLM e permitir seleção explícita por `LLM_PROVIDER=ollama`, usando `qwen3:8b`, `think=false` e contexto 8192 como baseline local inicial.  
**Motivo:** o Gemini ficou temporariamente indisponível durante a validação da 0.5.19, e o notebook local confirmou execução do Qwen3 8B com API acessível a partir do container Docker.  
**Evidência local:** `qwen3:8b` Q4_K_M, 8.2B parâmetros, resposta sem reasoning com `think=false`, contexto 8192, carga observada de aproximadamente 36% CPU / 64% GPU nesse contexto e acesso via `http://host.docker.internal:11434`.  
**Impacto:** o mesmo retrieval, corpus, Qdrant e gate de grounding podem ser testados com Gemini ou Ollama sem reindexação. A troca é explícita para preservar rastreabilidade experimental; não há fallback automático Gemini→Ollama nesta etapa. O provider rejeita vazamento de `</think>` quando thinking está desativado.


## D021 — Groq como terceiro provider explícito para contingência e comparação

**Data:** 2026-09-20  
**Mudança:** adicionar `GroqProvider` à interface de LLM, inicialmente com `openai/gpt-oss-120b`, seleção explícita por `LLM_PROVIDER=groq` e sem fallback automático entre providers.  
**Motivo:** o Gemini apresentou indisponibilidade transitória por 503 e, posteriormente, 429 mesmo após retries; o Qwen3 8B local é funcional, mas a geração medida no notebook ficou em aproximadamente 8,94 tokens/s. A Groq oferece endpoint OpenAI-compatible e permite testar o GPT-OSS 120B sem alterar retrieval, corpus ou Qdrant.  
**Impacto:** o mesmo RAG pode ser executado explicitamente com Gemini, Groq/GPT-OSS 120B ou Ollama/Qwen3 8B. O provider Groq desativa reasoning na resposta, mantém reasoning effort baixo, registra tokens/latência e trata 429/498/5xx como falhas transitórias limitadas. Testes externos continuam restritos a fontes oficiais enquanto CHATSCM não tiver revisão manual de privacidade.


## D022 — Pós-processamento determinístico remove claims sem citação após o repair

**Data:** 2026-09-20  
**Mudança:** após a geração inicial e um único repair, o RagTest pode remover deterministicamente o claim sem citação apenas quando a resposta reparada mantém sintaxe válida, exatamente um claim uncited, pelo menos um claim citado e cobertura de pelo menos 80%. A resposta é revalidada e só é aceita se a cobertura resultante for 100%.  
**Motivo:** no teste real com Groq/GPT-OSS 120B, o modelo manteve repetidamente uma conclusão final sem citação mesmo quando o repair recebeu o bloco exato que precisava ser corrigido. Continuar adicionando retries ou relaxar o gate tornaria o comportamento menos previsível.  
**Impacto:** o sistema deixa de depender exclusivamente da obediência do LLM no último estágio sem permitir poda ampla de respostas pouco sustentadas. Citações fora do intervalo, baixa cobertura, múltiplos claims sem citação, respostas sem nenhuma citação válida ou respostas que continuem inválidas após a poda caem no fallback seguro. O CLI passa a distinguir `stage=initial`, `stage=repair` e `stage=postprocess`, enquanto `citation_retry_count` permanece representando apenas chamadas adicionais ao LLM. Validado em runtime com Groq/GPT-OSS 120B: `initial 8/9`, `repair 8/9`, `postprocess 8/8`, cobertura final 1.000 e `grounded=true`.


## D023 — Pós-processamento antecipado para alta cobertura evita repair externo desnecessário

**Data:** 2026-09-20  
**Mudança:** antes de chamar o repair do LLM, o RagTest pode tentar a poda determinística quando a resposta inicial já possui sintaxe de citação válida, exatamente um claim sem citação, pelo menos um claim citado e cobertura estrutural de pelo menos 80%. A resposta podada é revalidada e só é aceita se atingir 100% de cobertura.  
**Motivo:** três validações reais com fontes oficiais distintas — direitos da pessoa usuária, vacinação da pessoa idosa e saúde bucal na gestação — terminaram com grounded=true, mas todas consumiram citation_retry_count=1. No padrão observado, um único bloco uncited podia ser eliminado deterministicamente, tornando a segunda chamada externa um custo evitável de tokens e requisições.  
**Impacto:** casos de alta cobertura podem terminar com uma única chamada ao LLM e citation_retry_count=0. Respostas com cobertura inferior a 80%, mais de um claim uncited ou sintaxe inválida preservam o fluxo anterior de repair/fallback. A mudança foi desenvolvida por TDD; o teste novo falhou primeiro porque duas chamadas ainda eram feitas e, após a implementação, a CI passou com Ruff verde e 109 passed, 4 warnings. Observado em runtime com Groq/GPT-OSS 120B no cenário de direitos_saude: grounded=true, citation_ids=[1,2] e citation_retry_count=0, confirmando que nenhuma chamada de repair foi necessária nessa execução. Como a resposta da API não expõe os estágios de validação, esse log isolado não distingue uma resposta inicial já válida de um caso resolvido por postprocess-before-repair.


## D024 — Instrumentar limites da Groq antes de automatizar fallback entre providers

**Data:** 2026-09-20  
**Mudança:** a 0.5.20 captura e expõe os headers oficiais de rate limit da Groq no provider e no CLI antes de introduzir qualquer fallback automático entre LLMs.  
**Motivo:** a Groq se mostrou adequada para desenvolvimento pela velocidade, mas possui cotas de requisições e tokens. Sem observabilidade local, um fallback automático poderia mascarar consumo de cota, misturar providers em avaliações e dificultar o diagnóstico de 429.  
**Impacto:** cada resposta Groq pode atualizar um snapshot de RPD/TPM e respectivos resets, inclusive em HTTP 429. O CLI identifica explicitamente `requests_rpd` e `tokens_tpm`. Os headers não fornecem saldo de TPD diário, portanto essa métrica continua fora do snapshot. A seleção de provider permanece explícita e sem fallback automático. Validação real com `openai/gpt-oss-120b` confirmou `requests_rpd: 999/1000 reset=1m26.4s` e `tokens_tpm: 6069/8000 reset=14.482s`.


## D025 — Manter o cliente demonstrativo multiplataforma desacoplado do núcleo RAG

**Data:** 2026-09-21  
**Mudança:** a interface de demonstração passa a usar React Native + Expo + TypeScript, substituindo o scaffold experimental Next.js criado no início da 0.5.21.  
**Motivo:** o e-mail completo do orientador define um frontend/aplicativo multiplataforma como parte da arquitetura sugerida e, principalmente, deixa claro que o artefato central deve ser um módulo conversacional integrável ao Se Cuida Mulher. Um cliente Expo atende a demonstração do TCC sem tornar o backend dependente do aplicativo oficial.  
**Impacto:** o frontend fica em `frontend/`, possui dependências e testes próprios e consome apenas o contrato da API. Nenhuma regra de retrieval, grounding, ingestão ou provider é movida para o cliente. O Se Cuida Mulher poderá substituir esse cliente futuramente sem reescrever o núcleo RAG.

## D026 — Usar REST como transporte inicial do cliente

**Data:** 2026-09-21  
**Mudança:** a primeira integração do cliente multiplataforma usará `POST /v1/chat` por REST/JSON. WebSocket não é requisito da 0.5.x inicial.  
**Motivo:** o endpoint REST já está implementado e validado, atende respostas não-streaming e simplifica testes, observabilidade e futura integração com clientes diferentes. WebSocket adicionaria complexidade sem necessidade funcional demonstrada neste momento.  
**Impacto:** o contrato TypeScript do frontend espelha o schema FastAPI. WebSocket/streaming permanece uma evolução possível caso a experiência futura realmente exija resposta incremental.


## D027 — Configurar CORS restrito e URL do backend por ambiente para o cliente Expo

**Data:** 2026-09-21  
**Mudança:** a integração Expo Web -> FastAPI usa CORS explícito com origens configuráveis e o cliente lê a URL da API por `EXPO_PUBLIC_RAG_API_BASE_URL`, usando `http://localhost:8000` apenas como padrão de desenvolvimento.  
**Motivo:** o navegador aplica same-origin policy entre Expo Web em `localhost:8081` e FastAPI em `localhost:8000`. Liberar `*` resolveria o protótipo, mas criaria um padrão inadequado para evolução do projeto. Além disso, Android emulator e dispositivo físico exigem endereços diferentes do localhost do navegador.  
**Impacto:** as origens padrão de desenvolvimento são `http://localhost:8081` e `http://127.0.0.1:8081`; outras origens devem ser configuradas explicitamente em `CORS_ALLOWED_ORIGINS`. O frontend pode apontar para outro host sem alterar código por meio de `EXPO_PUBLIC_RAG_API_BASE_URL`. React Native nativo continua consumindo o mesmo contrato REST.
