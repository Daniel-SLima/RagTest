# RagTest

Módulo RAG reutilizável via API.

## Fase 0.5.3 — Retrieval híbrido

A 0.5.2 melhorou o MRR de 0.714 para 0.786, mas não aumentou o HitRate@5. O motivo provável é recall: reranking não recupera documentos ausentes do conjunto inicial.

A 0.5.3 combina:

    Dense multilingual embedding
            +
    BM25 em português
            |
            v
      Reciprocal Rank Fusion
            |
            v
    agrupamento + reranking
            |
            v
          Gemini

Baseline registrada em docs/avaliacao-retrieval.md.

### Atualização obrigatória da collection

O schema do Qdrant mudou de um vetor denso único para vetores nomeados dense + sparse. Por isso esta versão exige uma reindexação única:

    git pull origin main
    docker compose down
    docker compose up --build -d
    docker compose run --rm api ragtest-ingest --recreate

Depois:

    docker compose run --rm api ragtest-search "Quais são os direitos e deveres da pessoa usuária da saúde?" --limit 5

E a avaliação:

    docker compose run --rm api ragtest-evaluate-retrieval

Resultados esperados devem ser comparados com:

    0.5.1  HitRate@5=0.857  MRR@5=0.714
    0.5.2  HitRate@5=0.857  MRR@5=0.786

Não considere a 0.5.3 melhor antes de medir os sete casos.

## API

- GET /health
- GET /ready
- POST /v1/search
- POST /v1/chat
- Swagger: http://localhost:8000/docs

## Dificuldades TCC

Registro contínuo em docs/dificuldades-tcc.md.

## Segurança

Nunca versione GEMINI_API_KEY. Use apenas .env local.
