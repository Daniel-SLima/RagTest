# Contexto de Continuidade do Projeto — RagTest / Se Cuida Mulher

> **Documento vivo de continuidade.**
>
> Este arquivo existe para permitir que o desenvolvimento continue em outro chat sem perda de contexto.
> **Sempre que houver mudança relevante de código, arquitetura, testes, métricas, decisões, dificuldades ou próximos passos, este arquivo deve ser atualizado antes de encerrar a tarefa.**
>
> Em um novo chat, antes de continuar o projeto, leia este arquivo e depois confira o estado atual do repositório/branch/PR.

**Última atualização:** 2026-09-20  
**Repositório:** `Daniel-SLima/RagTest`  
**Branch padrão:** `main`  
**Estado validado e mesclado no main:** `0.5.18`  
**Trabalho em andamento:** `0.5.19` em `feature/semantic-grounding-0.5.19`; primeira etapa adiciona auditoria determinística de cobertura estrutural das citações por bloco informativo, sem alterar o endpoint e sem enviar conteúdo a juiz externo.

---

## 1. Objetivo final do projeto

Este projeto é o módulo conversacional baseado em RAG do TCC:

**“Desenvolvimento de Módulo Conversacional Baseado em RAG para Apoio ao Letramento em Saúde e Acesso a Serviços no Aplicativo Se Cuida Mulher”.**

O objetivo final é entregar um módulo independente, reutilizável e integrável ao aplicativo **Se Cuida Mulher**, capaz de:

- receber perguntas em linguagem natural;
- recuperar trechos relevantes de documentos oficiais e materiais do corpus;
- gerar respostas contextualizadas e fundamentadas;
- citar as fontes utilizadas;
- reduzir alucinações;
- manter rastreabilidade/auditoria das respostas;
- futuramente oferecer histórico de sessão, streaming e integração com o aplicativo;
- servir como artefato técnico do TCC, com métricas de retrieval e documentação das decisões de engenharia.

O módulo deve continuar independente da interface mobile até o pipeline RAG estar estável e mensurável.

---

## 2. Escopo acadêmico e técnico

### Objetivo geral

Desenvolver e integrar um módulo de chat inteligente baseado em RAG para apoio ao letramento informacional em saúde e orientação de acesso/agendamento de serviços.

### Objetivos técnicos

1. Pipeline automatizado de ingestão, extração, OCR quando necessário, limpeza, chunking e vetorização.
2. Retrieval semântico e/ou híbrido sobre corpus documental.
3. Geração fundamentada com LLM e citações de fontes.
4. Segurança, resiliência e mitigação de respostas sem base documental.
5. Auditoria e métricas de qualidade do retrieval.
6. API REST reutilizável.
7. Futuramente: sessões, histórico, streaming/WebSocket, links/gatilhos de serviços e integração com app.

---

## 3. Arquitetura atual

### Backend

- Python 3.12
- FastAPI
- Docker / Docker Compose

### Banco vetorial

- Qdrant

### Embeddings

**Dense:**
- FastEmbed
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- dimensão: 384

**Sparse:**
- FastEmbed
- `Qdrant/bm25`
- idioma: português

### LLM

- Google Gemini
- modelo atual: `gemini-3.6-flash`

### Processamento documental

- PyPDF para extração textual normal;
- Tesseract OCR + pacote português;
- PyMuPDF para renderização das páginas que precisam de OCR;
- python-docx para DOCX;
- LangChain Text Splitters para chunking.

### API atual

- `GET /health`
- `GET /ready`
- `POST /v1/search`
- `POST /v1/chat`
- Swagger: `http://localhost:8000/docs`

---

## 4. Fluxo atual do RAG

```text
PDF / DOCX
    |
    v
extração normal
    |
    +---- página sem texto ----> OCR Tesseract local
    |
    v
Document
    |
    v
chunking
    |
    +-------------------+
    |                   |
    v                   v
dense embedding       BM25 sparse
    |                   |
    +---------+---------+
              |
              v
            Qdrant
              |
              v
     retrieval de candidatos
              |
              v
     agrupamento por página
              |
              v
      reranking / seleção
              |
              v
          contexto RAG
              |
              v
      Gemini 3.6 Flash
              |
              v
       resposta + fontes
```

---

## 5. Corpus atual

Total de arquivos: **18**

Categorias principais:

- alimentação;
- chatscm;
- diabetes;
- direitos_saude;
- gestacao;
- medicamentos;
- pessoa_idosa;
- saude_sexual_reprodutiva;
- vacinacao.

Arquivos incluem PDFs do SUS/Ministério da Saúde e 3 DOCX da pasta CHATSCM.

### Cobertura após OCR — estado 0.5.6

Antes do OCR havia **699 chunks**.

Após a correção de ingestão:

- corpus total: **767 chunks**;
- Carta dos Direitos e Deveres: 28/28 páginas recuperadas por OCR;
- Carta dos Direitos e Deveres: aproximadamente 41 mil caracteres;
- Carta dos Direitos e Deveres: 62 chunks;
- Caderneta da Gestante: 50/50 páginas com texto, incluindo 3 recuperadas por OCR;
- Caderneta da Pessoa Idosa: 63/64 páginas com texto; a página restante pode ser visualmente vazia e ainda precisa ser auditada se isso se tornar relevante.

---

## 6. Regra de privacidade importante

Os arquivos `chatscm/*.docx` ainda **não foram manualmente auditados neste projeto quanto a dados pessoais/identificáveis**.

Por isso:

- não presumir que estão anonimizados;
- não afirmar que são seguros apenas pelo nome;
- antes de usar conteúdo CHATSCM em chamadas externas do Gemini em contexto real, revisar/desidentificar ou obter autorização adequada;
- nunca versionar chaves, tokens, segredos ou dados clínicos identificáveis.

A `GEMINI_API_KEY` deve existir apenas no `.env` local.

---

## 7. Estado do .env local

Configuração recomendada a partir da 0.5.8:

```env
PDF_OCR_ENABLED=true
PDF_OCR_LANGUAGE=por
PDF_OCR_DPI=200
PDF_OCR_TIMEOUT_SECONDS=60

SPARSE_EMBEDDING_PROVIDER=fastembed_bm25
SPARSE_EMBEDDING_MODEL=Qdrant/bm25
SPARSE_EMBEDDING_LANGUAGE=portuguese

RETRIEVAL_MODE=dense-rerank
RETRIEVAL_MERGE_SAME_PAGE=true
RETRIEVAL_MAX_GROUP_CHARS=5000

LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.6-flash
LLM_TEMPERATURE=0.1
```

A 0.5.8 passa a usar perfis versionados para `dense`, `dense-rerank` e `hybrid`. As antigas variáveis de tuning de candidate multiplier, score margin, pesos lexicais e pesos híbridos podem continuar no `.env` local por compatibilidade, mas são ignoradas pelo runtime novo.

No ambiente local do usuário, `LLM_MAX_OUTPUT_TOKENS` foi mantido em **4096** após um caso real de truncamento da resposta.

Nunca copiar nem registrar o valor da chave Gemini neste documento.

