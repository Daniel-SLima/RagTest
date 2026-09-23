# Roteiro de apresentação do RagTest — M6

Status do roteiro: **documental, com replay fora do escopo**. Este documento prepara uma
apresentação de 5–10 minutos usando apenas o build atual e evidências públicas/sintéticas. Não é
um procedimento de validação externa, produção, saúde ou conformidade LGPD.

## Regra de evidência

Use sempre um dos rótulos abaixo ao falar ou mostrar uma tela:

- **AO VIVO** — interação observada durante a reunião no build atual. A apresentação ao vivo é
  somente a navegação da interface e seus estados locais; não alegue provider, Qdrant, resposta
  gerada ou disponibilidade externa.
- **VALIDAÇÃO M5** — fato sustentado pelos gates e pela inspeção local/controlada registrados em
  `docs/demo-m1.md` e `docs/CONTEXTO_CONTINUIDADE.md`. A fotografia M5 usa o commit-base
  `75c924c`.
- **CAPTURA HISTÓRICA** — screenshot ou registro produzido em uma execução anterior. Não o
  apresente como execução da reunião nem como prova do build atual.

O build que será aberto hoje está no commit `0213d80` (reconciliação documental posterior). Isso
é diferente do snapshot M5 `75c924c`; a diferença deve ser dita antes de comparar uma tela com
uma captura histórica.

## Roteiro de 5–10 minutos

### 0:00–1:00 — enquadramento

1. **FORMA SIMPLES:** Explique que o RagTest é um módulo RAG portável com cliente Expo
   demonstrativo.
2. **SE O PROFESSOR QUISER DETALHES:** Diga explicitamente: “Esta apresentação mostra a
   superfície demonstrativa e a rastreabilidade
   da entrega; não é uma demonstração de produção, atendimento clínico ou integração oficial ao
   Se Cuida Mulher.”
3. **FORMA SIMPLES:** Mostre a identificação da versão/branch no catálogo, marcando como **AO
   VIVO** somente o que estiver visível no build atual.
4. **SE O PROFESSOR QUISER DETALHES:** Explique que o build atual é `0213d80`, enquanto a
   fotografia de validação M5 é `75c924c`; são referências diferentes.

### 1:00–3:00 — arquitetura e limites

1. **FORMA SIMPLES:** Abra `Como funciona` e percorra as etapas sem executar uma pergunta.
2. **SE O PROFESSOR QUISER DETALHES:** Mostre o fluxo conceitual: Demo/Expo → FastAPI →
   RAG/retrieval/grounding → Qdrant + provider.
3. **FORMA SIMPLES:** Explique que “aguardando execução”, Planejado e Em estudo são estados
   honestos do roadmap, não resultados fabricados.
4. **SE O PROFESSOR QUISER DETALHES:** Aponte que `grounded=true`, quando mencionado em
   evidência anterior, significa apenas cobertura estrutural de citações; não é prova de verdade
   factual, clínica ou entailment semântico.

### 3:00–5:30 — visão rastreável M5

1. **FORMA SIMPLES:** Abra `O que ainda falta` (**AO VIVO**).
2. **SE O PROFESSOR QUISER DETALHES:** Mostre `VISÃO GERAL`, as contagens e os filtros por
   status/área.
3. **FORMA SIMPLES:** Abra um accordion e mostre limitações e referências; não improvise uma
   evidência que não esteja no catálogo.
4. **SE O PROFESSOR QUISER DETALHES:** Mostre também detalhe técnico, dependências e a origem
   relativa do item.
5. **FORMA SIMPLES:** Explique que a validação M5 registrou 12 itens em 12 áreas: 6
   Implementados, 2 Parciais / em desenvolvimento, 3 Planejados e 1 Em estudo (**VALIDAÇÃO M5**).
6. **SE O PROFESSOR QUISER DETALHES:** Se usar uma tela gravada ou screenshot anterior, anuncie-a
   como **CAPTURA HISTÓRICA** e informe que pertence ao snapshot `75c924c`, não necessariamente ao
   build `0213d80`.

### 5:30–7:00 — o que foi verificado e o que não foi

