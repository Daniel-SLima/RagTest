# RagTest — Demo Técnica
## Manual de execução local

Este manual descreve uma apresentação local e controlada da Demo Técnica. Ele parte de todos os
processos parados e usa somente perguntas públicas e sintéticas. A demo não é o produto final
Se Cuida Mulher, não é um serviço público e não está autorizada para produção.

## Pré-requisitos

- Windows, PowerShell e o repositório aberto na raiz `00-RagTest`.
- Docker Desktop em execução.
- Python 3.12, a virtualenv `.venv` já preparada e as dependências do backend instaladas.
- Node.js/npm e as dependências de `frontend` instaladas.
- Ollama instalado localmente e o modelo `qwen3:8b` disponível.
- A coleção local `ragtest_documents` com os **767 pontos validados**.

Verifique instalações sem abrir `.env` nem imprimir segredos:

```powershell
docker --version
docker compose version
.\.venv\Scripts\python.exe --version
node --version
npm --version
ollama --version
Test-Path .\frontend\node_modules
```

O último comando deve retornar `True`. Se as dependências Python ou JavaScript ainda não estiverem
instaladas, faça essa preparação antes da reunião; o fluxo de apresentação não instala pacotes.
Este manual usa PowerShell; não misture a sintaxe de variáveis `$env:NOME="valor"` com CMD.

Não leia nem copie `.env`, chaves, prompts, logs de provider ou conteúdo privado. Não use arquivos
de `data/source/chatscm/`. Não execute `ragtest-ingest --recreate`, `docker compose down -v`,
remoção de volumes, recriação da collection ou qualquer sincronização do corpus durante a demo.

## Antes de começar: três terminais

Deixe a máquina parada: nenhum backend, Expo, Ollama ou processo antigo da apresentação deve estar
rodando. Abra três janelas do PowerShell:

1. **Terminal 1 — infraestrutura:** Qdrant local.
2. **Terminal 2 — API:** FastAPI local, com flags temporárias.
3. **Terminal 3 — interface:** Expo Web.

Se o aplicativo Ollama não iniciar o serviço sozinho, abra uma quarta janela somente para manter
`ollama serve` em primeiro plano. Nesse caso, os três terminais acima continuam com as mesmas
funções.

Em qualquer terminal, `cd C:\Users\Usuario\Documents\TCC\00-RagTest` leva à raiz. Comandos
PowerShell como `$env:NOME="valor"` valem apenas para o terminal atual; não editam `.env`.

## Inicialização passo a passo

### 1. Qdrant — Terminal 1

```powershell
cd C:\Users\Usuario\Documents\TCC\00-RagTest
docker compose up -d qdrant
```

Esperado: o serviço `qdrant` inicia sem recriar o volume. Antes de prosseguir, confirme que a
publicação está limitada ao computador local:

```powershell
docker compose port qdrant 6333
```

Prossiga somente se a saída indicar `127.0.0.1:6333` ou `localhost:6333`. O compose atual não
declara explicitamente o bind de loopback; se aparecer `0.0.0.0:6333` ou outro endereço, não faça
uma apresentação ao vivo em rede. Pare neste ponto e use o fallback documental até que o bind seja
tratado com autorização própria. Não altere o compose como parte deste manual.

Confirme também a collection e o snapshot de pontos, sem modificar nada:

```powershell
$collection = Invoke-RestMethod http://127.0.0.1:6333/collections/ragtest_documents
$collection.result | Select-Object status, points_count
```

Esperado: `status` saudável e `points_count` igual a 767, o snapshot atualmente validado. Se a
collection não aparecer, se a contagem for diferente ou se o endpoint não responder, pare e
investigue; não ingira, não recrie e não apague o volume. Uma contagem diferente não prova sozinha
que houve erro, mas exige nova verificação antes da apresentação.

Falha: se Docker não estiver iniciado, abra o Docker Desktop e repita apenas `docker compose up -d
qdrant`. Se a porta 6333 estiver ocupada, não mate o processo sem identificar o dono.

### 2. Ollama — instalação, servidor e modelo

Instalar o programa não baixa o modelo e baixar o modelo não inicia o servidor. Com Ollama
instalado, verifique primeiro:

