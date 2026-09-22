# Design da 0.7.0-A — Auditoria estruturada segura

**Data:** 2026-09-22  
**Branch de implementação:** `feature/audit-0.7.0`  
**Base:** `main` após o merge da 0.6.0 (`f173a29`)  
**Status:** proposta aprovada em conversa; aguardando revisão desta especificação antes do plano TDD

## 1. Objetivo

Adicionar ao módulo RAG uma camada de auditoria estruturada, intercambiável e segura para
registrar o comportamento operacional da API sem transformar perguntas, respostas ou trechos
documentais em logs. O primeiro recorte deve permitir rastrear uma requisição de ponta a ponta,
diagnosticar falhas de provider e demonstrar no TCC que as respostas podem ser auditadas sem
expor conteúdo sensível.

O cliente Expo, o Qdrant, o corpus, os embeddings e o contrato funcional de `POST /v1/chat`
continuam independentes desta camada.

## 2. Problema e limites

Hoje existem logs pontuais de infraestrutura, mas não há um contrato único para responder:
quando uma operação ocorreu, qual requisição a originou, qual foi o resultado, quanto demorou e
qual classe de erro ocorreu. Também não há uma garantia testável de que uma instrumentação
futura não grave dados pessoais ou material documental não revisado.

Este recorte **inclui**:

- contexto de requisição com identificador opaco gerado pelo backend;
- eventos JSON estruturados para ciclo de vida de sessões e turnos de chat;
- sink abstrato que pode ser trocado por outro destino sem alterar rotas ou providers;
- saída inicial em logger estruturado, adequada para stdout de Docker;
- política determinística de minimização e testes que proíbem conteúdo sensível;
- documentação do contrato, dos limites e da integração.

Este recorte **não inclui**:

- autenticação, autorização ou identidade de usuária;
- armazenamento persistente de auditoria, endpoint de consulta ou dashboard;
- gravação de pergunta, resposta, prompt, histórico, trecho, nome de arquivo ou conteúdo de
  `chatscm`;
- fallback entre providers, streaming, alteração do retrieval ou reindexação;
- alegação de conformidade final com LGPD. O resultado é uma base técnica para revisão jurídica
  e política posterior.

## 3. Princípios de privacidade e segurança

1. **Minimização por construção:** o tipo de evento não terá campos genéricos como `payload`,
   `message` ou `details` nos quais uma rota poderia esconder conteúdo.
2. **Nenhum segredo:** API keys, headers de autorização, prompts completos e URLs com credenciais
   nunca entram no evento.
3. **Nenhum conteúdo documental:** fontes serão representadas apenas por contagens e metadados
   operacionais mínimos; não serão registrados `source`, `excerpt`, página ou texto recuperado.
4. **Identificadores opacos:** `request_id`, `event_id` e `session_id` serão UUIDs; o backend
   gera o `request_id` e devolve somente esse identificador em `X-Request-ID`.
5. **Falha não bloqueante:** se o sink não conseguir emitir um evento, a resposta funcional não
   será substituída por erro de auditoria. A falha do sink será registrada em logger técnico
   separado, sem repetir o evento com conteúdo.
6. **Providers explícitos:** o evento informa provider/modelo apenas como rótulo configurado;
   não haverá fallback ou chamada adicional causada pela auditoria.

## 4. Arquitetura proposta

### 4.1 Contexto de requisição

Um middleware ASGI cria um UUID por requisição, adiciona o valor a `request.state.request_id`
e devolve `X-Request-ID` na resposta. O middleware não aceita nem persiste um identificador
arbitrário enviado pelo cliente nesta primeira versão. Isso evita que um header controlado por
terceiros se torne um campo de log não validado.

### 4.2 Contrato do sink

O módulo `app/observability/audit.py` deverá expor uma interface pequena e provider-agnostic:

```python
class AuditSink(Protocol):
    def emit(self, event: AuditEvent) -> None: ...
```

`AuditEvent` será imutável e serializável como JSON. O evento terá somente campos tipados e
opcionais necessários à operação:

- `event_id`, `timestamp`, `request_id`;
- `event_type` e `outcome`;
- `operation` e `duration_ms`;
- `session_id` opcional;
- `provider` e `model` opcionais;
- `status_code`, `error_code` e `error_type` opcionais, normalizados para classes estáveis;
- `grounded`, `source_count`, `citation_count`, `citation_retry_count` e
  `retrieval_query_count` opcionais;
- `turn_count` opcional para eventos de snapshot de sessão.

O `JsonLogAuditSink` emitirá uma linha JSON determinística em `ragtest.audit`. Um sink de teste
em memória poderá capturar objetos sem interceptar ou analisar texto de log. Rotas receberão o
sink por estado/dependência, evitando instanciação global difícil de substituir.

