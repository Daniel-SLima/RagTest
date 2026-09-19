# Avaliação do Retrieval

## Baseline 0.5.1

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.714

## Experimento 0.5.2 — reranking lexical

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.786

Melhor resultado medido até aqui.

## Experimento 0.5.3 — dense + BM25 + RRF

- HitRate@5: 0.714 (5/7)
- MRR@5: 0.607

Piorou as duas métricas.

## Experimento 0.5.4 — BM25 enriquecido com metadados

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.690

Recuperou o HitRate da baseline, mas ficou abaixo da 0.5.1 e 0.5.2 em MRR. A carta de direitos e deveres continuou ausente do top 5.

Conclusão provisória: novas tentativas de ajuste de ranking devem ser interrompidas até verificar se o documento esperado realmente contribui com texto e chunks para o índice.

## Diagnóstico 0.5.5 — cobertura do corpus

A versão 0.5.5 adiciona auditoria por arquivo ao comando:

    docker compose run --rm api ragtest-inspect

E permite filtrar:

    docker compose run --rm api ragtest-inspect --source direitos_saude

Para cada arquivo são exibidos:

- unidades/páginas carregadas;
- unidades com texto;
- total de caracteres extraídos;
- chunks gerados;
- status de cobertura.

Se a carta de direitos/deveres apresentar NO_TEXT ou NO_CHUNKS, o problema é anterior ao retrieval e deve ser tratado na extração/OCR.