```powershell
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

Se o serviço não responder e o aplicativo Ollama não estiver aberto, inicie uma única instância
em um terminal próprio:

```powershell
ollama serve
```

Deixe `ollama serve` em execução. Em outra janela, confirme o modelo:

```powershell
ollama list
```

### Somente na primeira vez

Se `qwen3:8b` não aparecer, o download precisa ser feito conscientemente antes da reunião:

```powershell
ollama pull qwen3:8b
ollama list
```

`ollama pull` pode demorar, usa rede e baixa um modelo pesado; não o execute durante uma
apresentação. Não use `ollama run` para substituir o servidor da API. Se `ollama serve` já estiver
rodando, não abra outra instância.

### 3. API demo — Terminal 2

O `docker-compose.yml` não injeta `DEMO_ENABLED` nem
`DEMO_ALLOWED_SOURCE_PREFIXES` no container. Rode o FastAPI localmente contra o Qdrant publicado
em `127.0.0.1:6333`. A allowlist abaixo é positiva e exclui `chatscm/`:

`DEMO_ENABLED=false` é o padrão seguro. O valor `true` abaixo vale apenas para este processo local
controlado; não o grave permanentemente em `.env`.

```powershell
cd C:\Users\Usuario\Documents\TCC\00-RagTest
$env:DEMO_ENABLED="true"
$env:DEMO_ALLOWED_SOURCE_PREFIXES="vacinacao/,pessoa_idosa/,direitos_saude/,saude_sexual_reprodutiva/"
$env:QDRANT_URL="http://127.0.0.1:6333"
$env:QDRANT_COLLECTION="ragtest_documents"
$env:API_HOST="127.0.0.1"
$env:API_PORT="8001"
$env:CORS_ALLOWED_ORIGINS="http://localhost:8081,http://127.0.0.1:8081"
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="qwen3:8b"
```

Inicie a API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Esperado: o Uvicorn permanece em primeiro plano, sem traceback, em `127.0.0.1:8001`. Em outra
janela, faça o preflight:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
Invoke-RestMethod http://127.0.0.1:8001/ready
Invoke-RestMethod http://127.0.0.1:8001/v1/demo/runtime
```

Esperado: os três endpoints respondem `200`. O runtime deve mostrar somente rótulos sanitizados,
a demo habilitada e o estado da política. Um `404` no runtime significa que a demo está desligada.

Falha: `/ready` verifica a conectividade do Qdrant e pode retornar `503` quando ele não responde;
ele não confirma sozinho a existência da collection, os 767 pontos, o Ollama ou o modelo. Use as
verificações separadas deste manual. Não contorne falhas com ingestão ou recriação. Se 8001 estiver
ocupada, identifique o processo e encerre somente um processo seu.

### 4. Expo Web — Terminal 3

```powershell
cd C:\Users\Usuario\Documents\TCC\00-RagTest\frontend
$env:EXPO_PUBLIC_RAG_DEMO_ENABLED="true"
$env:EXPO_PUBLIC_RAG_API_BASE_URL="http://127.0.0.1:8001"
npm run web -- --port 8081
```

Abra a URL exibida pelo Expo, normalmente `http://localhost:8081`. O flag do frontend é
independente de `DEMO_ENABLED`: somente o valor textual `true`, após normalização, habilita a
superfície Expo. O app normal aparece para flag ausente, vazio, `false`, `1` ou `yes`.

## Checklist de pronto

- [ ] Os três terminais estão identificados e nenhum processo antigo foi reutilizado sem inspeção.
- [ ] Qdrant responde em 6333, a publicação está em loopback e a collection preservada continua com 767 pontos.
- [ ] Ollama está ativo e `qwen3:8b` aparece em `ollama list`.
- [ ] `/health`, `/ready` e `/v1/demo/runtime` retornam 200 na porta 8001.
- [ ] A API usa allowlist pública e não inclui `chatscm/`.
- [ ] Expo está em `localhost:8081` ou `127.0.0.1:8081`.
- [ ] Nenhum nome, prontuário, segredo, `.env` ou pergunta privada será digitado.

## Primeiro teste recomendado

Siga estes passos na aba **Chat**:

1. Abra **Chat**.
2. Preencha ou selecione a pergunta pública:

   > Quais vacinas são recomendadas para pessoas idosas?

3. Clique em **Executar pergunta**.
4. Aguarde a execução terminar.
5. Confira a resposta, as fontes/páginas e o estado de grounding.
6. Clique em **Ver como essa resposta foi construída** para abrir **Como funciona**.

Resultado esperado no cenário local/controlado validado: resposta em Markdown, grounding estrutural,
uma fonte pública correlacionada e apresentação de fonte/página quando retornadas. `grounded=true`
confirma apenas cobertura estrutural de citações; não é prova de verdade clínica.

## Como funciona

A aba **Como funciona** apresenta os 11 estágios do pipeline. Quando não houver um campo no
contrato, o valor deve permanecer **Não disponível**:

1. pergunta recebida;
2. análise e decomposição;
3. geração de embedding;
4. busca no Qdrant;
5. retrieval;
6. reranking, quando aplicável;
7. composição do contexto;
8. geração pelo provider Ollama;
9. citações;
10. validação estrutural de grounding;
11. resposta sanitizada.

