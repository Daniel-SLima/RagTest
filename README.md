# RagTest — módulo RAG para o Se Cuida Mulher

Módulo conversacional baseado em RAG (Retrieval-Augmented Generation) para apoiar o letramento em
saúde da mulher e a orientação de agendamento de serviços (preventivo, mamografia, pré-natal e
urgência). TCC do curso de ADS. Integração prevista: app **Se Cuida Mulher**.

> Para agentes de IA e continuidade: leia `AGENTS.md` e `docs/ESTADO_ATUAL.md`.

## Arquitetura

```
Cliente (Expo demo / app integrador)
        │  REST /v1/chat
        ▼
FastAPI ── triagem de urgência (regras) ──► resposta fixa + ação 192
   │
   ├─ retrieval: FastEmbed (denso) + BM25 (esparso) no Qdrant, rerank, multi-query
   ├─ geração: Gemini / Groq / Ollama, com gate de citações e fallback seguro
   ├─ ações: links e lembretes do catálogo de serviços citado
   └─ sessões (SQLite) e auditoria estruturada sem conteúdo
```

| Camada | Tecnologia |
|---|---|
| API | Python 3.12, FastAPI, Pydantic |
| Vetores | Qdrant 1.19 (denso + esparso) |
| Embeddings | FastEmbed `paraphrase-multilingual-MiniLM-L12-v2`, BM25 |
| Orquestração | LangChain (text splitter, prompt templates) |
| LLM | Gemini, Groq (GPT-OSS 120B) ou Ollama (Qwen3 8B) |
| Cliente demo | Expo / React Native / TypeScript |
| Infra | Docker Compose, GitHub Actions |

## Base documental (`data/source`)

Cartilhas e cadernetas do Ministério da Saúde, calendários de vacinação, contracepção, direitos
da pessoa usuária, o FAQ do Se Cuida Mulher (`chatscm/`) e o catálogo estruturado de serviços
(`servicos/catalogo_servicos.json`).

## Como rodar

```bash
cp .env.example .env              # coloque a chave do provider escolhido
docker compose up -d --build
curl http://localhost:8000/ready
docker compose exec api ragtest-plan-ingestion-sync
docker compose exec api ragtest-sync-ingestion --apply
curl -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" \
  -d '{"message":"Quando devo fazer o preventivo?"}'
```

Cliente demo: `cd frontend && npm install && npm run web`.
Avaliação completa no Windows: `scripts/avaliar_dominio.ps1` (salva em `docs/resultados/`).

## Desenvolvimento

```bash
python -m pip install -e ".[dev]"
pytest && ruff check .
cd frontend && npm test && npm run typecheck
```

## Documentação

| Documento | Conteúdo |
|---|---|
| `docs/ESTADO_ATUAL.md` | estado atual e próximos passos |
| `docs/PLANO_FINALIZACAO_TCC.md` | plano por fases |
| `docs/INTEGRACAO.md` | contrato da API para o app integrador |
| `docs/decisoes-tecnicas.md` | decisões arquiteturais (D001–D041) |
| `docs/dificuldades-tcc.md` | problemas reais e aprendizados |
| `docs/avaliacao-retrieval.md` | metodologia e resultados de avaliação |
| `docs/historico/` | contexto e README anteriores à reorientação |

## Limitações

Ambiente demonstrativo: sem autenticação, sem dados reais de usuárias. `grounded=true` significa
que cada afirmação tem citação válida, não que houve validação clínica. As orientações não
substituem a avaliação de profissionais de saúde.