### 4.3 Eventos mínimos

| Evento | Momento | Campos adicionais |
|---|---|---|
| `session.created` | sessão criada | `session_id`, `outcome=success` |
| `session.read` | snapshot retornado | `session_id`, quantidade de turnos |
| `session.deleted` | sessão removida | `session_id`, `outcome=success` |
| `chat.completed` | RAG concluído e, se aplicável, turno salvo | sessão, provider/modelo, grounding, contagens, duração |
| `chat.failed` | erro HTTP ou falha de provider | sessão opcional, código/classe normalizados, duração |

O evento de leitura de sessão usará uma contagem de turnos, nunca as perguntas ou respostas.
Operações de saúde e busca ficam fora do primeiro recorte para manter o contrato pequeno; podem
usar o mesmo sink em evolução posterior.

### 4.4 Composição com sessões

O chat stateless emite `chat.completed` ou `chat.failed` como qualquer outro chat. Quando há
`session_id`, o mesmo evento recebe apenas o UUID opaco da sessão. O histórico continua fora do
evento e permanece contexto não confiável. A auditoria será emitida depois do resultado conhecido
ou da exceção classificada, sem alterar a lease, a persistência SQLite ou a ordem dos turnos.

## 5. Tratamento de falhas

- Falhas conhecidas (`404`, `409`, `410`, `502`, `503`) serão convertidas em `error_code` e
  `error_type` estáveis, sem copiar `detail` bruto.
- Exceções inesperadas emitirão `error_code=internal_error` e `error_type=unhandled`, sem
  traceback no evento público. O logger técnico pode registrar traceback localmente conforme a
  configuração do ambiente.
- A emissão será protegida por uma função de segurança que captura exceções do sink. O erro do
  sink não deve causar retry do LLM, rollback adicional da sessão ou mudança de status HTTP.
- Duração será calculada monotonicamente e serializada como milissegundos não negativos.

## 6. Testes e critérios de aceitação

O plano TDD deverá cobrir, no mínimo:

1. serialização estável de `AuditEvent`, com timestamp UTC e ausência de campos proibidos;
2. rejeição/teste de contrato que garanta que pergunta, resposta, prompt, excerpt, source,
   authorization e API key não aparecem no JSON;
3. middleware que cria `request_id` e devolve o mesmo UUID em `X-Request-ID`;
4. emissão de `session.created`, `session.read` e `session.deleted` nas rotas correspondentes;
5. emissão de `chat.completed` para chat stateless e com sessão, preservando contagens e
   `grounded` sem conteúdo;
6. emissão de `chat.failed` para 503 e erro inesperado com classes normalizadas;
7. sink que falha não interrompe a resposta funcional nem a persistência do turno;
8. suíte existente, Ruff e validação Docker sem provider adicional ou reindexação.

Aceitação manual: uma chamada local a `/v1/chat` deve produzir eventos legíveis como JSON,
correlacionados pelo `X-Request-ID`, sem conter a pergunta usada no teste nem trechos do corpus.

## 7. Evolução posterior deliberadamente separada

Após este recorte, uma fase própria poderá avaliar retenção, acesso controlado, anonimização,
exportação, armazenamento durável e política LGPD com o orientador. Essa evolução não deve ser
implementada apenas porque o sink estruturado existe: cada campo persistido precisará de finalidade,
prazo e controle de acesso definidos.

## 8. Documentação e rastreabilidade

Durante a implementação, atualizar:

- `README.md` com o contrato de eventos e limites de privacidade;
- `docs/CONTEXTO_CONTINUIDADE.md` com o estado real da `main` e da branch 0.7.0-A;
- `docs/PROMPT_RETOMADA.md` com o próximo passo executável;
- `docs/decisoes-tecnicas.md` com uma decisão nova sobre auditoria minimizada;
- `docs/dificuldades-tcc.md` somente se surgir falha reproduzível de ambiente ou implementação;
- plano TDD e ledger da execução em `docs/superpowers/plans/` e `.superpowers/sdd/`.

## 9. Autorrevisão desta especificação

- Não há placeholders, dependência de provider específico ou instrução para enviar CHATSCM a
  serviços externos.
- O sink tem fronteira substituível e não altera o contrato de resposta do chat.
- Os eventos cobrem sucesso e falha, mas não prometem persistência nem conformidade jurídica.
- A ausência deliberada de conteúdo e de endpoint de consulta reduz risco nesta primeira etapa.
- Os critérios de aceitação cobrem serialização, correlação, rotas, falhas e não bloqueio; o plano
  TDD deverá transformar cada item em teste observável.
