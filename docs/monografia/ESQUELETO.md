# Esqueleto da monografia — mapa de evidências

Cada seção aponta para onde está o material no repositório. Números de decisão (Dxxx) estão em
`docs/decisoes-tecnicas.md`; dificuldades (#n) em `docs/dificuldades-tcc.md`.

## 1. Introdução

- Problema: barreiras de acesso a exames preventivos e baixo letramento em saúde (proposta do orientador).
- Objetivo geral e específicos: proposta do orientador (`docs/PLANO_FINALIZACAO_TCC.md`, seção 0).
- Contribuição: módulo RAG headless, integrável ao Se Cuida Mulher, com guardrails verificáveis.

## 2. Fundamentação teórica

- LLMs e alucinação; RAG (retrieval + geração).
- Embeddings densos, BM25/esparso, busca híbrida e RRF (D002, D006, D046, #5–#9).
- Chunking e metadados (D003, D047).
- Avaliação de retrieval: HitRate, MRR, NDCG, dev × holdout (D008, D009, D017).
- Letramento em saúde e rastreamento no SUS (fontes do catálogo: Diretriz MS 2025, NT 626/2025).

## 3. Metodologia

- Processo: desenvolvimento incremental com TDD, CI e registro de decisões/dificuldades.
- Corpus: `data/source/README.md`, auditoria de PII (D038), catálogo estruturado (`data/source/servicos`).
- Datasets: dev/holdout v1 (genérico), v2 (domínio), v3 (holdout congelado) — `docs/avaliacao-retrieval.md`.
- Avaliação de respostas: rubrica em `docs/avaliacao-respostas.md`.

## 4. Arquitetura e implementação

- Visão geral e diagrama: `README.md`.
- Pipeline de ingestão: loaders, OCR seletivo (D005, #8), sync incremental (D015).
- Retrieval: perfis (D007), hybrid padrão (D046), decomposição/multi-query (D011, D012).
- Geração e guardrails: citações (D010), gate de cobertura (D018, D022, D023, D050, D051),
  recusa explícita (D048), triagem de urgência (D039), fora de escopo (D041).
- Backend headless e contrato: D042, D043, `docs/INTEGRACAO.md`, `docs/contrato/openapi-v1.json`.
- Ações (links e lembretes): D040.
- Segurança e auditoria: D035–D037, D044, D053.
- Padrões de projeto: Factory (providers de LLM e embeddings), Strategy (perfis de retrieval),
  Repository (sessões SQLite), Adapter (providers Gemini/Groq/Ollama), Middleware (auditoria).

## 5. Resultados

- Retrieval no domínio: tabela dense × dense-rerank × hybrid (`docs/avaliacao-retrieval.md`).
- Holdout v3 (quando executado).
- Rubrica das respostas e taxas de grounded/fallback/recusa.
- Latência por provider (métricas do `ragtest-chat` e da planilha).
- Casos qualitativos: mamografia antes/depois (D050, `docs/resultados/diagnostico_mamografia*.txt`).

## 6. Discussão e lições aprendidas

- Seleção de estratégia depende do público (#34).
- Guardrails estruturais × formato real do modelo (#19, #22–#26, #36).
- Recusa precisa de saída explícita (#35).
- Hermeticidade de testes e diferenças de ambiente (#32, #33, #38).

## 7. Limitações e trabalhos futuros

- Integração real no Se Cuida Mulher; dados reais de UBS no catálogo.
- Juiz semântico de fidelidade; avaliação com usuárias (SUS).
- Autenticação por usuária final, limite distribuído, backups.
