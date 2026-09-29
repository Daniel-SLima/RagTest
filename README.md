# RagTest — RAG para o Se Cuida Mulher

<div align="center">

**Módulo conversacional com recuperação aumentada por geração para apoio ao letramento em saúde da mulher.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC244C)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/projeto-TCC-6B7280)

</div>

## Sobre o projeto

O **RagTest** é o módulo conversacional desenvolvido para o TCC de Análise e Desenvolvimento de Sistemas, com integração prevista ao aplicativo **Se Cuida Mulher**.

A solução usa **RAG (Retrieval-Augmented Generation)** para recuperar informações de uma base documental controlada antes de gerar a resposta. O projeto dá atenção especial a rastreabilidade, citações, avaliação de retrieval, privacidade e comportamento seguro fora do escopo.

> Para continuidade técnica e agentes de IA, consulte `AGENTS.md` e `docs/ESTADO_ATUAL.md`.

## O que o projeto demonstra

- API REST versionada com FastAPI
- Retrieval denso e esparso
- Qdrant como banco vetorial
- Reranking e multi-query retrieval
- Respostas fundamentadas em fontes
- Gate de citações e fallback seguro
- Triagem determinística para situações de urgência
- Suporte a múltiplos providers de LLM
- Sessões locais e auditoria estruturada
- Cliente demo em React Native / Expo
- Testes automatizados e quality gates
- Docker Compose e GitHub Actions
- Documentação de decisões arquiteturais e avaliação

## Arquitetura

```text
Cliente Expo / app integrador
            │
            │  REST /v1/chat
            ▼
         FastAPI
            │
            ├── Triagem de urgência
            ├── Retrieval híbrido
            │     ├── FastEmbed
            │     ├── BM25
            │     ├── Qdrant
            │     └── rerank / multi-query
            │
            ├── Geração
            │     ├── Gemini
            │     ├── Groq
            │     └── Ollama
            │
            ├── Gate de grounding/citações
            └── Sessões + auditoria
```

## Stack

| Camada | Tecnologias |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic |
| Vetores | Qdrant 1.19 |
| Retrieval | FastEmbed, BM25, reranking, multi-query |
| Orquestração | LangChain |
| LLM | Gemini, Groq ou Ollama |
| Frontend demo | Expo, React Native, TypeScript |
| Testes | Pytest, Jest, Testing Library |
| Qualidade | Ruff, TypeScript |
| Infra | Docker Compose, GitHub Actions |

## Base documental

A base em `data/source` utiliza materiais controlados, incluindo documentos do Ministério da Saúde, calendários de vacinação, materiais sobre contracepção, direitos da pessoa usuária, FAQ do Se Cuida Mulher e catálogo estruturado de serviços.

O pipeline de ingestão transforma esse conteúdo em representações pesquisáveis no Qdrant.

## Executando com Docker

```bash
cp .env.example .env
docker compose up -d --build

curl http://localhost:8000/ready

docker compose exec api ragtest-plan-ingestion-sync
docker compose exec api ragtest-sync-ingestion --apply
```

Exemplo de consulta:

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Quando devo fazer o preventivo?"}'
```

Frontend demo:

```bash
cd frontend
npm install
npm run web
```

## Desenvolvimento e testes

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

Frontend:

```bash
cd frontend
npm test
npm run typecheck
```

## Documentação técnica

| Documento | Conteúdo |
|---|---|
| `docs/ESTADO_ATUAL.md` | Estado atual e próximos passos |
| `docs/PLANO_FINALIZACAO_TCC.md` | Plano de finalização |
| `docs/INTEGRACAO.md` | Contrato para integração |
| `docs/contrato/openapi-v1.json` | Contrato OpenAPI |
| `docs/decisoes-tecnicas.md` | Decisões arquiteturais |
| `docs/dificuldades-tcc.md` | Problemas e aprendizados |
| `docs/avaliacao-retrieval.md` | Metodologia de avaliação |
| `docs/resultados/` | Resultados de avaliações |

## Limitações e uso responsável

O projeto é um ambiente demonstrativo e acadêmico. Não utiliza dados reais de usuárias.

`grounded=true` indica que a resposta passou pelas regras de fundamentação/citação definidas pelo sistema; isso **não representa validação clínica**.

As informações geradas pelo sistema não substituem avaliação ou orientação de profissionais de saúde.

---

Desenvolvido por [Daniel Lima](https://github.com/Daniel-SLima) como projeto de TCC em Análise e Desenvolvimento de Sistemas.