---

## 8. O que já foi concluído

### Fases iniciais

- estrutura do projeto;
- FastAPI;
- Qdrant;
- Docker Compose;
- loaders PDF/DOCX;
- chunking;
- embeddings locais;
- ingestão;
- retrieval;
- endpoint de busca;
- chat RAG;
- Gemini;
- metadado `audience`;
- filtros por público;
- fontes/citações;
- CLI de ingestão, busca, chat e avaliação.

### Melhorias de retrieval

- overfetch;
- agrupamento de chunks da mesma página;
- reconstrução respeitando `start_index`;
- remoção de overlap quando possível;
- reranking lexical;
- retrieval híbrido dense + BM25;
- RRF;
- avaliação com HitRate@5 e MRR@5.

### Qualidade de ingestão

- auditoria por arquivo;
- detecção de `NO_TEXT`, `NO_CHUNKS`, `PARTIAL_TEXT`;
- OCR seletivo local;
- metadata `extraction_method`.

---

## 9. Histórico experimental

### 0.5.1 — dense

Corpus ainda incompleto.

- HitRate@5: 0.857
- MRR@5: 0.714

### 0.5.2 — dense + reranking lexical

Corpus ainda incompleto.

- HitRate@5: 0.857
- MRR@5: 0.786

### 0.5.3 — dense + BM25 + RRF

Corpus ainda incompleto.

- HitRate@5: 0.714
- MRR@5: 0.607

### 0.5.4 — BM25 enriquecido

Corpus ainda incompleto.

- HitRate@5: 0.857
- MRR@5: 0.690

### 0.5.5 — auditoria

Descoberta principal:

`direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf`

tinha:

- 28 páginas;
- 0 páginas com texto;
- 0 caracteres;
- 0 chunks.

Logo, a falha de retrieval da consulta sobre direitos/deveres era principalmente uma falha de ingestão.

### 0.5.6 — OCR seletivo

Corpus corrigido para 767 chunks.

No modo híbrido atual:

- HitRate@5: **1.000 (7/7)**
- MRR@5: **0.821**
- consulta de direitos/deveres recupera a Carta no rank 1.

**Importante:** esta é a primeira baseline pós-correção de cobertura. Os números anteriores não são diretamente comparáveis porque o corpus mudou.

### 0.5.7 — benchmark controlado no mesmo corpus

Todos os modos foram executados sobre os mesmos 767 chunks:

| Modo | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| dense | 1.000 | 0.857 |
| dense-rerank | 1.000 | 0.929 |
| hybrid | 1.000 | 0.821 |

`dense-rerank` é o melhor resultado **medido no conjunto atual de sete consultas**, mas o conjunto ainda é pequeno e não permite concluir superioridade geral.

---

## 10. Dificuldades do TCC já registradas

Arquivo detalhado:

`docs/dificuldades-tcc.md`

Casos atuais:

1. filtro por categoria piorou a recuperação;
2. Gemini atingiu limite de tokens;
3. avaliador dependia de arquivo que não existia no runtime Docker;
4. busca densa não recuperava a carta de direitos;
5. reranking melhorou MRR, mas não recall;
6. retrieval híbrido inicial piorou métricas;
7. BM25 enriquecido não resolveu a fonte problemática;
8. fonte esperada tinha zero texto e zero chunks;
9. retrieval híbrido não superou dense-rerank no mesmo corpus;
10. `pyproject.toml` inválido bloqueou o build Docker da 0.5.11;
11. consulta composta recuperou direitos, mas não detalhou deveres;
12. RRF reforçou a intenção dominante quando a pergunta original foi fundida com as subconsultas;
13. CI bloqueava o pytest por falhas de lint;
14. teste de health tinha versão inicial hardcoded.

**Regra:** quando algo planejado não funcionar como esperado, criar uma nova “Dificuldade TCC #N” com:

- planejado;
- observado;
- diagnóstico;
- correção;
- Aprendizado técnico.

---

## 11. O que está sendo feito agora

### Fase 0.5.14 — CI e execução real da suíte

A 0.5.13 foi validada e mesclada no `main`.

Objetivo atual:

- corrigir as 8 violações Ruff que bloqueiam a CI;
- separar lint e pytest em jobs independentes;
- tornar a versão/regras do Ruff reprodutíveis;
- finalmente observar o resultado real da suíte pytest no GitHub Actions;
- evitar workflows em mudanças exclusivamente documentais.

Branch ativa:

`feature/ci-quality-gate-0.5.14`

Status: **validado em CI e runtime local. Lint verde, pytest 51 passed / 4 warnings, `/health`=0.5.14 e `/ready` com Qdrant ok. PR #8 aguarda autorização explícita de merge.**

### Histórico — fase 0.5.13 — decomposição automática no chat

A 0.5.12 foi validada e mesclada no `main`.

Objetivo atual:

- detectar perguntas potencialmente compostas;
- usar o LLM apenas como planejador de subconsultas quando necessário;
- limitar a decomposição a 2-3 consultas autossuficientes;
- usar o multi-query/RRF validado na 0.5.12;
- preservar single-query para perguntas simples;
- fazer fallback seguro para single-query quando o planejamento falhar;
- expor diagnóstico da estratégia na resposta da API.

Branch ativa:

`feature/automatic-decomposition-0.5.13`

Status: **validado em runtime nos dois caminhos: multi-query automático para pergunta composta e single-query para pergunta simples. PR #7 permanece draft aguardando autorização explícita de merge.**

### Histórico — fase 0.5.12 — experimento controlado de multi-query

A 0.5.11 foi validada e mesclada no `main`.

Objetivo atual:

- provar o mecanismo de multi-query antes de automatizar a decomposição;
- executar a consulta original e subconsultas explícitas;
- preservar `dense-rerank` em cada busca;
- deduplicar resultados por fonte/página;
- fundir rankings por RRF;
- verificar se a página 13 de deveres volta ao top 5 no caso diagnóstico;
- não alterar pesos, corpus ou endpoint `/v1/chat` nesta etapa.

Branch ativa:

`feature/multi-query-retrieval-0.5.12`

Status: **validado em runtime: self-check completo PASS e página 13 de deveres em rank 2 no top 5 multi-query. PR #6 permanece draft aguardando autorização de merge.**

### Histórico — fase 0.5.11 — groundedness e citações verificáveis

A 0.5.10 foi validada e mesclada no `main`.

Objetivo atual:

- remover scores internos do contexto enviado ao LLM;
- tratar documentos recuperados explicitamente como dados não confiáveis;
- adicionar defesa de prompt contra instruções encontradas dentro dos documentos;
- validar programaticamente citações `[n]`;
- repetir a geração uma vez quando citações forem inválidas ou ausentes;
- retornar fallback seguro se a resposta continuar sem citações verificáveis;
- expor `grounded`, `citation_ids` e `citation_retry_count` na API.

Branch ativa:

`feature/grounded-citations-0.5.11`

Status: **fluxo real validado: `grounded=true`, citações [1,2,3] válidas e `citation_retry_count=0`. PR #5 permanece draft. A resposta revelou cobertura parcial de deveres, registrada como Dificuldade TCC #11.**

