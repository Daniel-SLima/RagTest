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
**Impacto:** a 0.5.11 permanece focada em groundedness/citações. A cobertura multi-intent será tratada em uma fase posterior, sem alterar os pesos já validados do `dense-rerank` nem reindexar o corpus.
