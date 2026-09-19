# RagTest

Módulo RAG reutilizável via API.

## Fase 0.5.4 — ajuste do retrieval híbrido

Resultados já medidos:

    0.5.1  HitRate@5=0.857  MRR@5=0.714
    0.5.2  HitRate@5=0.857  MRR@5=0.786
    0.5.3  HitRate@5=0.714  MRR@5=0.607

A 0.5.3 não foi aceita como melhoria.

A 0.5.4 corrige duas hipóteses do experimento anterior:

- BM25 passa a indexar source, filename, category e audience junto ao conteúdo;
- RETRIEVAL_SCORE_MARGIN passa a 0.0 no híbrido;
- dense e sparse usam pesos neutros 1.0 / 1.0.

## Atualizar no Windows CMD

    git pull origin main
    docker compose down
    docker compose up --build -d

No .env use:

    HYBRID_DENSE_WEIGHT=1.0
    HYBRID_SPARSE_WEIGHT=1.0
    RETRIEVAL_SCORE_MARGIN=0.0

Como o conteúdo do vetor sparse mudou, recrie a collection:

    docker compose run --rm api ragtest-ingest --recreate

Depois teste:

    docker compose run --rm api ragtest-search "Quais são os direitos e deveres da pessoa usuária da saúde?" --limit 5
    docker compose run --rm api ragtest-evaluate-retrieval

A 0.5.4 só deve ser considerada melhor após medir o mesmo conjunto de sete consultas.

## Dificuldades TCC

Registro contínuo em docs/dificuldades-tcc.md.

## Segurança

Nunca versione GEMINI_API_KEY. Use apenas .env local.
