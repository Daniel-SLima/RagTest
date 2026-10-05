# Guia de continuidade — RagTest

**Fotografia técnica de 05/10/2026.** Este guia foi escrito para o orientador e para estudantes que possam assumir o TCC. Descreve o que existe, como foi estudado e o que falta comprovar. O RagTest é um trabalho acadêmico em andamento: a versão declarada ainda é `0.8.0` e não há monografia nem release `1.0.0` finalizadas.

## 1. Problema, objetivo e recorte

O projeto investiga um módulo de conversação RAG (Retrieval-Augmented Generation) para o aplicativo **Se Cuida Mulher**. O objetivo é apoiar o letramento em saúde da mulher e orientar o acesso a serviços do SUS, sobretudo exame preventivo do colo do útero, mamografia, pré-natal e sinais de urgência. O fluxo recupera trechos de uma base documental controlada antes de solicitar a resposta a um modelo de linguagem. A resposta apresenta fontes e pode sugerir ações ao aplicativo integrador.

A diretriz atual do autor é **backend headless**: a API é o produto; o cliente Expo/React Native é uma demonstração congelada. A API define triagem, segurança, textos de exibição, sugestões, serviços, datas de lembrete e ações. Um aplicativo futuro em Flutter ou React Native executaria as ações e desenharia a interface. A integração com o Se Cuida Mulher real ainda não ocorreu. O [plano de finalização](PLANO_FINALIZACAO_TCC.md) explica a reorientação feita em 28/09/2026; o [roteiro](ROTEIRO_EXECUCAO.md) divide o caminho até uma eventual v1.0.0 em micro-etapas.

## 2. O que já foi desenvolvido

### Corpus e ingestão

O corpus versionado está em [`data/source/`](../data/source/), com PDFs de saúde pública, três DOCX de FAQ CHATSCM e um [catálogo estruturado de serviços](../data/source/servicos/catalogo_servicos.json). O pipeline em [`app/rag/`](../app/rag/) extrai PDF/DOCX, aplica OCR seletivo em páginas sem texto, divide os documentos em chunks e gera embeddings densos e esparsos para o Qdrant. Há planejamento e sincronização incremental da ingestão; não é necessário destruir a collection para incluir atualizações. Os 773 chunks registrados em 28/09/2026 descrevem o ambiente usado naquela avaliação, não um índice incluído no repositório.

O FAQ CHATSCM foi liberado para desenvolvimento e avaliação pela decisão [D038](decisoes-tecnicas.md), depois de auditoria automática com zero achados. O [registro de privacidade](revisao-privacidade-chatscm.md) mantém um checklist manual recomendado antes de uso em produção. O catálogo é **demonstrativo**: informações de agendamento precisam ser trocadas pelos fluxos reais de um município antes de integração operacional. A lista e o estado bibliográfico das fontes estão em [FONTES_E_REFERENCIAS.md](FONTES_E_REFERENCIAS.md).

### Recuperação, geração e segurança

A busca combina FastEmbed, Qdrant, BM25 e RRF. Os modos denso, denso com reranking e híbrido continuam disponíveis; o híbrido é o padrão após o estudo no domínio. O código de busca fica em [`app/rag/`](../app/rag/) e as perguntas de avaliação em [`app/evaluation/datasets/`](../app/evaluation/datasets/). O projeto usa LangChain de forma seletiva para documentos, divisão de texto e templates; a orquestração do chat é própria para manter o gate de citações e a triagem controláveis e testáveis.

A geração aceita Gemini, Groq ou Ollama. O gate estrutural exige cobertura de citações para blocos informativos, tenta reparo, pode podar blocos sem suporte e usa fallback quando não consegue validar. A [D054](decisoes-tecnicas.md) corrigiu dois casos de listas curtas que derrubavam respostas; **a coleta completa após essa correção ainda não foi executada**. `grounded=true` quer dizer que o texto passou na regra estrutural de citações, não que foi clinicamente validado.

Sinais de urgência em primeira pessoa são triados por regras antes do retrieval e do LLM; o sistema devolve orientação fixa e pode sugerir ligar 192. A calibração do limiar de similaridade não separou bem domínio e fora de escopo, então `RETRIEVAL_MIN_SCORE` permanece desligado por padrão. Uma recusa explícita do LLM é tratada como fora de escopo sem receber citação falsa. Auditoria estruturada evita registrar perguntas, respostas, prompts e trechos. Autenticação `X-API-Key` e limite por cliente protegem as rotas da API; o limite é em memória por processo.

