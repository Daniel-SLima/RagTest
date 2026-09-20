# RagTest

Módulo RAG reutilizável via API.

## Fase 0.5.9 — avaliação holdout

A 0.5.8 foi validada e mesclada. O modo padrão continua sendo `dense-rerank`.

A 0.5.9 amplia a avaliação sem alterar os parâmetros de retrieval:

- `dev`: 7 consultas já usadas durante o desenvolvimento;
- `holdout`: 15 consultas novas, congeladas antes da primeira execução;
- `all`: combinação das duas suites, totalizando 22 consultas.

Dataset:

    2026-09-20-v1

O objetivo é verificar generalização. O holdout não deve ser usado para ajustar pesos e depois ser apresentado como uma avaliação independente.

## Atualizar

    git fetch origin
    git switch --track origin/feature/holdout-evaluation-0.5.9
    docker compose down
    docker compose up --build -d
    curl http://localhost:8000/health
    curl http://localhost:8000/ready

Não recrie a collection. O corpus permanece com 767 chunks.

## Primeira execução do holdout — concluída

Resultado preservado do modo padrão:

    dense-rerank
    HitRate@5=1.000 (15/15)
    MRR@5=0.933

Foram 13 casos com fonte esperada em rank 1 e 2 casos em rank 2, sem falhas no top 5.

Agora compare os três perfis:

    docker compose run --rm api ragtest-evaluate-retrieval --suite holdout --mode all

Para confirmar que a regressão histórica segue igual:

    docker compose run --rm api ragtest-evaluate-retrieval --suite dev --mode all

A primeira saída do holdout deve ser preservada como resultado experimental. Se surgirem falhas, elas devem ser analisadas, mas não se deve recalibrar o perfil e reutilizar o mesmo holdout como se continuasse sendo um teste não visto.

## Segurança

Nunca versione GEMINI_API_KEY. Use apenas .env local.
