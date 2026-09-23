# Contrato de trabalho dos agentes — RagTest

Este arquivo define regras operacionais. Ele não substitui o estado do projeto nem as decisões
históricas. Para reconstruir o contexto, leia nesta ordem:

1. `docs/CONTEXTO_CONTINUIDADE.md`;
2. `docs/decisoes-tecnicas.md`;
3. `docs/dificuldades-tcc.md`;
4. a especificação/plano da versão em andamento;
5. `README.md`, `docs/PROMPT_RETOMADA.md` e os testes relevantes.

## Fonte de verdade

Para o trabalho em andamento, compare evidências nesta ordem: workspace local sem descarte,
estado Git local e commits, especificação da tarefa, testes/comportamento observado, decisões
técnicas, contexto de continuidade, GitHub remoto e histórico da conversa. Se houver divergência
relevante, pare e relate-a; o remoto não substitui automaticamente o trabalho local.

## Orquestração

O agente principal é o ORCHESTRATOR. Para mudança funcional relevante, use:

`REVIEWER → DEVELOPER → QA → REVIEWER → DOCUMENTER → ORCHESTRATOR`.

Leituras independentes podem ocorrer em paralelo. Alterações no mesmo arquivo, função, contrato,
corpus ou collection Qdrant são sequenciais. O resultado de cada agente deve informar objetivo,
contexto consultado, evidências, arquivos, decisões, alterações, testes, problemas, riscos,
pendências e próxima etapa.

Não use o fluxo completo para uma leitura simples ou correção documental isolada. Não crie agentes
adicionais sem problema concreto, ganho esperado e permissões justificadas.

## Regras de Git e workspace

- Comece por `git status --short --branch`, branch, HEAD e comparação com o remoto.
- Preserve alterações locais e arquivos não rastreados.
- Não use `git reset --hard`, `git clean`, `git restore`, checkout destrutivo, rebase, force-push
  ou exclusão de branch.
- `git fetch origin` é permitido para comparação; pull, merge, push e qualquer sincronização
  dependem de autorização explícita do usuário.
- Não declare uma branch pronta sem testes e diff verificáveis.

## Regras técnicas e de teste

- Backend: Python 3.12, FastAPI, Pydantic Settings, Qdrant, providers Gemini/Groq/Ollama,
  pytest/pytest-asyncio e Ruff 0.16.8.
- Frontend: Expo/React Native/TypeScript, Jest/RNTL e `npm run typecheck`.
- QA pode executar ferramentas e permitir artefatos de teste, mas não deve modificar código de produção, testes ou documentação para fazer uma validação passar. Problemas devem ser reportados ao orquestrador.
- Mudanças funcionais seguem TDD: teste RED observável, implementação mínima, GREEN direcionado,
  suíte completa e lint. Validações Docker usam `docker compose config` e não recriam volumes.
- Não altere parâmetros de retrieval, embeddings, corpus ou collection sem especificação e
  autorização próprias.

## Privacidade e segurança

- Nunca leia, imprima, versione ou envie valores de `.env`/API keys.
- `data/source/chatscm/*.docx` não pode ser enviado a providers externos antes de revisão manual
  de privacidade.
- Logs e erros devem ser minimizados: não registrar perguntas, respostas, prompts, excerpts,
  conteúdo documental ou credenciais sem requisito explícito e revisão de privacidade.
- `grounded=true` é cobertura estrutural de citações, não prova de verdade clínica.
- O backend permanece independente do Expo e do futuro Se Cuida Mulher.

## Qdrant e ingestão

- Não execute `ragtest-ingest --recreate` nem `docker compose down -v`.
- Preserve corpus, embeddings, collection e os 767 pontos validados quando aplicável.
- Planeje/audite sincronizações antes de mutar Qdrant; prefira comandos de inspeção.

## Documentação

Toda mudança relevante atualiza `docs/CONTEXTO_CONTINUIDADE.md`. Decisões arquiteturais e
metodológicas entram em `docs/decisoes-tecnicas.md`; falhas reproduzíveis entram em
`docs/dificuldades-tcc.md`; uso e limitações públicas entram em `README.md`; retomada histórica
fica em `docs/PROMPT_RETOMADA.md`. Diferencie planejado, implementado, aguardando validação e
verificado. Não documente sucesso sem saída de comando ou teste correspondente.

## Autorizações

Peça autorização quando uma ação puder descartar/reescrever trabalho, alterar estado remoto,
fazer merge/push, usar provider externo com conteúdo novo, modificar corpus/Qdrant, instalar
dependência ou ampliar o escopo da versão. A configuração de agentes não autoriza nenhuma dessas
ações.
