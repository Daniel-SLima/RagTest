# RagTest

Backend modular para experimentar e evoluir um fluxo **RAG (Retrieval-Augmented Generation)** reutilizável por Flutter, React Native, Web ou outros sistemas via API.

## Fase atual — 0.3 Retrieval vetorial

Já estão implementados:

- FastAPI e health checks;
- Qdrant em Docker;
- leitura recursiva de PDF e DOCX;
- chunking com LangChain;
- metadados por chunk;
- embeddings locais com FastEmbed;
- modelo multilíngue adequado para consultas em português;
- IDs determinísticos para reindexar sem duplicar o mesmo chunk;
- persistência do cache do modelo em volume Docker;
- indexação dos chunks no Qdrant;
- busca semântica por CLI;
- filtro opcional por categoria;
- endpoint REST `POST /v1/search`;
- testes automatizados.

## Fluxo

```text
PDF / DOCX
    |
    v
 loaders
    |
    v
LangChain Documents
    |
    v
chunking
    |
    v
FastEmbed
    |
    v
Qdrant
    |
    +---- CLI search
    |
    +---- POST /v1/search
    |
    v
próxima fase: prompt + LLM -> POST /v1/chat
```

## Atualizar e subir no Windows CMD

```cmd
git pull origin main
docker compose down
docker compose up --build -d
```

Teste:

```cmd
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Indexar os documentos

Na primeira execução o modelo de embeddings será baixado e guardado no volume `fastembed_cache`.

```cmd
docker compose run --rm api ragtest-ingest
```

Para apagar e recriar a collection:

```cmd
docker compose run --rm api ragtest-ingest --recreate
```

Com os 18 documentos atuais, o pipeline deve indexar os mesmos chunks encontrados por `ragtest-inspect`.

## Primeira busca semântica

Depois da ingestão:

```cmd
docker compose run --rm api ragtest-search "Quais vacinas são recomendadas para idosos?"
```

Com filtro:

```cmd
docker compose run --rm api ragtest-search "Quais vacinas são recomendadas?" --category vacinacao --limit 5
```

A busca retorna score, arquivo, página (quando disponível) e um trecho do chunk.

## API de retrieval

```http
POST /v1/search
Content-Type: application/json
```

Exemplo:

```json
{
  "query": "Quais vacinas são recomendadas para idosos?",
  "limit": 5,
  "category": "vacinacao"
}
```

A resposta já possui os elementos que outro aplicativo precisa consumir:

```json
{
  "query": "Quais vacinas são recomendadas para idosos?",
  "results": [
    {
      "score": 0.82,
      "content": "...",
      "source": "vacinacao/calendario_nacional_vacinacao_idoso.pdf",
      "category": "vacinacao",
      "page": 1,
      "metadata": {}
    }
  ]
}
```

Swagger: `http://localhost:8000/docs`

## Por que FastEmbed nesta fase?

O provider inicial roda localmente em ONNX, sem exigir chave de API. A aplicação usa uma interface `EmbeddingProvider`, então outro provider pode ser adicionado depois sem alterar o restante do pipeline.

Modelo padrão:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

## Reindexação

Cada chunk recebe um UUID determinístico baseado em origem, página, posição e conteúdo. Rodar a ingestão novamente não cria uma segunda cópia do mesmo chunk.

Se trocar de modelo de embeddings, use:

```cmd
docker compose run --rm api ragtest-ingest --recreate
```

## Próxima fase — 0.4 Chat RAG

1. recuperar os melhores chunks;
2. montar prompt com contexto e regras de citação;
3. abstrair o provider de LLM;
4. criar `POST /v1/chat`;
5. retornar resposta + fontes;
6. adicionar avaliação para detectar respostas sem suporte documental.

## Segurança

Não versione nem indexe documentos com dados pessoais ou clínicos identificáveis. Use materiais públicos, sintéticos ou anonimizados.
