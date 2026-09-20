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

Benchmark verificado sobre a mesma collection corrigida de 767 chunks:

    MODE            HITRATE@5   MRR@5
    dense             1.000      0.857
    dense-rerank      1.000      0.929
    hybrid            1.000      0.821

No conjunto atual de sete consultas, dense-rerank obteve o maior MRR@5. Este resultado é experimental e não deve ser generalizado antes de ampliar o conjunto de avaliação.

Para repetir:

    docker compose run --rm api ragtest-evaluate-retrieval

Ou por perfil:

    docker compose run --rm api ragtest-evaluate-retrieval --mode dense
    docker compose run --rm api ragtest-evaluate-retrieval --mode dense-rerank
    docker compose run --rm api ragtest-evaluate-retrieval --mode hybrid

Não é necessário recriar a collection: os 767 chunks já contêm vetores dense e sparse.

## Dificuldades TCC

Registro contínuo em docs/dificuldades-tcc.md.

## Segurança

Nunca versione GEMINI_API_KEY. Use apenas .env local.