### Histórico — fase 0.5.10 — métricas source-level

A 0.5.9 foi validada e mesclada no `main`.

Objetivo atual:

- preservar HitRate@k e MRR@k para comparação histórica;
- adicionar SourceRecall@k para medir quantas fontes esperadas distintas foram recuperadas;
- adicionar SourceNDCG@k para medir a ordenação das fontes esperadas sem contar páginas repetidas da mesma fonte como novos acertos;
- mostrar a quantidade de fontes distintas por consulta;
- não alterar retrieval, pesos, corpus ou dataset.

Branch ativa:

`feature/source-metrics-0.5.10`

Status: **implementado, PR #4 aberto como draft e aguardando validação local**.

### Histórico — fase 0.5.9 — avaliação holdout congelada

O PR #2 da 0.5.8 foi autorizado pelo usuário e mesclado no `main`.

Objetivo atual:

- ampliar a avaliação sem alterar os parâmetros do retrieval;
- separar as 7 consultas usadas no desenvolvimento de um conjunto novo;
- congelar um holdout antes da primeira execução;
- verificar se o `dense-rerank` generaliza para perguntas e domínios não usados no ajuste;
- preservar a primeira execução do holdout como evidência experimental.

### Branch ativa

`feature/holdout-evaluation-0.5.9`

### Dataset versionado

`2026-09-20-v1`

Suites:

- `dev`: 7 consultas históricas;
- `holdout`: 15 consultas novas;
- `all`: 22 consultas.

O holdout cobre alimentação, vacinação de adulto/adolescente/criança/idoso/gestante, saúde bucal na gestação, cadernetas, medicamentos, contracepção e paráfrases das consultas centrais.

Status: **implementado e validado localmente. No holdout, `dense-rerank` manteve HitRate@5=1.000 e obteve o maior MRR@5 (0.933) entre os três perfis. A suite dev reproduziu exatamente a baseline histórica. PR #3 aguarda autorização de merge.**

---

## 12. Ponto exato onde o trabalho foi pausado

A 0.5.8 foi validada e mesclada no `main`.

A 0.5.9 foi implementada e validada localmente.

Verificado:

1. `/health` retornou versão 0.5.9;
2. `/ready` retornou ready com Qdrant ok;
3. primeira execução preservada de `dense-rerank` no holdout:
   - HitRate@5=1.000 (15/15);
   - MRR@5=0.933;
4. comparação completa no holdout:
   - dense: HitRate@5=1.000, MRR@5=0.889;
   - dense-rerank: HitRate@5=1.000, MRR@5=0.933;
   - hybrid: HitRate@5=1.000, MRR@5=0.878;
5. regressão da suite dev reproduziu exatamente:
   - dense: HitRate@5=1.000, MRR@5=0.857;
   - dense-rerank: HitRate@5=1.000, MRR@5=0.929;
   - hybrid: HitRate@5=1.000, MRR@5=0.821.

Conclusão experimental: `dense-rerank` foi o perfil com maior MRR tanto na suite dev quanto no primeiro holdout congelado, sempre com HitRate@5=1.000. Isso reforça a escolha do perfil padrão, sem transformar o resultado em uma alegação de superioridade universal.

Dois pontos qualitativos permanecem relevantes:

- `holdout-caderneta-gestante`: a Caderneta da Gestante ficou em rank 2;
- `holdout-vacinas-gestante-parafrase`: o rank 1 foi `chatscm_gestante.docx`; uma fonte esperada ficou em rank 2 e o calendário oficial em rank 5.

O PR #3 ainda não foi mesclado.

Não recriar a collection: os 767 chunks continuam compatíveis.

---

## 13. Próximos 5 passos

### Passo 1 — mesclar a 0.5.10 após autorização

A validação de runtime foi concluída. Aguardar autorização explícita do usuário para mesclar o PR #4.

### Passo 2 — analisar diversidade e cobertura por fonte

Os novos números mostram que o perfil hybrid perdeu uma das duas fontes esperadas em um caso do holdout (SourceRecall@5 agregado=0.967), enquanto dense e dense-rerank mantiveram 1.000. Usar isso como evidência na análise, sem alterar o holdout.

### Passo 3 — preparar decomposição/multi-query

Implementar e avaliar detecção/decomposição de perguntas compostas sem aumentar o top-k global. O caso direitos+deveres é o primeiro caso diagnóstico.

### Passo 4 — preparar relevância preferencial

Definir, em uma fase separada e documentada, como distinguir fonte aceitável de fonte preferencial sem reescrever retroativamente o holdout original.

### Passo 5 — reforçar groundedness e segurança

Validar citações, remover scores internos do prompt, adicionar defesa contra prompt injection documental e revisar a privacidade dos arquivos CHATSCM antes de chamadas externas.

### Passo 6 — preparar a camada de produto

Adicionar logs/auditoria estruturada, sessões, histórico, streaming e integração posterior com o aplicativo Se Cuida Mulher.

---

## 14. Pendências técnicas conhecidas

- warning do FastEmbed sobre mudança de pooling do modelo dense;
- dependências ainda usam intervalos e Qdrant Docker usa `latest`; devem ser pinadas antes da entrega;
- página sem texto restante na Caderneta da Pessoa Idosa pode precisar de inspeção visual;
- loader DOCX atualmente foca em parágrafos; tabelas/cabeçalhos/rodapés ainda devem ser avaliados;
- estratégia de remoção de chunks antigos em ingestão incremental ainda não foi implementada;
- metadata de versão/configuração do embedding na collection deve ser reforçada;
- cliente Gemini pode ser persistido e receber telemetria de `finish_reason`/uso;
- warning de Hugging Face sem autenticação é não bloqueante;
- a suite histórica tem 7 perguntas; a 0.5.9 adiciona 15 perguntas holdout, ainda aguardando primeira execução.

---

## 15. Regras de desenvolvimento daqui para frente

1. Não afirmar que algo “passou” sem teste real.
2. Não alterar métricas para fazer um experimento parecer melhor.
3. Preservar baselines históricas.
4. Sempre comparar estratégias no mesmo corpus quando a comparação for algorítmica.
5. Quando o corpus mudar, registrar explicitamente a mudança.
6. Preferir branch + Pull Request para novas alterações.
7. Não fazer merge sem pedido/validação do usuário.
8. Não expor chaves ou segredos.
9. Não enviar dados de saúde identificáveis a serviços externos.
10. Atualizar **este arquivo** ao final de toda tarefa relevante.
11. Quando uma decisão alterar arquitetura, provider, estratégia padrão, segurança, armazenamento ou metodologia de avaliação, registrar também em `docs/decisoes-tecnicas.md`.

---

## 16. Procedimento para reiniciar em outro chat

Quando o usuário disser algo como:

> “Continuar o RagTest”

ou simplesmente:

> “continuar”

o assistente deve:

