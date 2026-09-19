# Contexto de Continuidade do Projeto — RagTest / Se Cuida Mulher

> **Documento vivo de continuidade.**
>
> Este arquivo existe para permitir que o desenvolvimento continue em outro chat sem perda de contexto.
> **Sempre que houver mudança relevante de código, arquitetura, testes, métricas, decisões, dificuldades ou próximos passos, este arquivo deve ser atualizado antes de encerrar a tarefa.**
>
> Em um novo chat, antes de continuar o projeto, leia este arquivo e depois confira o estado atual do repositório/branch/PR.

**Última atualização:** 2026-09-19  
**Repositório:** `Daniel-SLima/RagTest`  
**Branch padrão:** `main`  
**Estado testado no main:** `0.5.6`  
**Trabalho em andamento:** `0.5.7` em branch separada, ainda não mesclada.

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

Configuração recomendada/atual:

```env
PDF_OCR_ENABLED=true
PDF_OCR_LANGUAGE=por
PDF_OCR_DPI=200
PDF_OCR_TIMEOUT_SECONDS=60

SPARSE_EMBEDDING_PROVIDER=fastembed_bm25
SPARSE_EMBEDDING_MODEL=Qdrant/bm25
SPARSE_EMBEDDING_LANGUAGE=portuguese

HYBRID_DENSE_WEIGHT=1.0
HYBRID_SPARSE_WEIGHT=1.0

RETRIEVAL_CANDIDATE_MULTIPLIER=8
RETRIEVAL_SCORE_MARGIN=0.0
RETRIEVAL_MERGE_SAME_PAGE=true
RETRIEVAL_MAX_GROUP_CHARS=5000
RETRIEVAL_SOURCE_LEXICAL_WEIGHT=0.25
RETRIEVAL_CONTENT_LEXICAL_WEIGHT=0.05

LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.6-flash
LLM_TEMPERATURE=0.1
```

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
8. fonte esperada tinha zero texto e zero chunks.

**Regra:** quando algo planejado não funcionar como esperado, criar uma nova “Dificuldade TCC #N” com:

- planejado;
- observado;
- diagnóstico;
- correção;
- aprendizado para a monografia.

---

## 11. O que está sendo feito agora

### Fase 0.5.7 — benchmark comparativo justo

Objetivo:

Comparar estratégias de retrieval usando **exatamente o mesmo corpus corrigido de 767 chunks**, para separar:

- efeito da correção de ingestão/OCR;
- efeito da estratégia de retrieval.

### Branch ativa

`feature/retrieval-benchmark-0.5.7`

### Commit atual da branch

`cc0f9d865b72f8c77d6185c54e3e9cbe0d5497c9`

### Pull Request

**PR #1 — Draft**

`Benchmark comparativo de retrieval no corpus corrigido`

Ainda **não fazer merge** antes da validação.

### Perfis implementados na 0.5.7

- `dense`
- `dense-rerank`
- `hybrid`

O comando:

```cmd
docker compose run --rm api ragtest-evaluate-retrieval
```

passa a executar os três perfis no mesmo corpus e imprimir um resumo comparativo.

Também podem ser executados isoladamente:

```cmd
docker compose run --rm api ragtest-evaluate-retrieval --mode dense
docker compose run --rm api ragtest-evaluate-retrieval --mode dense-rerank
docker compose run --rm api ragtest-evaluate-retrieval --mode hybrid
```

---

## 12. Ponto exato onde o trabalho foi pausado

O usuário decidiu pausar **antes de testar a 0.5.7**.

O ambiente local testado continua em **0.5.6**, com a collection já recriada e contendo **767 chunks dense + sparse**.

A branch 0.5.7 já existe no GitHub e o PR #1 está aberto como draft.

Ao receber a palavra **“continuar”**, a próxima ação deve ser:

1. ler este arquivo;
2. conferir o estado do PR #1 e da branch `feature/retrieval-benchmark-0.5.7`;
3. orientar o usuário a entrar nessa branch;
4. subir a imagem 0.5.7;
5. rodar o benchmark comparativo.

Não recriar a collection antes do benchmark, porque os 767 chunks atuais já possuem dense + sparse.

---

## 13. Próximos 5 passos

### Passo 1 — testar a 0.5.7

No Windows CMD:

```cmd
git fetch origin
git switch --track origin/feature/retrieval-benchmark-0.5.7
docker compose down
docker compose up --build -d
curl http://localhost:8000/health
docker compose run --rm api ragtest-evaluate-retrieval
```

Resultado esperado: tabela final com HitRate@5 e MRR@5 para:

- dense;
- dense-rerank;
- hybrid.

### Passo 2 — escolher a estratégia de retrieval

Comparar os três perfis usando o mesmo corpus.

Não escolher por complexidade ou preferência subjetiva: usar métricas + inspeção qualitativa dos resultados.

Se houver regressão ou trade-off relevante, registrar nova Dificuldade TCC.

### Passo 3 — consolidar a fase 0.5

Depois de escolher a estratégia:

- ajustar configuração padrão;
- atualizar documentação;
- validar busca e chat;
- executar testes;
- somente depois decidir se o PR #1 pode ser finalizado/mesclado.

### Passo 4 — reforçar groundedness e segurança

Depois da qualidade de retrieval:

- validar programaticamente citações `[n]`;
- impedir citações inexistentes;
- remover score interno do contexto enviado ao LLM;
- adicionar defesa contra prompt injection em documentos recuperados;
- mapear melhor erros do provider Gemini;
- revisar privacidade dos CHATSCM antes de uso externo.

### Passo 5 — preparar camada de produto

Com RAG estável:

- logs/auditoria estruturada;
- sessões e histórico;
- streaming;
- integração REST/WebSocket;
- integração final com o aplicativo Se Cuida Mulher;
- interface de chat, rich text, links e gatilhos de serviços/lembretes.

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
- conjunto de avaliação com 7 perguntas ainda é pequeno e deve crescer antes da conclusão acadêmica.

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
- `docs/avaliacao-retrieval.md` — histórico de métricas e experimentos;
- `README.md` — uso e estado funcional do projeto.

---

## 18. Resumo de retomada rápida

```text
Projeto: RagTest / Se Cuida Mulher
Main testado: 0.5.6
Corpus: 18 arquivos / 767 chunks após OCR
Qdrant: dense + sparse
Dense: paraphrase-multilingual-MiniLM-L12-v2
Sparse: Qdrant/bm25 português
LLM: Gemini 3.6 Flash
OCR: Tesseract local, seletivo
Baseline pós-OCR híbrida: HitRate@5=1.000 / MRR@5=0.821

Em andamento:
0.5.7 benchmark comparativo

Branch:
feature/retrieval-benchmark-0.5.7

PR:
#1 draft

Pausado antes de:
rodar ragtest-evaluate-retrieval na 0.5.7

Próxima ação ao receber "continuar":
testar dense vs dense-rerank vs hybrid no mesmo corpus de 767 chunks.
```