### Ações, contrato e cliente de referência

A API em [`app/api/`](../app/api/) expõe chat, sessões, busca, sugestões e catálogo de serviços. O [contrato OpenAPI](contrato/openapi-v1.json) é testado contra o código; o [guia de integração](INTEGRACAO.md) descreve campos, autenticação, erros e ações. `open_link`, `schedule_reminder` e `call_emergency` são sugestões estruturadas do backend; abrir links, criar notificações e efetuar chamadas cabe ao aplicativo integrador. O catálogo só gera ação de serviço quando o serviço aparece entre as fontes citadas de resposta verificada. O cliente em [`frontend/`](../frontend/) demonstra o contrato e guarda lembretes apenas em memória. Docker Compose, [CI](../.github/workflows/ci.yml) e um [guia de homologação](DEPLOY.md) estão presentes; não há registro de deploy real concluído.

## 3. Estudos realizados e resultados observados

O histórico experimental detalhado, etapa por etapa, está em [ESTUDOS_E_RESULTADOS.md](ESTUDOS_E_RESULTADOS.md). As saídas originais estão em [`docs/resultados/`](resultados/); a interpretação metodológica completa em [avaliacao-retrieval.md](avaliacao-retrieval.md) e [avaliacao-respostas.md](avaliacao-respostas.md).

- **Ingestão/OCR:** a Carta dos Direitos tinha 28 páginas e zero chunks; OCR seletivo recuperou 41.237 caracteres e 62 chunks. O corpus passou de 699 para 767 chunks. Isso invalidou comparações diretas com os primeiros benchmarks feitos sobre o corpus incompleto.
- **Benchmark genérico:** num conjunto de 7 perguntas, denso com reranking teve 7/7 e MRR@5 0,929, superando o modo híbrido (7/7; 0,821). Num primeiro holdout de 15 perguntas, teve 15/15 e MRR 0,933. Era a melhor escolha para aquele conjunto, não para qualquer domínio.
- **Reorientação de domínio:** com 15 perguntas de desenvolvimento sobre saúde da mulher e agendamento, o híbrido obteve 15/15 e MRR 0,833; denso e denso com reranking fizeram 9/15. No primeiro holdout v2, híbrido fez 23/25. Uma falha desse holdout motivou alteração no chunking; por isso a repetição do v2 não é uma medida independente.
- **Holdout v3 independente:** 25 perguntas novas, primeira e única execução em 28/09/2026. Híbrido 24/25, MRR@5 0,801; denso 19/25; denso com reranking 21/25. O critério mínimo do desenvolvimento (PassRate >= 0,90, MRR >= 0,75) passou. A única falha híbrida envolveu sinônimo coloquial de libido.
- **Respostas finais:** na primeira coleta com Groq/GPT-OSS 120B, 11 das 13 perguntas de domínio chegaram a `verified`; 2 caíram em fallback. Os 2 casos de urgência foram triados sem LLM e as 4 perguntas fora de escopo foram recusadas. A D054 atacou os fallbacks; falta repetir a coleta. A rubrica humana 0–2 de fidelidade, relevância e clareza foi definida, mas ainda não pontuada. A latência dessa coleta foi distorcida por erros 429 da cota Groq e não serve como medida de desempenho.

## 4. Decisões, erros, acertos e ideias

Os **porquês** das escolhas estão em [decisoes-tecnicas.md](decisoes-tecnicas.md) (D001–D054). Para começar: D005 (OCR), D006 e D046 (mudança do perfil padrão entre datasets), D008/D017 (dev, holdout e rótulos), D018–D023/D050–D054 (citações), D038 (FAQ), D039–D042 (triagem, ações e backend headless), D043–D045 (contrato, autenticação e e2e).

