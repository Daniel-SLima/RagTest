# RagTest

Módulo RAG reutilizável via API para Flutter, React Native, Web e outros sistemas.

## Fase atual — 0.5 Qualidade do Retrieval

Pipeline atual:

```text
PDF/DOCX
  -> chunking
  -> embeddings
  -> Qdrant
  -> overfetch de candidatos
  -> agrupamento por fonte/página
  -> filtro relativo por score
  -> contexto final
  -> Gemini
  -> resposta + fontes
```

A fase 0.5 melhora a qualidade do contexto entregue ao LLM sem alterar os vetores já indexados.

### Melhorias de retrieval

- overfetch: busca mais candidatos no Qdrant do que o número final solicitado;
- agrupamento de chunks da mesma página de PDF;
- reconstrução do texto respeitando `start_index`;
- remoção do overlap de chunk quando possível;
- corte relativo por score em relação ao melhor resultado;
- `chunk_count` nas fontes para auditoria;
- parâmetros configuráveis por ambiente.

Configuração padrão:

```env
RETRIEVAL_CANDIDATE_MULTIPLIER=4
RETRIEVAL_SCORE_MARGIN=0.22
RETRIEVAL_MERGE_SAME_PAGE=true
RETRIEVAL_MAX_GROUP_CHARS=5000
```

O corte relativo evita depender de um threshold global fixo. Por exemplo, com melhor score 0.75 e margem 0.22, resultados abaixo de aproximadamente 0.53 são descartados.

## Avaliação do retrieval

Foi adicionado um pequeno conjunto inicial de avaliação em:

```text
tests/evaluation/retrieval_cases.json
```

Execute:

```cmd
docker compose run --rm api ragtest-evaluate-retrieval
```

A saída informa:

- `HitRate@5`: proporção de perguntas em que uma fonte esperada apareceu no top 5;
- `MRR@5`: favorece fontes esperadas que aparecem nas primeiras posições.

Essas métricas podem ser ampliadas e usadas na seção experimental do TCC.

## Registro de dificuldades do TCC

Problemas relevantes encontrados durante o desenvolvimento são documentados em:

```text
docs/dificuldades-tcc.md
```

Cada caso registra planejamento, observação, diagnóstico, correção e aprendizado técnico.

## Atualizar no Windows CMD

```cmd
git pull origin main
docker compose down
docker compose up --build -d
```

Não é necessário reindexar para a fase 0.5, pois embeddings e chunks armazenados não foram alterados.

Teste a recuperação:

```cmd
docker compose run --rm api ragtest-search "Quais vacinas são recomendadas para idosos?" --audience idoso --limit 5
```

Teste o chat:

```cmd
docker compose run --rm api ragtest-chat "Quais vacinas são recomendadas para idosos?" --audience idoso
```

## API

- `GET /health`
- `GET /ready`
- `POST /v1/search`
- `POST /v1/chat`
- Swagger em `http://localhost:8000/docs`

## Segurança da chave

Nunca versione a chave do Gemini. Use somente o arquivo local `.env`, que está ignorado pelo Git.

## Próximas etapas

Depois de medir a fase 0.5, os próximos incrementos naturais são reranking com modelo específico, busca híbrida, logs estruturados de auditoria, histórico de sessão e streaming para integração com o aplicativo.
