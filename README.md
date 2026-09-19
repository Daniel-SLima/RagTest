# RagTest

Módulo RAG reutilizável via API para Flutter, React Native, Web e outros sistemas.

## Fase atual — 0.4 Chat RAG

Pipeline funcional:

```text
PDF/DOCX
  -> loader
  -> chunking (LangChain)
  -> embeddings locais (FastEmbed)
  -> Qdrant
  -> retrieval semântico + filtros
  -> prompt grounded
  -> Gemini
  -> resposta + fontes
```

## O que já funciona

- FastAPI;
- Qdrant em Docker;
- ingestão de PDF/DOCX;
- 699 chunks para a base de teste atual;
- embeddings multilíngues;
- busca semântica;
- metadados de origem, categoria, página e público;
- filtro por `category` e `audience`;
- LangChain para chunking e montagem de prompt;
- provider de LLM desacoplado;
- Gemini como primeiro provider;
- `POST /v1/search`;
- `POST /v1/chat`;
- resposta estruturada com fontes;
- testes automatizados.

## Segurança da chave

Nunca versione a chave do Gemini. Crie um arquivo local `.env`, que já está ignorado pelo Git:

```env
GEMINI_API_KEY=SUA_NOVA_CHAVE
```

Se uma chave tiver sido publicada em chat, commit, print ou outro local, revogue-a e gere outra antes de usar.

## Atualizar no Windows CMD

```cmd
git pull origin main
docker compose down
docker compose up --build -d
```

Confira:

```cmd
curl http://localhost:8000/health
curl http://localhost:8000/ready
docker compose ps
```

Swagger:

```text
http://localhost:8000/docs
```

## Reindexar com o novo metadado de público

A fase 0.4 adiciona o metadado `audience`. Portanto, depois de atualizar, recrie a collection:

```cmd
docker compose run --rm api ragtest-ingest --recreate
```

Exemplos de público:

- `idoso`
- `gestante`
- `crianca`
- `adolescente_jovem`
- `adulto`

## Testar retrieval

Sem filtro:

```cmd
docker compose run --rm api ragtest-search "Quais vacinas são recomendadas para idosos?"
```

Com filtro de público:

```cmd
docker compose run --rm api ragtest-search "Quais vacinas são recomendadas para idosos?" --audience idoso --limit 5
```

Você também pode combinar filtros:

```cmd
docker compose run --rm api ragtest-search "Quais vacinas são recomendadas para idosos?" --category vacinacao --audience idoso --limit 5
```

## Testar o chat RAG

Com uma nova chave configurada em `.env`:

```cmd
docker compose run --rm api ragtest-chat "Quais vacinas são recomendadas para idosos?" --audience idoso
```

O modelo recebe apenas os trechos recuperados e é instruído a citar `[1]`, `[2]`, etc.

## API do chat

```http
POST /v1/chat
Content-Type: application/json
```

Exemplo:

```json
{
  "message": "Quais vacinas são recomendadas para idosos?",
  "limit": 5,
  "audience": "idoso"
}
```

Resposta:

```json
{
  "answer": "De acordo com os documentos recuperados... [1]",
  "model": "gemini-2.5-flash",
  "sources": [
    {
      "citation_id": 1,
      "score": 0.74,
      "source": "pessoa_idosa/caderneta_saude_pessoa_idosa_5ed_1re.pdf",
      "category": "pessoa_idosa",
      "audience": "idoso",
      "page": 34,
      "excerpt": "..."
    }
  ]
}
```

## Integração com outro aplicativo

O cliente não precisa conhecer FastEmbed, Qdrant ou Gemini. Ele consome apenas a API:

```text
Aplicativo existente
      |
      | POST /v1/chat
      v
RagTest API
      |
      +-- retrieval
      +-- LLM
      +-- fontes
```

Isso permite trocar o frontend ou o provider de IA sem reescrever o pipeline inteiro.

## Próximas etapas

- histórico de conversa desacoplado;
- WebSocket/streaming;
- avaliação automática do retrieval;
- reranking e busca híbrida;
- autenticação da API;
- empacotamento/documentação para integração em outro projeto.
