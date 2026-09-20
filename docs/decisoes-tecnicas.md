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
**Impacto:** as métricas históricas e o holdout v1 permanecem intocados e reproduzíveis. A 0.5.18 não reinterpreta nem reescreve resultados antigos; ela impede que novos datasets repitam a ambiguidade e adiciona uma auditoria do contrato atual.
