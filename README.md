# RagTest

Backend modular para experimentar e evoluir um fluxo **RAG (Retrieval-Augmented Generation)** reutilizável por Flutter, React Native, Web ou outros sistemas via API.

## Fase atual — 0.2 Document pipeline

Já estão implementados:

- FastAPI e health checks;
- Qdrant como serviço vetorial;
- Docker e Docker Compose;
- configuração por ambiente;
- descoberta recursiva de PDF e DOCX;
- extração de texto;
- metadados de origem, categoria, tipo de arquivo e página para PDFs;
- chunking com LangChain, overlap e `start_index`;
- comando de inspeção dos documentos sem imprimir o conteúdo;
- testes automatizados e CI.

## Fluxo atual

```text
data/source/**/*.pdf|docx
          |
          v
      loaders
          |
          v
LangChain Documents + metadados
          |
          v
RecursiveCharacterTextSplitter
          |
          v
       chunks
          |
          v
   próxima etapa:
embeddings -> Qdrant -> retrieval -> LLM
```

## Executar

```powershell
git pull origin main
Copy-Item .env.example .env
docker compose up --build
```

Swagger: `http://localhost:8000/docs`

Health:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Inspecionar a base documental

Depois de instalar o projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
ragtest-inspect
```

Ou:

```bash
python -m app.cli.inspect_documents
```

O comando mostra quantidade de arquivos, unidades carregadas, chunks, categorias e erros de leitura. Ele não imprime o texto dos documentos.

Configurações principais:

```env
SOURCE_DIR=data/source
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Metadados

Exemplo de um chunk vindo de PDF:

```json
{
  "source": "vacinacao/calendario_nacional_vacinacao_idoso.pdf",
  "filename": "calendario_nacional_vacinacao_idoso.pdf",
  "category": "vacinacao",
  "file_type": "pdf",
  "page": 1,
  "start_index": 0
}
```

Esses metadados serão enviados ao Qdrant e depois retornados como fontes nas respostas do chat.

## Próxima etapa

A fase 0.3 implementará:

1. interface de embeddings desacoplada;
2. provider inicial configurável;
3. collection do Qdrant;
4. IDs determinísticos para evitar duplicação na reindexação;
5. comando de ingestão;
6. busca semântica com filtros por metadados;
7. testes de integração do índice.

Depois conectaremos o retrieval ao LLM e criaremos `POST /v1/chat`.

## Segurança

Não versione nem indexe documentos com dados pessoais ou clínicos identificáveis. Use materiais públicos, sintéticos ou anonimizados.
