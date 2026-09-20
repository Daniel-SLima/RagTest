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
**Estado validado e mesclado no main:** `0.5.9`  
**Trabalho em andamento:** `0.5.10` em `feature/source-metrics-0.5.10`; métricas source-level validadas em runtime. PR #4 aguarda autorização de merge.

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
9. retrieval híbrido não superou dense-rerank no mesmo corpus.

**Regra:** quando algo planejado não funcionar como esperado, criar uma nova “Dificuldade TCC #N” com:

- planejado;
- observado;
- diagnóstico;
- correção;
- aprendizado para a monografia.

---

## 11. O que está sendo feito agora

### Fase 0.5.10 — métricas source-level

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

### Passo 3 — preparar relevância preferencial

Definir, em uma fase separada e documentada, como distinguir fonte aceitável de fonte preferencial sem reescrever retroativamente o holdout original.

### Passo 4 — reforçar groundedness e segurança

Validar citações, remover scores internos do prompt, adicionar defesa contra prompt injection documental e revisar a privacidade dos arquivos CHATSCM antes de chamadas externas.

### Passo 5 — preparar a camada de produto

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
Main validado/mesclado: 0.5.9
Corpus: 18 arquivos / 767 chunks após OCR
Qdrant: dense + sparse
Dense: paraphrase-multilingual-MiniLM-L12-v2
Sparse: Qdrant/bm25 português
LLM: Gemini 3.6 Flash
OCR: Tesseract local, seletivo
Baseline pós-OCR híbrida: HitRate@5=1.000 / MRR@5=0.821

Em andamento:
0.5.10 métricas source-level

Branch:
feature/source-metrics-0.5.10

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
0.5.10 validada em runtime. Holdout manteve as métricas históricas e adicionou: dense SourceRecall@5=1.000 / SourceNDCG@5=0.917; dense-rerank 1.000 / 0.941; hybrid 0.967 / 0.885. Suite dev: dense 1.000 / 0.903; dense-rerank 1.000 / 0.936; hybrid 1.000 / 0.869.

Próxima ação ao receber "continuar":
confirmar o estado do PR #4 e, se houver autorização do usuário, mesclar a 0.5.10. Os testes unitários adicionados ainda não foram executados em CI/container de desenvolvimento; não afirmar que passaram.
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

Aprendizado para o TCC:
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
> **Aprendizado para o TCC:** ...
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