1. abrir `docs/CONTEXTO_CONTINUIDADE.md` no GitHub;
2. verificar a branch/PR atual;
3. verificar se houve commits posteriores à última atualização;
4. retomar pelo item **“Ponto exato onde o trabalho foi pausado”**;
5. atualizar este documento novamente ao final da nova etapa.

Se houver divergência entre este arquivo e o estado real do GitHub, o **GitHub atual prevalece** e este arquivo deve ser corrigido.

---

## 17. Arquivos de documentação relacionados

- `docs/CONTEXTO_CONTINUIDADE.md` — este arquivo; estado geral e ponto de retomada;
- `docs/dificuldades-tcc.md` — problemas, diagnósticos, correções e aprendizados;
- `docs/decisoes-tecnicas.md` — registro curto das decisões que mudam arquitetura, comportamento padrão ou metodologia;
- `docs/avaliacao-retrieval.md` — histórico de métricas e experimentos;
- `README.md` — uso e estado funcional do projeto.

---

## 18. Resumo de retomada rápida

```text
Projeto: RagTest / Se Cuida Mulher
Main validado/mesclado: 0.5.18
Corpus: 18 arquivos / 767 chunks após OCR
Qdrant: dense + sparse
Dense: paraphrase-multilingual-MiniLM-L12-v2
Sparse: Qdrant/bm25 português
LLM: Gemini 3.6 Flash
OCR: Tesseract local, seletivo
Baseline pós-OCR híbrida: HitRate@5=1.000 / MRR@5=0.821

Em andamento:
0.5.18 semântica explícita dos rótulos de avaliação

Branch:
feature/evaluation-label-semantics-0.5.18

PR:
#12 draft — Explicita semântica dos rótulos de avaliação na 0.5.18

PR:
#11 draft — Adiciona auditoria estrutural de DOCX na 0.5.17

PR:
#10 draft — Adiciona planejamento seguro da ingestão incremental 0.5.16

PR:
#9 draft — Adiciona fingerprint de runtime na 0.5.15

PR:
#4 draft — Adiciona métricas source-level na avaliação 0.5.10

Dataset:
2026-09-20-v1 — dev=7, holdout=15, all=22

PR:
#3 draft — Adiciona avaliação holdout congelada na 0.5.9

0.5.7 validada:
dense         HitRate@5=1.000 / MRR@5=0.857
dense-rerank  HitRate@5=1.000 / MRR@5=0.929
hybrid        HitRate@5=1.000 / MRR@5=0.821

Pausado em:
a infraestrutura de avaliação v2 da 0.5.18 foi validada localmente. O `ragtest-check-evaluation-v2` passou em todos os checks de semântica OR/AND. A regressão do dataset v1 em `dense-rerank` reproduziu exatamente a baseline histórica: HitRate@5=1.000 (7/7), MRR@5=0.929, SourceRecall@5=1.000 e SourceNDCG@5=0.936. A CI final passou com Ruff verde e `72 passed, 4 warnings`.

O warning do FastEmbed sobre mean pooling continua sendo o warning conhecido do runtime 0.8.0 e não altera a decisão já tomada na 0.5.15 de preservar o runtime validado, em vez de voltar cegamente para 0.5.1.

Próxima ação ao receber "continuar":
aguardar autorização explícita do usuário para merge do PR #12. Após o merge, iniciar a próxima fase de groundedness/segurança sem reindexar a collection.
```


---

## 19. Modelo de conversa e comportamento esperado do assistente

Este projeto está sendo desenvolvido de forma incremental por chat. A continuidade técnica não é suficiente: a experiência de conversa também deve permanecer consistente entre chats.

Ao retomar o projeto em um novo chat, o assistente deve conversar como continuação natural do trabalho anterior, e não como se estivesse conhecendo o projeto pela primeira vez.

### Idioma e tom

- responder em português do Brasil;
- manter tom colaborativo, técnico e acessível;
- ser direto, mas explicar o raciocínio necessário para o usuário entender por que cada mudança está sendo feita;
- evitar respostas excessivamente formais ou acadêmicas durante o desenvolvimento;
- preservar termos usados durante o projeto, como `Dificuldade TCC`, `baseline`, `retrieval`, `chunks`, `dense`, `BM25`, `RRF`, `OCR` e nomes das fases;
- não reexplicar conceitos básicos já consolidados sem necessidade;
- não agir como se o usuário precisasse reapresentar o projeto.

### Forma de conduzir o desenvolvimento

O fluxo de conversa deve seguir este padrão:

1. analisar o log, erro ou resultado enviado;
2. dizer claramente **o que aconteceu**;
3. explicar **o que esse resultado significa tecnicamente**;
4. relacionar o resultado com o TCC quando ele produzir aprendizado relevante;
5. implementar/corrigir no GitHub quando apropriado;
6. informar exatamente o que foi alterado;
7. dizer se precisa ou não reconstruir Docker, reindexar Qdrant ou alterar `.env`;
8. fornecer os comandos exatos para Windows CMD;
9. esperar o usuário executar e enviar o retorno antes de afirmar que a etapa passou;
10. atualizar este arquivo ao final da tarefa relevante.

### Regra de verificação

Nunca dizer que:

- a versão está funcionando;
- um teste passou;
- um bug foi corrigido;
- uma métrica melhorou;
- uma integração está pronta;

sem evidência real de execução.

Usar distinções explícitas:

- **implementado:** código foi alterado;
- **aguardando validação:** ainda não houve execução pelo usuário/CI;
- **verificado:** existe log/teste confirmando;
- **hipótese:** ainda será testada.

### Quando o usuário enviar logs

Se o usuário colar saída de CMD/Docker:

- ler o log completo;
- identificar warnings separadamente de erros bloqueantes;
- não tratar warning como falha automaticamente;
- comparar o resultado com a versão/teste anterior;
- apontar mudanças de métricas;
- registrar uma nova Dificuldade TCC somente quando algo planejado falhar, revelar limitação ou exigir mudança relevante;
- se o resultado estiver correto, dizer claramente que a hipótese foi confirmada;
- dar somente os próximos comandos necessários para a etapa seguinte.

### Quando houver uma Dificuldade TCC

Usar o formato:

```text
Dificuldade TCC #N — título curto

Planejado:
...

Observado:
...

Diagnóstico:
...

Correção:
...

Aprendizado técnico:
...
```

Também atualizar `docs/dificuldades-tcc.md`.

### Quando uma versão mudar

Sempre informar:

- versão anterior;
- nova versão;
- objetivo da mudança;
- branch;
- commit;
- PR, quando existir;
- se exige `docker compose up --build`;
- se exige `ragtest-ingest --recreate`;
- comandos de validação.

### GitHub

Preferir:

```text
feature branch
    ↓
commit
    ↓
Pull Request draft
    ↓
teste real
    ↓
resultado
    ↓
merge somente após validação/pedido do usuário
```

Mudanças de documentação de continuidade podem ser mantidas também no `main`, pois este arquivo precisa estar acessível para recuperação de contexto em novos chats.

### Ritmo da conversa

Não despejar muitas tarefas de uma vez.

O padrão preferido é:

```text
alteração
↓
comandos de teste
↓
usuário envia resultado
↓
análise
↓
próxima alteração
```

Quando vários comandos forem necessários para validar a mesma etapa, agrupá-los no mesmo bloco.

### Resposta após “continuar”

Quando o usuário enviar apenas:

> continuar

não pedir que ele explique novamente o projeto.

Primeiro:

1. ler este arquivo;
2. conferir GitHub/branch/PR;
3. dizer em poucas linhas onde o projeto parou;
4. continuar diretamente da próxima ação registrada.

Exemplo de abertura adequada:

> Perfeito. Retomando exatamente de onde paramos: o `main` validado está na 0.5.6 com 767 chunks após OCR, e a 0.5.7 está na branch `feature/retrieval-benchmark-0.5.7` aguardando o benchmark dense vs dense-rerank vs hybrid. Antes de alterar qualquer código, vou conferir o estado atual da branch e do PR #1.

---

## 20. Exemplo do modelo de resposta usado neste projeto

O exemplo abaixo serve como referência de estrutura, nível de detalhe e estilo. Não deve ser copiado mecanicamente; deve ser adaptado ao resultado real.

### Exemplo: usuário envia um teste bem-sucedido

Usuário:

```text
HitRate@5: 1.000 (7/7)
MRR@5: 0.821
```

Resposta esperada:

> Perfeito. Esse resultado confirma que a correção da ingestão funcionou e que agora todas as sete consultas possuem pelo menos uma fonte esperada no top 5.
>
> O ponto mais importante é separar duas coisas: antes do OCR, a Carta dos Direitos e Deveres não tinha nenhum chunk no índice. Depois do OCR, ela passou a ser recuperada em primeiro lugar. Portanto, não devemos interpretar isso apenas como uma melhora do algoritmo de retrieval; houve uma correção do próprio corpus.
>
> A nova baseline pós-correção fica:
>
> ```text
> HitRate@5 = 1.000 (7/7)
> MRR@5     = 0.821
> ```
>
> Isso também confirma a **Dificuldade TCC #8**: a falha anterior estava na ingestão, não apenas no ranking.
>
> Agora o próximo experimento precisa manter o corpus constante. Por isso vamos comparar `dense`, `dense-rerank` e `hybrid` usando exatamente os mesmos 767 chunks.
>
> A alteração já está preparada na branch:
>
> ```text
> feature/retrieval-benchmark-0.5.7
> ```
>
> Antes de considerar a 0.5.7 pronta, rode:
>
> ```cmd
> git fetch origin
> git switch --track origin/feature/retrieval-benchmark-0.5.7
> docker compose down
> docker compose up --build -d
> curl http://localhost:8000/health
> docker compose run --rm api ragtest-evaluate-retrieval
> ```
>
> Não recrie a collection nessa etapa. Os 767 chunks já estão indexados com vetores dense e sparse.
>
> Quando você enviar o resultado, vamos comparar as três estratégias antes de decidir qual fica como padrão.

### Exemplo: usuário envia um erro

Resposta esperada:

> Encontramos uma falha real nessa etapa.
>
> **Dificuldade TCC #N — descrição curta**
>
> **Planejado:** ...
>
> **Observado:** ...
>
> **Diagnóstico:** ...
>
> **Correção:** ...
>
> **Aprendizado técnico:** ...
>
> Já corrigi/preparei a alteração no GitHub, mas ainda está **aguardando validação**.
>
> Rode:
>
> ```cmd
> comando 1
> comando 2
> ```
>
> Envie o retorno completo. Só depois do teste vamos marcar essa correção como verificada.

---

## 21. Sensação de continuidade entre chats

O objetivo deste arquivo não é apenas recuperar fatos técnicos. Ele deve preservar a forma como o projeto está sendo conduzido.

Em um novo chat, o assistente deve assumir que existe uma relação de trabalho em andamento e:

- usar as mesmas nomenclaturas;
- respeitar decisões anteriores;
- lembrar por que uma arquitetura foi escolhida;
- evitar repetir perguntas já respondidas;
- não desfazer decisões sem apresentar nova evidência;
- continuar registrando experimentos e dificuldades;
- indicar claramente quando está propondo algo novo versus retomando algo já decidido;
- manter a lógica de versões incrementais;
- preservar o foco no TCC e no produto final;
- tratar os logs do usuário como a principal evidência de validação local.

Se houver conflito entre memória do chat, este documento e o estado do GitHub:

1. o estado real do GitHub e os logs de execução mais recentes prevalecem;
2. este documento deve ser atualizado;
3. não inventar uma conclusão para preencher a lacuna.


## Atualização 0.5.19 — cobertura de grounding

A 0.5.18 foi mesclada no main. A 0.5.19 inicia o fortalecimento de groundedness sem usar juiz semântico externo nesta etapa.

Implementado:

- validação determinística por bloco informativo;
- contagem de blocos citados e não citados;
- proporção de cobertura;
- self-check `ragtest-check-grounding-coverage`;
- sem alteração do endpoint `/v1/chat`;
- sem envio de conteúdo CHATSCM a LLM externo para avaliação.

Próximo passo: validar CI e executar o self-check local. Não reindexar Qdrant.


### Etapa 2 da 0.5.19 — gate de cobertura no runtime

O self-check local da cobertura estrutural passou nos quatro cenários esperados, e a CI da primeira etapa passou com Ruff verde e 77 testes.

Com base nisso, a cobertura estrutural foi promovida ao gate de geração do chat:

- toda resposta gerada passa por validação de cobertura por bloco informativo;
- cobertura completa mantém `grounded=true`;
- cobertura incompleta aciona o único retry de reparo já existente;
- se o retry continuar incompleto, retorna fallback seguro com `grounded=false`;
- nenhum juiz semântico externo foi introduzido;
- nenhuma mudança no retrieval/corpus/Qdrant.

Próximo passo: validar a nova CI e executar novamente os self-checks de grounding/cobertura. Depois, testar um chat real apenas com fonte oficial para observar o gate em runtime sem expor CHATSCM ao Gemini.


### Falha real observada e correção — Gemini 503

Na validação real da etapa 2 da 0.5.19:

- `ragtest-check-grounding`: PASS;
- `ragtest-check-grounding-coverage`: PASS;
- chat real com `--category direitos_saude --no-decompose`: falhou antes do gate com `google.genai.errors.ServerError: 503 UNAVAILABLE`, alta demanda temporária.

Registrado como Dificuldade TCC #15.

Correção implementada na mesma branch:

- retry de aplicação somente para 429/500/502/503/504;
- até 2 retries adicionais por padrão;
- backoff exponencial curto e configurável;
- erro de domínio `LLMServiceUnavailableError` após esgotamento;
- API responde HTTP 503;
- CLI mostra mensagem curta, sem traceback;
- erros não transitórios não recebem retry.

Próximo passo: aguardar CI, rebuildar e repetir exatamente o chat oficial de direitos. Não reindexar Qdrant.


### Missão secundária 0.5.19 — provider local Ollama