**FORMA SIMPLES:** Diga o que foi observado e o que continua bloqueado.

**SE O PROFESSOR QUISER DETALHES:** Apresente a tabela abaixo, verbalmente ou em uma captura
sanitizada:


| Classificação | Pode ser afirmado | Não pode ser afirmado |
|---|---|---|
| **AO VIVO** | Navegação, filtros, accordions e textos que aparecem no build atual | Provider/Qdrant/retrieval real se não houver execução autorizada observável |
| **VALIDAÇÃO M5** | 13 suites/114 testes, typecheck, diff-check e inspeção Expo Web nos quatro viewports, conforme os registros | Produção, disponibilidade externa, segurança de produção ou validade clínica |
| **CAPTURA HISTÓRICA** | O que a imagem/registro mostra, com data e origem identificadas | Que a captura seja uma execução atual ou que prove mudança posterior |

### 7:00–8:30 — fallback seguro

Se a interface não abrir, não tente “consertar” durante a reunião nem faça replay. Mostre o
próprio roteiro e `docs/demo-m1.md`; use a seção M5 e as classificações acima como apresentação
documental. Se houver capturas, use somente as previamente sanitizadas. Registre a falha como
pendência, sem convertê-la em validação.

## Caminho AO VIVO opcional e preflight

Este caminho só deve ser usado se a reunião tiver autorização explícita para um ambiente
local/controlado. Ele não é replay e não transforma uma execução local em evidência de produção.

**FORMA SIMPLES:** confirme que a API local responde, que o armazenamento preservado está
disponível e que a interface aponta para a mesma API; se qualquer item falhar, aborte o caminho
AO VIVO e use o fallback documental.

**SE O PROFESSOR QUISER DETALHES:** faça, antes de abrir a tela, os checks somente de leitura:

1. API habilitada para a demo, com allowlist pública já revisada; não alterar `.env` durante a
   reunião.
2. `/health` e `/ready` respondendo pela API local configurada.
3. Qdrant local preservando os 767 pontos; não recriar collection, corpus ou embeddings.
4. Provider local Ollama disponível com o baseline `qwen3:8b`; nenhuma chave ou conteúdo privado.
5. Frontend apontando para a base URL correta da API. No cenário local/controlado previamente
   validado, use `EXPO_PUBLIC_RAG_API_BASE_URL=http://127.0.0.1:8001`; não confundir com uma
   composição local que exponha a API em outra porta.

Critério de abortar: qualquer falha em `/health`, `/ready`, contagem preservada, provider local,
allowlist, base URL, privacidade ou sanitização encerra o caminho AO VIVO. Não corrigir em tempo
de reunião, não trocar provider, não usar dados reais e não chamar replay; registrar “aguardando
validação” e seguir para capturas/roteiro.

Para uma apresentação local sem backend, os comandos existentes são suficientes:

```powershell
cd frontend
$env:EXPO_PUBLIC_RAG_DEMO_ENABLED="true"
npm run web
```

Não é necessário criar script de inicialização. Não executar `ragtest-ingest --recreate`,
`docker compose down -v`, recriação da collection, reindexação ou qualquer operação que altere
os 767 pontos preservados. Não habilitar provider externo, não usar dados pessoais e não abrir
`.env` durante a apresentação.

## Checklist pré-reunião

- [ ] Confirmar branch/build e registrar que o build atual é `0213d80`.
- [ ] Manter a distinção visível entre build atual e snapshot M5 `75c924c`.
- [ ] Abrir somente telas e textos sanitizados; preparar `docs/demo-m1.md` como fallback.
- [ ] Testar a navegação local sem depender de provider, Qdrant ou rede externa.
- [ ] **Opcional — AO VIVO:** confirmar API demo habilitada e allowlist pública revisada.
- [ ] **Opcional — AO VIVO:** verificar `/health` e `/ready` na base URL local configurada.
- [ ] **Opcional — AO VIVO:** confirmar Qdrant local com os 767 pontos preservados, sem recriação.
- [ ] **Opcional — AO VIVO:** confirmar Ollama local com `qwen3:8b`, sem expor chaves ou conteúdo.
- [ ] **Opcional — AO VIVO:** confirmar `EXPO_PUBLIC_RAG_API_BASE_URL` apontando para a API
      correta (cenário validado: `http://127.0.0.1:8001`); abortar se qualquer check falhar.
