# Avaliação do Retrieval

## Baseline 0.5.1 — 2026-09-19

Conjunto inicial: 7 perguntas, com k=5.

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.714

Ranks da primeira fonte esperada:

1. vacinação de idosos: 1
2. vacinação na gestação: 2
3. vacinação da criança: 1
4. DIU de cobre: 1
5. implante contraceptivo: 2
6. canetas de insulina: 1
7. direitos e deveres da pessoa usuária da saúde: não recuperado

A baseline deve ser preservada para comparação. A versão 0.5.2 testa reranking lexical de metadados e conteúdo, mantendo o score semântico original separado do rank_score.

Após atualizar:

    docker compose run --rm api ragtest-evaluate-retrieval

Registrar HitRate@5, MRR@5 e ranks para comparar com a baseline.
