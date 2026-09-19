# RagTest

Módulo RAG reutilizável via API.

## Estado atual

O OCR seletivo corrigiu a cobertura do corpus:

- Carta dos Direitos e Deveres: 28/28 páginas via OCR;
- 41.237 caracteres;
- 62 chunks;
- corpus total: 767 chunks;
- HitRate@5 observado no modo híbrido: 1.000 (7/7);
- MRR@5 observado no modo híbrido: 0.821.

## Fase 0.5.7 — benchmark justo de retrieval

Os resultados anteriores a 0.5.6 foram obtidos com um corpus incompleto. A 0.5.7 compara as estratégias sobre a mesma collection corrigida:

    dense
    dense-rerank
    hybrid

Atualize e execute:

    git pull origin feature/retrieval-benchmark-0.5.7
    docker compose down
    docker compose up --build -d
    docker compose run --rm api ragtest-evaluate-retrieval

Não é necessário recriar a collection: os 767 chunks da 0.5.6 já contêm vetores dense e sparse.

Para testar um perfil isolado:

    docker compose run --rm api ragtest-evaluate-retrieval --mode dense
    docker compose run --rm api ragtest-evaluate-retrieval --mode dense-rerank
    docker compose run --rm api ragtest-evaluate-retrieval --mode hybrid

## Dificuldades TCC

Registro contínuo em docs/dificuldades-tcc.md.

## Segurança

Nunca versione GEMINI_API_KEY. Use apenas .env local.
