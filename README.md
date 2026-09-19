# RagTest

Backend modular para experimentar e evoluir um fluxo **RAG (Retrieval-Augmented Generation)** que possa ser usado neste ambiente de homologação e integrado a outros aplicativos via API.

## Fase atual — 0.1 Foundation

A fundação contém FastAPI, Qdrant, configuração por ambiente, Docker Compose, health checks, testes automatizados e CI. Os documentos em `data/source/` são montados no container como volume somente leitura.

A ingestão, embeddings, LangChain e o endpoint de chat entram na próxima etapa.

## Arquitetura

```text
Flutter / React Native / Web / sistema existente
                    |
                    | HTTP / futuro WebSocket
                    v
              FastAPI (RagTest)
                    |
             pipeline RAG
                    |
           +--------+--------+
           |                 |
        Qdrant          provedor LLM
```

O RAG fica desacoplado do frontend. Outro sistema precisa apenas conhecer o contrato HTTP do módulo.

## Executar com Docker

Opcionalmente:

```powershell
Copy-Item .env.example .env
```

Suba tudo:

```bash
docker compose up --build
```

Acesse:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Qdrant: `http://localhost:6333`

## Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

`/health` verifica se a API está viva. `/ready` também verifica a conectividade com o Qdrant.

## Executar sem Docker

Requer Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:QDRANT_URL="http://localhost:6333"
uvicorn app.main:app --reload
```

## Testes

```bash
pytest
ruff check .
```

Os testes unitários de readiness simulam o Qdrant e não dependem de um banco externo em execução.

## Próximas etapas

1. loader recursivo para PDF e DOCX;
2. metadados por documento/chunk;
3. chunking configurável;
4. embeddings;
5. criação e atualização da collection no Qdrant;
6. LangChain para retrieval → prompt → LLM;
7. `POST /v1/chat` com resposta e fontes;
8. testes de avaliação do retrieval;
9. contrato de integração para Flutter/React Native e outros sistemas.

## Segurança dos documentos

Não versione arquivos contendo dados clínicos ou pessoais identificáveis. Para testes, use documentos públicos, sintéticos ou previamente anonimizados.