Os erros reproduzíveis e seus aprendizados estão em [dificuldades-tcc.md](dificuldades-tcc.md) (#1–#40). Exemplos úteis para uma futura equipe: #8 (PDF sem texto), #19–#26 (falhas e reparos do gate de citações), #34 (perfil antigo inadequado ao novo domínio), #35–#36 (recusa com citação falsa e fallback de mamografia), #38 (testes divergentes entre máquina e CI), #39 (cota Groq distorcendo latência) e #40 (item curto sem citação). O [esqueleto da monografia](monografia/ESQUELETO.md) mapeia capítulos para essas evidências. O diretório [`docs/historico/`](historico/) conserva o contexto anterior à reorientação; é material de consulta, não estado vigente. Especificações e planos de implementação antigos continuam versionados por registrarem o raciocínio de arquitetura. O prompt de retomada da 0.7.0 e o guia da interface 0.5.x foram retirados da árvore atual porque descreviam prioridades e comportamentos já superados; podem ser recuperados no histórico do Git.

As ideias futuras estão no [roteiro](ROTEIRO_EXECUCAO.md) e no [plano](PLANO_FINALIZACAO_TCC.md), marcadas como pendentes: nova coleta e rubrica, conjunto final de avaliação, relatórios operacionais, adaptador LangChain, homologação, exemplos de integração em TypeScript/Dart, estudo de usabilidade e monografia. Elas não devem ser descritas como funcionalidades prontas.

## 5. Bibliografia e fontes

O repositório contém **documentos-fonte do RAG**, mas ainda **não contém bibliografia acadêmica final em ABNT**. O catálogo referencia diretrizes de rastreamento do Ministério da Saúde/INCA, a Nota Técnica 626/2025 para mamografia, a Caderneta da Gestante e os FAQs CHATSCM; o arquivo [FONTES_E_REFERENCIAS.md](FONTES_E_REFERENCIAS.md) separa o corpus realmente entregue das referências apenas citadas no catálogo. Títulos, datas, versões e URLs devem ser verificados antes de citação em trabalho acadêmico. O capítulo de fundamentação ainda precisa de referências lidas e formalizadas sobre RAG, embeddings, BM25, RRF, alucinação, avaliação e letramento em saúde.

## 6. Estado de validação e limites

O [estado atual](ESTADO_ATUAL.md) registrava, em 28/09/2026, 339 testes backend aprovados (5 ponta a ponta), Ruff limpo, 19 testes frontend aprovados e TypeScript sem erros. São resultados daquela sessão; execute os comandos novamente no seu ambiente. Não há evidência de integração com o app real, estudo com participantes, cálculo SUS, rubrica concluída, holdout final v4, homologação real ou monografia final. O cliente Expo é demonstrativo. As respostas não substituem avaliação de profissionais de saúde e não foram clinicamente validadas.

## 7. Como retomar

1. Leia [`AGENTS.md`](../AGENTS.md), [ROTEIRO_EXECUCAO.md](ROTEIRO_EXECUCAO.md), [ESTADO_ATUAL.md](ESTADO_ATUAL.md), [PLANO_FINALIZACAO_TCC.md](PLANO_FINALIZACAO_TCC.md) e [INTEGRACAO.md](INTEGRACAO.md), nessa ordem. Confirme no GitHub se a branch de transferência já foi mesclada; o estado do Git pode mudar depois desta fotografia.
2. Prepare Python 3.12, Node.js e Docker Compose. Em ambiente local, use `python -m pip install -e ".[dev]"`, `pytest`, `ruff check .`, `cd frontend && npm test && npm run typecheck`, e `docker compose config`. Os testes usam providers falsos quando necessário; avaliações reais exigem Docker, rede e credenciais configuradas localmente.
3. Se precisar recriar o índice, siga `ragtest-plan-ingestion-sync` e depois `ragtest-sync-ingestion --apply`. Não use `ragtest-ingest --recreate` nem destrua volumes existentes. O corpus autorizado é somente `data/source/`.
4. Se o TCC prosseguir, comece pelas pendências registradas no [estado atual](ESTADO_ATUAL.md): publicar/mesclar a branch, repetir a coleta após D054 e aplicar a rubrica. Siga o [roteiro](ROTEIRO_EXECUCAO.md) para as etapas seguintes, preservando a independência dos holdouts.
5. Antes de uma entrega acadêmica, combine o escopo com o orientador; revise conteúdo clínico e bibliografia, execute avaliação final e redija a monografia. Registre resultados brutos e diferencie hipótese, código implementado, teste automatizado e validação com pessoas.