- [ ] Deixar exemplos públicos/sintéticos prontos; não usar `CHATSCM`, documentos privados ou
      perguntas de saúde reais.
- [ ] Conferir que nenhum terminal, variável, arquivo `.env`, token, path pessoal, log cru ou
      URL privada aparecerá na gravação/compartilhamento.
- [ ] Ter uma captura histórica identificada por data, origem e snapshot, caso seja necessária.
- [ ] Confirmar que replay funcional não será tentado.

## Critérios para screenshots sanitizadas

Uma captura só pode ser usada se mostrar apenas interface e texto público/sintético, sem secrets,
`.env`, tokens, paths pessoais, nomes de usuários, conteúdo `CHATSCM`, documentos privados,
URLs privadas, headers, payloads, logs crus ou mensagens de provider. Recorte ou oculte abas,
endereços e notificações fora do produto; revise a imagem em tamanho integral antes de exibir.
Identifique a captura com data, rótulo **CAPTURA HISTÓRICA** e commit/snapshot de origem. Se não
for possível comprovar a origem ou sanitização, não use a imagem.

## Perguntas prováveis e respostas seguras

**“Isso está em produção?”** Não. M5 foi validado somente em ambiente local/controlado; uso
externo/produção permanece bloqueado por pendências de segurança, autenticação, rate limiting,
logs sanitizados, privacidade e prompt injection.

**“A resposta está correta clinicamente?”** Não há essa conclusão. `grounded` descreve cobertura
estrutural de citações, não verdade clínica; avaliação especializada ainda é planejada.

**“Por que não mostrar um replay?”** Replay foi explicitamente mantido fora do escopo. O M6 usa
contingência documental/multimídia para não transformar uma captura histórica em evidência atual.

**“O que mudou desde M5?”** O catálogo M5 foi fotografado no commit `75c924c`; o build atual é
`0213d80`, posterior. A apresentação deve distinguir a inspeção atual das evidências daquele
snapshot, sem inferir mudanças funcionais não registradas.

**“O Se Cuida Mulher já está integrado?”** Não. É uma integração futura documentada; o cliente
Expo demonstrativo permanece separado do núcleo RAG.

**“Podemos ligar um provider ou usar dados reais agora?”** Não nesta apresentação. Isso exigiria
autorização, revisão de privacidade e validação operacional próprias.

## Bloqueios e pendências

- Replay funcional: **fora do escopo M6**.
- Provider/Qdrant ao vivo: **não usado como evidência desta apresentação**.
- Uso externo/produção: **bloqueado** pelos achados de segurança/privacy registrados pelos
  revisores, incluindo exposição potencial de conteúdo privado a providers, sessões sem
  autenticação, logs crus e risco residual de prompt injection.
- Tema claro, Dynamic Type, leitor de tela nativo e inspeção de Network/Console: limitações
  observacionais da validação M5, não sucessos presumidos.
- Validação externa autorizada, autenticação, rate limiting, observabilidade sanitizada, revisão
  de privacidade/LGPD e integração formal: **planejados/aguardando trabalho autorizado**.

## Fontes consultadas

- `AGENTS.md` — regras de privacidade, Git, Qdrant e classificação de evidências.
- `docs/CONTEXTO_CONTINUIDADE.md` — handoffs M1–M5, gates e bloqueios.
- `docs/demo-m1.md` — contratos, limites da demo e validação M5.
- `docs/decisoes-tecnicas.md` e `docs/dificuldades-tcc.md` — decisões e dificuldades históricas.
- `.superpowers/sdd/2026-09-23-ragtest-demo-m5/task-1-report.md` e `task-2-report.md` —
  evidências de catálogo, tela e testes.
- `.superpowers/sdd/2026-09-23-ragtest-demo-m6/progress.md` — gates Reviewer/QA/Security e
  decisão de contingência sem replay.
