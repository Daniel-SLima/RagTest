# Avaliação das respostas (rubrica manual)

Complementa a avaliação de retrieval: mede se a **resposta final** é fiel às fontes, útil e clara.

## Como gerar a planilha

Com o Docker rodando e o provider configurado no `.env`:

```powershell
docker compose up -d --build
docker compose exec api ragtest-collect-answers
docker compose cp api:/app/state/respostas_modelo.csv docs\resultados\respostas_modelo.csv
```

Por padrão são 19 perguntas (15 do dev v2 + 4 fora de escopo), cerca de 20–40 chamadas ao
provider. O CSV usa `;` e abre direto no Excel.

## Como pontuar

Preencha as três colunas de 0 a 2 para cada linha (idealmente você e mais uma pessoa, sem combinar
as notas, para calcular a concordância).

| Critério | 0 | 1 | 2 |
|---|---|---|---|
| **Fidelidade** | afirma algo que não está nas fontes ou contradiz | tem pequena imprecisão ou generalização | tudo o que afirma está nas fontes citadas |
| **Relevância** | não responde à pergunta | responde em parte | responde ao que foi perguntado |
| **Clareza** | confusa ou técnica demais para a usuária | compreensível com esforço | linguagem simples e direta |

Casos especiais:

- `status=emergency` (triagem): avaliar se a orientação de urgência é adequada; fidelidade = 2 se
  coerente com o CHATSCM/Caderneta.
- `status=out_of_scope`: relevância = 2 se a pergunta realmente estava fora do tema; 0 se era do
  tema e foi recusada.
- `status=unverified` / `no_sources`: fallback; relevância = 0 (a usuária ficou sem resposta).

## Métricas para a monografia

- média de cada critério (0–2) e porcentagem de notas 2;
- `grounded_rate` (status `verified`), taxa de fallback, taxa de recusa correta nos fora de escopo;
- latência média e p95 (`latency_ms`);
- concordância entre avaliadores (kappa de Cohen), se houver dois avaliadores.

## Resultados

Ainda não executado.