Ambiente local validado:

    Ollama: 0.34.2
    qwen3:4b: instalado, 2.5 GB, 100% GPU em contexto 4096
    qwen3:8b: instalado, 5.2 GB, Q4_K_M, 8.2B parâmetros
    qwen3:8b contexto 4096: 30% CPU / 70% GPU
    qwen3:8b contexto 8192: 36% CPU / 64% GPU
    Docker -> Ollama: acesso confirmado em http://host.docker.internal:11434

O qwen3:4b vazou reasoning no `message.content` mesmo com `think=false` e `/no_think`; registrado como Dificuldade #16.

O qwen3:8b respeitou `think=false` no CLI e na API e respondeu normalmente em contexto 8192. Ele passa a ser o baseline local.

D020: integração por provider explícito:

    LLM_PROVIDER=gemini
    ou
    LLM_PROVIDER=ollama

Ollama defaults:

    OLLAMA_BASE_URL=http://host.docker.internal:11434
    OLLAMA_MODEL=qwen3:8b
    OLLAMA_CONTEXT_WINDOW=8192
    OLLAMA_THINK=false
    OLLAMA_REQUEST_TIMEOUT_SECONDS=180

Sem fallback automático nesta etapa. A intenção é permitir comparação controlada do mesmo RAG entre Gemini e Qwen3 8B.

Próximo teste após CI/rebuild: definir `LLM_PROVIDER=ollama`, executar `ragtest-runtime-info --skip-qdrant` e repetir a pergunta oficial de direitos com `--category direitos_saude --no-decompose`. Não reindexar.


### Primeira validação RAG real com Qwen3 8B — aguardando diagnóstico

A validação local do provider Ollama foi executada com `LLM_PROVIDER=ollama`, `qwen3:8b`, `OLLAMA_CONTEXT_WINDOW=8192`, `OLLAMA_THINK=false` e `LLM_MAX_OUTPUT_TOKENS=4096`.

Verificado:

- `/health` retornou versão 0.5.19;
- `ragtest-runtime-info --skip-qdrant` confirmou provider/modelo/configuração esperados;
- `ragtest-check-grounding`: PASS;
- `ragtest-check-grounding-coverage`: PASS;
- o retrieval real para "Quais são os direitos da pessoa usuária da saúde?" com `--category direitos_saude --no-decompose` retornou cinco páginas da Carta oficial.

Falha observada:

- execução do chat levou aproximadamente seis minutos;
- `citation_retry_count=1`, portanto houve geração inicial + uma geração de reparo;
- ambas não produziram saída aceita pelo gate;
- resultado final: `grounded=false`, sem `citation_ids`, com fallback seguro.

Registrado como Dificuldade TCC #17.

Diagnóstico atual: retrieval e validadores determinísticos estão funcionando no cenário observado, mas o provider não expõe ainda os metadados de timing/tokenização retornados pelo Ollama nem preserva para diagnóstico as respostas rejeitadas pelo gate. A causa exata da latência e da reprovação estrutural ainda é hipótese e não deve ser tratada como corrigida.

O teste controlado seguinte alterou somente `LLM_MAX_OUTPUT_TOKENS` de 4096 para 512. O resultado manteve `citation_retry_count=1`, `grounded=false` e as mesmas cinco fontes recuperadas, mas reduziu o tempo total para 158,5 s. Isso verifica que o orçamento de saída influencia fortemente a latência, mas não explica nem corrige a reprovação do gate.

Um teste direto do `qwen3:8b` fora do RAG mediu 254 tokens em 28,68 s, com 8,94 tokens/s; o tempo de avaliação do prompt curto foi de aproximadamente 0,21 s e o de geração de saída, 28,42 s.

Instrumentação implementada na mesma branch, sem alterar o comportamento funcional:

- `OllamaProvider` passa a preservar métricas por geração: duração total/carga, tokens e duração do prompt, tokens e duração de saída, tokens/s e `done_reason`;
- o CLI passa a mostrar o diagnóstico estrutural de cada tentativa do gate: validade, sintaxe, cobertura, blocos citados/total e motivo da reprovação;
- respostas brutas rejeitadas não são persistidas nem impressas;
- CI verificada: Ruff `All checks passed!`; pytest `92 passed, 4 warnings`.

Próxima ação: atualizar/rebuildar o ambiente local e repetir a mesma pergunta com override temporário de 512 tokens para observar as novas métricas. Não reindexar Qdrant e não fazer merge do PR #13.


### Reteste do Gemini após período de 503

O mesmo chat oficial foi executado com override temporário `LLM_PROVIDER=gemini`, sem alterar o `.env`.

Resultado observado:

- o Gemini recebeu um erro transitório 503 na primeira tentativa;
- o retry de aplicação entrou em ação após 1 segundo;
- a chamada subsequente conseguiu prosseguir;
- o retrieval retornou as mesmas cinco páginas da Carta oficial;
- o chat terminou com `grounded=false`, `citation_retry_count=1` e sem `citation_ids`.

Conclusão atual:

- o Gemini está novamente acessível, mas ainda apresenta oscilação transitória;
- o retry da Dificuldade #15 funcionou no cenário real;
- como Gemini e Qwen3 8B chegaram ao mesmo fallback estrutural, a investigação do grounding passa a priorizar o contrato compartilhado de prompt/gate, não um provider específico;
- registrado como Dificuldade TCC #18;
- Gemini pode voltar a ser o provider principal de desenvolvimento, com Ollama como contingência manual; fallback automático continua fora do escopo desta etapa para preservar rastreabilidade.

Próxima ação: atualizar/rebuildar a imagem com a instrumentação já implementada e repetir o mesmo teste com Gemini para capturar `Citation validation attempts`. Não reindexar Qdrant e não fazer merge do PR #13.


### Diagnóstico do gate após instrumentação — heading Markdown e repair direcionado

O reteste real com Gemini usando a instrumentação mostrou:

    tentativa 1: syntax=yes, coverage=0.786, blocks=22/28
    tentativa 2: syntax=yes, coverage=0.767, blocks=23/30
    resultado: grounded=false, citation_retry_count=1

A investigação encontrou dois pontos no contrato compartilhado do gate:

1. headings Markdown como `## Direitos da pessoa usuária` eram tratados como claim blocks quando não terminavam em dois-pontos;
2. o chamado "repair" não recebia a resposta anterior nem o motivo específico da falha e, portanto, regenerava do zero.

Registrado como Dificuldade TCC #19.

Correção implementada e verificada em CI (`All checks passed!`; `94 passed, 4 warnings`), aguardando validação real:

- headings Markdown iniciados por `#` não contam como afirmação informativa;
- parágrafos e itens continuam exigindo citações válidas;
- o retry recebe a resposta anterior e o motivo da validação;
- o modelo é instruído a revisar a resposta existente sem acrescentar novas afirmações;
- testes adicionados para os dois comportamentos.

Próxima ação: aguardar CI, rebuildar e repetir exatamente o chat oficial com Gemini. Não reindexar Qdrant e não fazer merge do PR #13.


### Nova oscilação do Gemini — 429 após retries

