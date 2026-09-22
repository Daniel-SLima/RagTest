# Design da 0.6.0 — Sessões conversacionais portáveis

**Data:** 2026-09-21

**Status:** arquitetura aprovada em conversa; consolidação escrita aguardando revisão

**Branch:** `feature/sessions-0.6.0`

## 1. Objetivo e alinhamento com o TCC

O RagTest deve ser um módulo conversacional RAG completo, independente e integrável ao
Se Cuida Mulher ou a qualquer outro sistema por meio de contratos públicos. O cliente Expo
existente é somente um consumidor demonstrativo; regras de sessão, contexto, segurança,
retrieval e grounding pertencem ao backend.

A 0.6.0 introduz sessões multi-turn persistentes sem acoplar o núcleo RAG a um frontend,
provider de LLM ou banco transacional específico. A troca entre Gemini, Groq, Ollama ou um
provider futuro deve continuar restrita à abstração `LLMProvider` já existente.

## 2. Escopo

### Incluído

- criação, consulta e exclusão de sessões;
- histórico persistente de turnos concluídos;
- `session_id` opcional no contrato de chat;
- contextualização limitada e segura de perguntas referenciais;
- abstração de armazenamento com SQLite como implementação inicial;
- expiração, limites e proteção contra concorrência na mesma sessão;
- persistência em volume Docker separado;
- testes de unidade, integração e regressão do modo stateless;
- documentação do contrato e das limitações de privacidade.

### Fora do escopo

- autenticação e autorização de usuárias;
- associação definitiva entre sessão e identidade do Se Cuida Mulher;
- painel administrativo ou listagem global de sessões;
- streaming ou WebSocket;
- estilização ou integração da sessão no cliente Expo;
- auditoria persistente completa, anonimização e políticas finais de LGPD;
- integração real com agenda, lembretes ou serviços institucionais;
- alteração de corpus, embeddings, retrieval base ou collection Qdrant.

## 3. Alternativas avaliadas

### Memória do processo

É simples, mas perde o histórico após reinício e não atende a portabilidade operacional
esperada para o artefato. Foi rejeitada como persistência principal.

### Histórico controlado pelo cliente

Manteria o backend stateless, porém transferiria regras de domínio para cada integração,
ampliaria o payload e permitiria que históricos fossem modificados livremente. Foi rejeitada
como contrato principal.

### Armazenamento persistente abstrato com SQLite padrão

Foi selecionado por funcionar localmente e em Docker sem serviço adicional, preservando uma
interface que poderá receber outra implementação, como PostgreSQL, sem alterar a API nem o
serviço conversacional.

## 4. Arquitetura

```text
Cliente integrador
    -> API REST / FastAPI
       -> ConversationService
          -> SessionStore (abstração)
             -> SQLiteSessionStore (implementação padrão)
          -> núcleo RAG
             -> retrieval / grounding
             -> LLMProvider (abstração existente)
```

`ConversationService` coordena sessão, contexto e execução do RAG. O pipeline RAG continua
responsável apenas por recuperar evidências e gerar uma resposta fundamentada. O
`SessionStore` não conhece FastAPI, Qdrant nem providers de LLM.

## 5. Contrato REST

### `POST /v1/sessions`

Cria uma sessão vazia e retorna:

- `session_id` em UUID opaco;
- `created_at`;
- `updated_at`;
- `expires_at`;
- `status`.

### `GET /v1/sessions/{session_id}`

Retorna metadados e turnos concluídos em ordem crescente. Não haverá endpoint para listar
todas as sessões. Uma sessão inexistente retorna `404`; uma sessão conhecida, mas expirada,
retorna `410` enquanto ainda não tiver sido eliminada pela limpeza de retenção. Após a remoção
física, passa a retornar `404`.

### `DELETE /v1/sessions/{session_id}`

Exclui a sessão e seus turnos de forma definitiva e retorna `204`. A repetição após a exclusão
retorna `404`.

### `POST /v1/chat`

`ChatRequest` recebe `session_id: UUID | None`. Sem o campo, a chamada mantém o comportamento
stateless atual e não cria armazenamento implícito. Com o campo, o backend carrega o contexto,
executa o RAG e grava o turno somente quando houver uma resposta concluída.

`ChatResponse` recebe `session_id: UUID | None`, preservando todos os campos atuais. Clientes
existentes continuam compatíveis, pois o novo campo é opcional e o fluxo stateless não muda.

## 6. Modelo de dados

### Sessão

- identificador UUID;
- criação, última atualização e expiração;
- revisão monotônica;
- estado necessário ao controle de concorrência;
- instante limite de eventual lease de processamento.

### Turno concluído