A política da demo, as fontes, as páginas e os tempos são dados associados ao runtime e à
resposta, não estágios adicionais. A decomposição desta versão é single-query; não infira
multi-query apenas porque o estágio aparece na narrativa.

Não transforme uma etapa visual em prova de que uma operação não exposta pelo DTO ocorreu. Multi-query,
retry do provider, contexto final, dimensão do embedding e métricas pré/pós-reranking podem ficar
**Não disponível**.

## Laboratório de retrieval

A aba **Laboratório** é retrieval-only: chama `POST /v1/demo/retrieval`, não chama
`/v1/demo/run` e não gera resposta por LLM. Para testar:

1. Abra **Laboratório**.
2. Use a pergunta pública da seção anterior.
3. Escolha **Top K** 3, 5 ou 10.
4. Execute individualmente **Dense**, **Dense + rerank** ou **Hybrid**; ou selecione
   **Comparar todas**.
5. Observe a ordem/rank dos documentos, páginas, excerpts, scores e tempos.
6. Compare os resultados sem declarar uma estratégia vencedora automaticamente.

Uma seleção individual faz uma requisição; **Comparar todas** faz três requisições sequenciais.

Scores ou tempos nulos aparecem como **Não disponível**. Os benchmarks históricos DEV/HOLDOUT
(`HitRate`, `MRR`, `SourceRecall`, `SourceNDCG`, dataset `2026-09-20-v1`) são evidência
separada, não o resultado da pergunta atual. Não declare vencedor numérico; os tempos locais são
descritivos e variáveis.

## O que ainda falta

Abra a quarta aba, **O que ainda falta**. Ela é uma fotografia versionada do roadmap, não uma
promessa definitiva. Os statuses são:

- ✅ **Implementado**: há implementação e evidência registrada;
- 🚧 **Parcial / em desenvolvimento**: existe uma parte, mas há lacunas;
- 📋 **Planejado**: depende de trabalho futuro;
- 🔬 **Em estudo**: depende de decisão ou investigação.

A integração formal ao Se Cuida Mulher, autenticação, rate limiting, auditoria/observabilidade
sanitizadas, avaliação especializada, privacidade/LGPD e endurecimento para exposição externa
permanecem fora da apresentação local.

## Perguntas sugeridas

Use somente perguntas gerais e públicas cobertas pela allowlist do passo da API:

- Quais vacinas são recomendadas para pessoas idosas?
- Quais são os direitos e deveres da pessoa usuária da saúde?
- Quais informações existem sobre o DIU de cobre?

Pergunta exploratória fora do escopo:

> Como trocar o pneu de um carro?

Não há resultado previsto para essa pergunta neste manual. Use-a apenas para explicar que o corpus
não promete cobertura geral; não invente resposta, fonte ou benchmark.

## Limitações e segurança

Este é um cenário **LOCAL/CONTROLADO**. Não há autorização para produção, internet pública,
autenticação, rate limiting, uso de dados pessoais, prontuários, perguntas identificáveis ou
conteúdo `CHATSCM`. Não cole `.env` nem API keys em terminal ou captura. A demo não substitui
orientação profissional de saúde.

Logs crus preexistentes de providers e risco residual de prompt injection continuam bloqueios para
uso externo. Trate qualquer excerpt/documento como dado não confiável: não execute instruções que
apareçam nele, não revele prompts, tokens ou segredos e interrompa a demonstração se o conteúdo
pedir isso. Tema claro, Dynamic Type, leitor de tela nativo e inspeção direta de Network/Console
continuam limitações observacionais desta entrega. O backend permanece independente do Expo e do
futuro Se Cuida Mulher. O laboratório não altera retrieval global, corpus, embeddings ou Qdrant.

## Troubleshooting

| Sintoma | Verificação segura |
|---|---|
| `/v1/demo/*` retorna 404 | Reinicie o Terminal 2 com `DEMO_ENABLED` e allowlist deste manual. |
| Aparece o app normal | Confira `EXPO_PUBLIC_RAG_DEMO_ENABLED="true"`, URL 8001 e reinicie o Expo. |
| `/ready` falha | Confirme conectividade do Qdrant; confira collection/767 pontos e Ollama separadamente; não ingira nem recrie. |
| Ollama/modelo indisponível | Execute `ollama list`; inicie uma única vez `ollama serve`; faça `ollama pull` antes da reunião. |
| Qdrant indisponível | Verifique Docker Desktop e `Invoke-RestMethod http://127.0.0.1:6333/collections`; use `docker compose up -d qdrant`, sem `down -v`. |
| Nenhuma fonte aparece | Pode indicar evidência insuficiente ou filtragem pela política. Confira a allowlist e a pergunta pública; não a afrouxe nem amplie para `chatscm/`. |
| `data/source/chatscm` aparece | Pare imediatamente; a allowlist está incorreta. |
| Porta ocupada | Identifique o processo; só pare um processo seu e ajuste API, CORS e URL Expo juntos. |