Após o rebuild com a correção do gate, duas execuções do chat oficial com `LLM_PROVIDER=gemini` não chegaram à geração: ambas receberam `429` na chamada inicial e nos dois retries configurados (1 s e 2 s), terminando com `LLMServiceUnavailableError`.

Isso não invalida a correção do gate; o teste real dessa correção continua pendente porque o provider externo não chegou a produzir resposta. A Dificuldade #15 foi atualizada para registrar que a indisponibilidade do Gemini agora também se manifesta como rate limit/cota, além do 503 já observado.

Próxima decisão: avaliar um terceiro provider de desenvolvimento/fallback manual sem alterar corpus, retrieval ou Qdrant. O Ollama continua disponível localmente; nenhum fallback automático foi habilitado.


### Integração Groq / GPT-OSS 120B

Após novas falhas 429 do Gemini, foi iniciada a integração de um terceiro provider explícito para desenvolvimento e contingência manual:

    LLM_PROVIDER=groq
    GROQ_MODEL=openai/gpt-oss-120b
    GROQ_BASE_URL=https://api.groq.com/openai/v1
    GROQ_REASONING_EFFORT=low

A integração preserva a interface `LLMProvider`, corpus, retrieval, Qdrant e gate de grounding. Não existe fallback automático nesta etapa.

Características implementadas:

- API OpenAI-compatible da Groq via HTTP, sem nova dependência Python;
- `include_reasoning=false` para não expor reasoning;
- citações nativas da Groq desabilitadas para preservar o contrato `[n]` do RagTest;
- retry limitado para 429/498/500/502/503/504;
- respeito a `Retry-After` com espera limitada;
- métricas de prompt/output e latência expostas ao CLI;
- chave somente via `GROQ_API_KEY` no ambiente;
- runtime-info identifica provider/modelo/configuração.

D021 registra a decisão. A validação real deve usar somente a categoria oficial `direitos_saude`; CHATSCM continua proibido em providers externos antes de revisão manual de privacidade.

CI da integração Groq verificada: Ruff `All checks passed!`; pytest `101 passed, 4 warnings`. Próximo passo: adicionar a chave Groq somente no `.env` local, rebuildar e testar primeiro o `runtime-info` e depois o chat RAG oficial. Não reindexar Qdrant.


### Primeira validação real da Groq — Cloudflare 1010

O `runtime-info` confirmou corretamente:

    llm_provider: groq
    llm_model: openai/gpt-oss-120b
    groq_base_url: https://api.groq.com/openai/v1
    groq_reasoning_effort: low

As duas primeiras chamadas reais ao chat falharam antes da geração com `HTTP 403` e `error code: 1010`. O traceback mostrou o bloqueio em `urllib.request.urlopen`.

Diagnóstico: Cloudflare 1010 indica bloqueio por assinatura do cliente HTTP. O provider usava o `User-Agent` padrão do `urllib`, portanto o erro não prova chave inválida e não chegou ao modelo. Registrado como Dificuldade TCC #20.

Correção implementada:

- `GroqProvider` envia `Accept: application/json`;
- envia `User-Agent: Mozilla/5.0 (compatible; RagTest/0.5.19)`;
- teste de regressão exige `User-Agent` explícito;
- nenhuma alteração em corpus, retrieval, Qdrant, prompt ou modelo.

CI da correção verificada: Ruff verde; pytest `102 passed, 4 warnings`. Próxima ação: rebuildar a imagem e repetir apenas o teste curto Groq com 512 tokens. Se ele chegar ao modelo, então executar a pergunta completa. Não reindexar Qdrant.


### Groq chegou ao GPT-OSS 120B — transporte validado, citações pendentes

Após a correção do User-Agent, o teste curto com `LLM_PROVIDER=groq`, `openai/gpt-oss-120b`, duas fontes oficiais e 512 tokens chegou ao modelo com sucesso.

Resultado:

    geração 1: 1,12 s | 512 tokens | ~478,05 tok/s | done_reason=length
    geração 2: 0,94 s | 409 tokens | ~478,22 tok/s | done_reason=stop
    citation validation 1: syntax=no | coverage=0.000 | 0/9
    citation validation 2: syntax=no | coverage=0.000 | 0/9
    grounded=false

A Dificuldade #20 fica validada como corrigida em runtime: o 403/1010 desapareceu.

Nova Dificuldade #21: o GPT-OSS 120B não produziu nenhuma citação literal `[n]` em nenhuma das duas tentativas. Como o repair terminou por `stop`, a falha não pode ser atribuída somente ao teto de 512 tokens.

Próxima ação: executar uma chamada direta mínima ao `GroqProvider`, sem retrieval, solicitando explicitamente uma frase com `[1]`. Não alterar prompt/gate antes desse isolamento. Não reindexar Qdrant.


### Teste literal de citação no GPT-OSS 120B

Uma chamada direta ao `GroqProvider`, sem retrieval e com `LLM_MAX_OUTPUT_TOKENS=256`, solicitou exatamente:

    Direito teste [1].

O modelo retornou exatamente essa frase, incluindo `[1]`.

Conclusão: o GPT-OSS 120B e o `GroqProvider` conseguem obedecer ao formato literal de citação. A Dificuldade #21 fica restrita ao caminho RAG completo; não há evidência para trocar o provider nem para afrouxar o gate.

Próxima ação: capturar uma geração RAG bruta antes da validação, usando somente a categoria oficial `direitos_saude`, para observar o efeito do prompt/contexto. Não reindexar Qdrant.


### Causa da falha de citações do GPT-OSS isolada — variante Unicode

A geração RAG bruta do GPT-OSS 120B revelou que o modelo estava citando as fontes, mas emitia:

    【1】
    【2】

em vez do formato canônico:

    [1]
    [2]

Isso explica por que o gate reportava `syntax=no`, `coverage=0.000` e 0 blocos citados apesar de a resposta visualmente conter referências válidas.

Correção implementada:

- normalização estrita `【n】 -> [n]`;
- aplicada imediatamente após a geração inicial e após o repair;
- `extract_citation_ids` também reconhece a variante por normalização;
- IDs continuam obrigados a estar dentro do intervalo de fontes;
- blocos informativos continuam exigindo citação;
- resposta final usa o formato canônico ASCII;
- testes reproduzem o caso do GPT-OSS.

CI verificada: Ruff `All checks passed!`; pytest `105 passed, 4 warnings`.

Próxima ação: rebuildar e repetir o chat oficial curto com Groq usando 1024 tokens. A correção ainda precisa de validação real antes de marcar a Dificuldade #21 como resolvida em runtime. Não reindexar Qdrant.


### Dificuldade #22 — introdução estrutural de lista no gate

Após a normalização `【n】 -> [n]`, o reteste real com Groq avançou para:

    syntax=yes
    coverage=0.889
    blocks=8/9
    done_reason=stop nas duas gerações

A regressão reproduziu a causa: uma introdução longa terminada em dois-pontos antes de uma lista citada era contada como claim independente.

Correção implementada:

- uma linha terminada em `:` só é tratada como introdução estrutural quando o próximo bloco não vazio é um item real de lista;
- os itens continuam obrigados a conter citações válidas;
- demais frases informativas continuam sujeitas ao gate;
- CI verificada: Ruff `All checks passed!`; pytest `106 passed, 4 warnings`.

Próxima ação: rebuildar e repetir exatamente o mesmo chat curto com Groq e 1024 tokens. Não reindexar Qdrant.


### Reteste após correção da introdução de lista

O chat curto com Groq/GPT-OSS 120B e 1024 tokens foi repetido após a correção contextual da introdução de lista.

Resultado real permaneceu:

    tentativa 1: syntax=yes | coverage=0.889 | blocks=8/9
    tentativa 2: syntax=yes | coverage=0.889 | blocks=8/9
    grounded=false
    done_reason=stop nas duas gerações

Conclusão: a regra de introdução de lista está coberta por teste e CI, mas não explica sozinha o bloco uncited do caso real. A Dificuldade #22 continua aberta em runtime.

Próxima ação: capturar novamente a resposta RAG bruta e comparar linha a linha com a classificação do gate para identificar exatamente qual bloco está sendo contado como uncited. Não alterar o gate até essa identificação.


### Dificuldade #23 — repair agora recebe o bloco uncited exato

O diagnóstico linha a linha isolou o bloco real que causava `8/9`:

    Esses direitos são extraídos dos documentos citados e refletem as garantias previstas para as pessoas usuárias dos serviços de saúde.

A introdução da lista estava corretamente classificada como estrutural, e os dez itens estavam citados. Portanto, a hipótese anterior de que a introdução explicava o caso real foi descartada.

Problema identificado: o repair recebia apenas um motivo genérico de cobertura incompleta, sem o texto do bloco que precisava ser corrigido.

Correção implementada:

- `CitationCoverage` preserva `uncited_blocks`;
- o repair recebe uma seção `BLOCOS SEM CITAÇÃO VÁLIDA`;
- o modelo deve citar o bloco somente se houver fonte que o sustente ou removê-lo se for desnecessário;
- nenhuma regra do gate foi relaxada;
- TDD confirmado: os novos testes falharam antes da implementação;
- CI após implementação: Ruff `All checks passed!`; pytest `106 passed, 4 warnings`.

Próxima ação: rebuildar e repetir exatamente o mesmo chat curto com Groq e 1024 tokens. O resultado esperado é primeira tentativa possivelmente 8/9 e segunda tentativa 100%, ou primeira tentativa já 100% se a geração variar. Não reindexar Qdrant.


### Pós-processamento determinístico após repair — D022 / Dificuldade #24

O reteste real do repair localizado ainda retornou:

    tentativa 1: syntax=yes | coverage=0.889 | blocks=8/9
    tentativa 2: syntax=yes | coverage=0.889 | blocks=8/9
    done_reason=stop nas duas gerações

Como o bloco uncited já era explicitamente enviado ao repair, a estratégia baseada apenas em prompting foi considerada insuficiente.

Implementação atual:

1. geração inicial;
2. validação estrutural;
3. um único repair com blocos uncited explícitos;
4. nova validação;
5. se a sintaxe estiver válida, houver pelo menos um claim citado e restarem claims sem citação, remover deterministicamente apenas esses claims;
6. revalidar;
7. aceitar somente se a cobertura final for 100%; caso contrário, fallback seguro.

O CLI passa a mostrar:

    stage=initial
    stage=repair
    stage=postprocess

`citation_retry_count` continua contando somente retries de LLM, portanto permanece 1 quando o postprocess é usado.

TDD confirmado e CI verificada: Ruff `All checks passed!`; pytest `108 passed, 3 warnings`.

Próxima ação: rebuildar e repetir o mesmo chat curto com Groq e 1024 tokens. O resultado esperado, caso o modelo repita o padrão observado, é initial 8/9, repair 8/9, postprocess 100% e `Grounded: yes`. Não reindexar Qdrant.


### Groq/GPT-OSS 120B — grounding estrutural validado em runtime

O reteste após a D022 confirmou o fluxo completo:

    Grounded: yes
    Citation ids: [1, 2]
    Citation retries: 1

    [1] stage=initial     valid=no  syntax=yes coverage=0.889 blocks=8/9
    [2] stage=repair      valid=no  syntax=yes coverage=0.889 blocks=8/9
    [3] stage=postprocess valid=yes syntax=yes coverage=1.000 blocks=8/8

Métricas observadas:

    geração inicial: 1,14 s | 516 tokens | ~476,58 tok/s | stop
    repair:          1,63 s | 488 tokens | ~316,53 tok/s | stop

A resposta final manteve apenas os oito blocos citados e removeu o claim final sem fonte.

Status:

- `GroqProvider`: verificado em runtime;
- `openai/gpt-oss-120b`: verificado para geração RAG oficial;
- normalização `【n】 -> [n]`: verificada em runtime;
- repair localizado: implementado, mas insuficiente sozinho no caso observado;
- pós-processamento determinístico D022: verificado em runtime;
- grounding estrutural final: verificado com `coverage=1.000`;
- grounding semântico/entailment de cada claim para a fonte citada: ainda não verificado automaticamente.

O Groq pode ser usado como provider principal de desenvolvimento enquanto o Gemini estiver limitado, mantendo a seleção explícita e sem fallback automático. CHATSCM continua proibido em providers externos antes da revisão manual de privacidade.


### D023 — otimização de cota validada em CI

Três testes reais com fontes oficiais distintas passaram com grounded=true: direitos_saude, vacinacao/idoso e gestacao/saude bucal. Nos três houve citation_retry_count=1.

Foi implementado postprocess antes do repair apenas quando a resposta inicial tem sintaxe válida, exatamente um claim sem citação, pelo menos um claim citado e cobertura >= 0,80. A poda é aceita somente após revalidação em 100%; caso contrário, o repair normal continua.

TDD confirmado: o novo teste falhou primeiro com duas chamadas ao LLM. Após a implementação, CI verde com 109 testes aprovados e 4 warnings.

Próxima ação: rebuildar e repetir um único teste real com Groq. Esperado no padrão conhecido: grounded=true e citation_retry_count=0. Não reindexar Qdrant.


### D023 — validação real concluída

O reteste real de direitos_saude após a otimização observou:

    grounded=true
    citation_ids=[1,2]
    citation_retry_count=0

A resposta final manteve os oito direitos citados e não precisou de uma segunda geração Groq. Isso confirma a execução sem repair externo, mas o JSON da API não expõe citation_validation_attempts; portanto, não distingue se a geração inicial já estava totalmente válida ou se o postprocess-before-repair foi acionado. A lógica da D023 permanece verificada por TDD/CI; o caminho interno específico ainda não foi observado diretamente em runtime.

Status da 0.5.19: grounding estrutural, normalização de citações, repair localizado, postprocess determinístico e otimização de cota estão implementados e verificados em CI; os fluxos principais foram validados em runtime com fontes oficiais de direitos_saude, vacinacao/idoso e gestacao/saude bucal. Grounding semântico/entailment automático continua fora do escopo validado desta versão.