- identificador e sequência dentro da sessão;
- pergunta e resposta;
- timestamps;
- modelo utilizado;
- estado de grounding e citações;
- fontes apresentadas;
- dados de retrieval e decomposição já expostos pelo contrato.

Não serão persistidos chaves, segredos, prompts internos completos, embeddings, conteúdo
integral dos documentos ou erros brutos de providers.

## 7. Contextualização e grounding

O contexto será limitado por quantidade de turnos e caracteres. Os padrões iniciais serão
seis turnos usados como contexto, vinte turnos mantidos por sessão e retenção de sete dias;
todos serão configuráveis.

Para melhorar perguntas referenciais sem adicionar obrigatoriamente uma nova chamada ao LLM,
a consulta de retrieval será formada deterministicamente pela pergunta atual e pelo contexto
recente relevante. O prompt de resposta receberá uma seção de histórico explicitamente
marcada como dado não confiável e não probatório.

Citações antigas serão removidas da representação contextual para não colidirem com a
numeração das fontes atuais. O histórico pode esclarecer a intenção, mas nunca sustentar uma
afirmação. A resposta deve continuar apoiada exclusivamente nas fontes recuperadas para a
pergunta atual. Sem evidência atual suficiente, permanece o fallback seguro.

## 8. Consistência e concorrência

Somente turnos concluídos serão gravados. Falhas de provider, timeout ou validação antes da
resposta final liberam a sessão sem criar turnos parciais.

O armazenamento oferecerá aquisição atômica de uma lease curta por sessão. Enquanto uma
chamada estiver em andamento, outra tentativa na mesma sessão retorna `409`. A lease terá
expiração para recuperação após interrupção do processo e funcionará mesmo com mais de uma
instância da API usando o mesmo armazenamento compatível.

A gravação final validará a revisão lida no início da operação. Divergências serão tratadas
como conflito, nunca como sobrescrita silenciosa.

## 9. Privacidade e segurança

O UUID funciona apenas como identificador opaco, não como autenticação forte. Na 0.6.0, quem
possuir o identificador poderá consultar ou excluir a sessão. Essa limitação será explícita na
documentação e impede classificar a versão como pronta para produção com dados pessoais reais.

Não serão registrados conteúdos de perguntas e respostas nos logs operacionais comuns. A fase
0.7.x adicionará autenticação integrável, política de auditoria, minimização, anonimização e
controles finais de LGPD. O endpoint de exclusão e a retenção curta já aplicam minimização no
recorte atual.

## 10. Configuração e implantação

Configurações previstas:

- caminho do banco de sessões;
- retenção em dias;
- máximo de turnos armazenados;
- máximo de turnos e caracteres usados como contexto;
- duração da lease.

O Dockerfile preparará um diretório gravável pelo usuário não privilegiado da API. O Compose
montará um volume nomeado exclusivo nesse diretório. O volume do Qdrant e o corpus permanecem
inalterados.

O SQLite usará chaves estrangeiras, timeout para contenção e migrações versionadas pelo
próprio módulo. A inicialização será idempotente. A limpeza de registros expirados ocorrerá de
forma oportunística e limitada, sem bloquear o início da API nem manter indefinidamente o
conteúdo de sessões vencidas.

## 11. Tratamento de erros

- `404`: sessão inexistente;
- `409`: sessão já processando ou revisão concorrente;
- `410`: sessão expirada;
- `422`: identificador ou payload inválido;
- erros `502` e `503` atuais do fluxo de LLM permanecem com a mesma semântica.

Mensagens públicas não devem expor caminhos, SQL, providers, chaves ou detalhes internos.

## 12. Testes e critérios de aceite

A implementação seguirá TDD RED -> GREEN. Devem existir testes para:

- contrato e comportamento do `SessionStore`;
- persistência após reabertura do SQLite;
- criação, leitura, expiração e exclusão;
- limites de turnos e contexto;
- remoção de citações antigas no contexto;
- uso do histórico para retrieval sem transformá-lo em evidência;
- gravação apenas após resposta concluída;
- lease, conflito e recuperação após expiração;
- compatibilidade integral do chat stateless;
- respostas e códigos HTTP dos novos endpoints;
- ciclo de vida da aplicação e volume Docker.

Nenhum teste da 0.6.0 deve chamar provider externo, recriar a collection ou modificar o corpus.

## 13. Sequência de entrega

1. contratos de domínio e testes do armazenamento;
2. implementação SQLite e ciclo de vida;
3. serviço conversacional e concorrência;
4. contextualização segura do retrieval e prompt;
5. endpoints e schemas;
6. configuração e Docker;
7. regressão completa e documentação;
8. avaliação multi-turn em versão posterior da 0.6.x.

O plano de implementação detalhado só será escrito após a revisão e aprovação desta
consolidação.