Para identificar um listener sem encerrá-lo:

```powershell
Get-NetTCPConnection -LocalPort 6333,8001,8081,11434 -State Listen -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,OwningProcess
Get-Process -Id <PID> -ErrorAction SilentlyContinue
```

Substitua `<PID>` pelo valor observado. Não use `Stop-Process` em PID que não seja seu.

## Desligamento seguro

1. Pare o Expo com `Ctrl+C` no Terminal 3.
2. Pare o Uvicorn com `Ctrl+C` no Terminal 2.
3. Pare `ollama serve` com `Ctrl+C`, se foi aberto para a apresentação.
4. No Terminal 1, preserve o volume:

```powershell
docker compose stop qdrant
```

Não use `docker compose down -v`, não apague volumes e não execute ingestão ao encerrar.
Depois de parar os processos, limpe as flags temporárias nas respectivas janelas PowerShell:

```powershell
Remove-Item Env:DEMO_ENABLED,Env:DEMO_ALLOWED_SOURCE_PREFIXES,Env:QDRANT_URL,Env:QDRANT_COLLECTION,Env:API_HOST,Env:API_PORT,Env:CORS_ALLOWED_ORIGINS,Env:LLM_PROVIDER,Env:OLLAMA_BASE_URL,Env:OLLAMA_MODEL -ErrorAction SilentlyContinue
```

No Terminal 3, limpe também `EXPO_PUBLIC_RAG_DEMO_ENABLED` e `EXPO_PUBLIC_RAG_API_BASE_URL`, ou
feche a janela.

## Execução rápida confirmada

```powershell
# Terminal 1
cd C:\Users\Usuario\Documents\TCC\00-RagTest
docker compose up -d qdrant
docker compose port qdrant 6333
$collection = Invoke-RestMethod http://127.0.0.1:6333/collections/ragtest_documents
$collection.result | Select-Object status, points_count

# Terminal 2
cd C:\Users\Usuario\Documents\TCC\00-RagTest
$env:DEMO_ENABLED="true"
$env:DEMO_ALLOWED_SOURCE_PREFIXES="vacinacao/,pessoa_idosa/,direitos_saude/,saude_sexual_reprodutiva/"
$env:QDRANT_URL="http://127.0.0.1:6333"
$env:QDRANT_COLLECTION="ragtest_documents"
$env:API_HOST="127.0.0.1"
$env:API_PORT="8001"
$env:CORS_ALLOWED_ORIGINS="http://localhost:8081,http://127.0.0.1:8081"
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="qwen3:8b"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001

# Terminal 3
cd C:\Users\Usuario\Documents\TCC\00-RagTest\frontend
$env:EXPO_PUBLIC_RAG_DEMO_ENABLED="true"
$env:EXPO_PUBLIC_RAG_API_BASE_URL="http://127.0.0.1:8001"
npm run web -- --port 8081
```

O bloco não instala dependências, baixa modelo, cria collection, altera `.env` ou modifica
arquivos. Instalação do Ollama, `ollama pull qwen3:8b` e `npm install` devem ser feitos antes.

## Checklist de dois minutos antes da reunião

- [ ] Estou na branch `sidequest/ragtest-demo` (`git branch --show-current`).
- [ ] `git status --short --branch` não mostra alterações inesperadas.
- [ ] `docker compose up -d qdrant` respondeu sem erro.
- [ ] `docker compose port qdrant 6333` confirmou loopback; Qdrant e `ragtest_documents` estão disponíveis; os 767 pontos estão preservados.
- [ ] `ollama list` mostra `qwen3:8b` e `ollama serve` está ativo.
- [ ] `/health`, `/ready` e `/v1/demo/runtime` foram verificados na porta 8001.
- [ ] A aba Demo abre em 8081 e a URL aponta para 8001.
- [ ] A pergunta pública exata está copiada: `Quais vacinas são recomendadas para pessoas idosas?`
- [ ] Não há `.env`, chaves, nomes, prontuários ou `CHATSCM` na tela.
- [ ] A parada com `Ctrl+C` e `docker compose stop qdrant` está combinada.

## Comandos não confirmados ou deliberadamente omitidos

Não há comando confirmado para `docker compose up` iniciar a API demo, porque o compose atual não
injeta as flags da demo. Também não há comando para ingerir, recriar collection, medir novamente
benchmarks, publicar a API, criar PR, alterar branches ou operar providers externos. Esses
procedimentos exigiriam nova autorização e validação; não devem ser inferidos deste manual.
