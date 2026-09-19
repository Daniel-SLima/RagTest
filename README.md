# RagTest

Módulo RAG reutilizável via API para Flutter, React Native, Web e outros sistemas.

## Fase atual — 0.5 Qualidade do Retrieval

A versão 0.5.2 combina retrieval denso com reranking lexical leve:

    Qdrant dense retrieval
      -> overfetch
      -> agrupamento por página
      -> reranking lexical de metadados/conteúdo
      -> corte relativo
      -> contexto final
      -> Gemini

O score semântico original é preservado. Um rank_score separado é usado para ordenar os candidatos e facilitar auditoria.

Baseline 0.5.1:

    HitRate@5 = 0.857 (6/7)
    MRR@5     = 0.714

Detalhes: docs/avaliacao-retrieval.md

## Atualizar no Windows CMD

    git pull origin main
    docker compose down
    docker compose up --build -d

Não é necessário reindexar.

Teste o caso que falhou na baseline:

    docker compose run --rm api ragtest-search "Quais são os direitos e deveres da pessoa usuária da saúde?" --limit 5

Depois rode a avaliação completa:

    docker compose run --rm api ragtest-evaluate-retrieval

Compare HitRate@5 e MRR@5 com a baseline antes de considerar a mudança uma melhoria.

## Dificuldades TCC

Registro em docs/dificuldades-tcc.md. Cada caso contém planejado, observado, diagnóstico, correção e aprendizado.

## API

- GET /health
- GET /ready
- POST /v1/search
- POST /v1/chat
- Swagger em http://localhost:8000/docs

## Segurança

Nunca versione a chave do Gemini. Use somente o arquivo local .env.
