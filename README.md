# RagTest

Módulo RAG reutilizável via API.

## Fase 0.5.8 — dense-rerank como candidato padrão

O benchmark 0.5.7 foi mesclado após validação no corpus corrigido de 767 chunks:

    MODE            HITRATE@5   MRR@5
    dense             1.000      0.857
    dense-rerank      1.000      0.929
    hybrid            1.000      0.821

A 0.5.8 torna `dense-rerank` o modo padrão da aplicação, usando exatamente os parâmetros do perfil validado no benchmark:

    candidate_multiplier = 8
    score_margin = 0.22
    source_lexical_weight = 0.25
    content_lexical_weight = 0.05
    sparse retrieval = desativado

Os perfis `dense` e `hybrid` continuam disponíveis para benchmark e diagnóstico.

## Atualizar e validar

No .env, adicione ou confirme:

    RETRIEVAL_MODE=dense-rerank

As variáveis antigas de tuning de perfil podem permanecer no arquivo local, mas a 0.5.8 usa os parâmetros versionados do perfil selecionado e ignora essas chaves antigas.

Depois:

    git fetch origin
    git switch --track origin/feature/default-dense-rerank-0.5.8
    docker compose down
    docker compose up --build -d
    curl http://localhost:8000/health
    curl http://localhost:8000/ready

Não recrie a collection. Os 767 chunks atuais continuam compatíveis.

Valide a busca padrão:

    docker compose run --rm api ragtest-search "Quais vacinas são indicadas durante a gestação?" --limit 5

A saída deve informar:

    Mode: dense-rerank

Repita o benchmark:

    docker compose run --rm api ragtest-evaluate-retrieval

E valide o chat apenas com documentos aprovados para envio ao Gemini.

## Segurança

Nunca versione GEMINI_API_KEY. Use apenas .env local.
