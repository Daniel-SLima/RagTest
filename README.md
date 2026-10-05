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

> **Vai assumir ou orientar o projeto?** Comece pelo [guia de continuidade](docs/GUIA_CONTINUIDADE.md).
> Ele separa o que foi implementado, o que foi medido e o que ainda é proposta. O
> [estado atual](docs/ESTADO_ATUAL.md) e o [roteiro](docs/ROTEIRO_EXECUCAO.md) registram as próximas etapas.

## Estado da pesquisa e da entrega

O produto estudado é a **API headless**. O cliente Expo demonstra o contrato, mas não é o aplicativo
Se Cuida Mulher final. A versão declarada no pacote Python ainda é `0.8.0`; os nomes `0.9.x`
identificam etapas de trabalho. A release `1.0.0`, a monografia, a integração com o app real e a
validação com usuárias **não foram concluídas**.

A etapa 0.9.2 foi incorporada ao `main` pelo [PR #25](https://github.com/Daniel-SLima/RagTest/pull/25).
Ela inclui a correção [D054](docs/decisoes-tecnicas.md) para respostas de agendamento e o roteiro
de execução. A coleta completa de respostas **ainda precisa ser repetida** após essa correção.

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

O [inventário das fontes e referências](docs/FONTES_E_REFERENCIAS.md) distingue os documentos
efetivamente incluídos no corpus das referências citadas pelo catálogo. Ainda não existe uma
bibliografia acadêmica final em ABNT. O catálogo de serviços é demonstrativo e precisará dos
fluxos reais de agendamento do município para uma integração operacional.

## Estudos e resultados até aqui

Os [experimentos em ordem cronológica](docs/ESTUDOS_E_RESULTADOS.md) mostram como a escolha do
retrieval mudou quando as perguntas passaram do corpus genérico para o domínio de saúde da mulher.
Os números abaixo vêm das [avaliações registradas](docs/avaliacao-retrieval.md), com saídas brutas
em [`docs/resultados/`](docs/resultados/):

| Estudo | Resultado observado | Limite da conclusão |
|---|---|---|
| OCR seletivo | Carta dos Direitos: 28 páginas recuperadas, 62 chunks; corpus de 699 para 767 chunks | Benchmarks anteriores usavam corpus incompleto |
| Benchmark genérico | `dense-rerank`: 7/7 no dev, MRR@5 0,929; 15/15 no primeiro holdout, MRR@5 0,933 | Conjunto pequeno e anterior ao foco em agendamento |
| Domínio v2, dev | `hybrid`: 15/15, MRR@5 0,833; `dense` e `dense-rerank`: 9/15 | Resultado usado para escolher o padrão |
| Holdout v3 independente | `hybrid`: 24/25, MRR@5 0,801 | Uma falha com sinônimo coloquial; não equivale a qualidade clínica |
| Primeira coleta de respostas | 11/13 respostas de domínio verificadas, 2/2 triagens, 4/4 recusas | Dois fallbacks motivaram D054; falta recoleta e rubrica humana |

As [decisões técnicas](docs/decisoes-tecnicas.md) explicam as escolhas e os trade-offs. As
[dificuldades documentadas](docs/dificuldades-tcc.md) registram erros reais, diagnósticos e
correções. A [rubrica de respostas](docs/avaliacao-respostas.md) define fidelidade, relevância e
clareza em escala 0–2, mas ainda não recebeu notas finais.

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
| [Guia de continuidade](docs/GUIA_CONTINUIDADE.md) | Visão completa para orientador e futuro estudante: objetivos, implementação, estudos, limites e retomada |
| [Estado atual](docs/ESTADO_ATUAL.md) e [roteiro](docs/ROTEIRO_EXECUCAO.md) | Branch, evidências, pendências e micro-etapas futuras |
| [Plano de finalização](docs/PLANO_FINALIZACAO_TCC.md) | Motivo da reorientação e status das fases |
| [Estudos e resultados](docs/ESTUDOS_E_RESULTADOS.md) | Linha do tempo dos experimentos, hipóteses e conclusões |
| [Avaliação de retrieval](docs/avaliacao-retrieval.md) e [de respostas](docs/avaliacao-respostas.md) | Metodologia, métricas e resultados interpretados |
| [Saídas originais](docs/resultados/) e [datasets](app/evaluation/datasets/) | Evidência bruta e perguntas usadas nas avaliações |
| [Fontes e referências](docs/FONTES_E_REFERENCIAS.md) e [corpus](data/source/) | Inventário documental e lacunas bibliográficas |
| [Decisões técnicas](docs/decisoes-tecnicas.md) e [dificuldades](docs/dificuldades-tcc.md) | Acertos, erros, justificativas e aprendizados |
| [Integração](docs/INTEGRACAO.md) e [OpenAPI](docs/contrato/openapi-v1.json) | Contrato para um aplicativo cliente |
| [Esqueleto da monografia](docs/monografia/ESQUELETO.md) | Mapa dos capítulos para as evidências já disponíveis |

Para uma leitura rápida: **guia de continuidade → estudos → decisões/dificuldades → resultados
brutos → código e testes**. O [histórico anterior à 0.7.0](docs/historico/) está preservado para
consulta, mas não descreve o estado vigente. Um antigo prompt de retomada e o guia da interface
0.5.x foram retirados da árvore atual por estarem desatualizados; continuam no histórico do Git.

## Limitações e uso responsável

O projeto é um ambiente demonstrativo e acadêmico. Não utiliza dados reais de usuárias.

`grounded=true` indica que a resposta passou pelas regras de fundamentação/citação definidas pelo sistema; isso **não representa validação clínica**.

As informações geradas pelo sistema não substituem avaliação ou orientação de profissionais de saúde.

---

Desenvolvido por [Daniel Lima](https://github.com/Daniel-SLima) como inicio de um projeto de TCC em Análise e Desenvolvimento de Sistemas.
