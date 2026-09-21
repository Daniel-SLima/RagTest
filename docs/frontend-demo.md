# Front-end de demonstração do RagTest

## Objetivo

Criar um cliente multiplataforma independente para apresentar o módulo conversacional do TCC funcionando antes da integração com o aplicativo oficial Se Cuida Mulher.

O cliente é apenas um consumidor da API. O núcleo RAG, a ingestão, o retrieval, o grounding, o Qdrant e os providers de LLM continuam independentes da interface.

## Stack da 0.5.21

- Expo SDK 57 estável;
- React Native 0.86;
- React 19.2;
- TypeScript;
- Jest + jest-expo;
- React Native Testing Library;
- FastAPI/Qdrant permanecem como backend e camada RAG.

O SDK 58 não é adotado nesta etapa porque ainda está em beta.

## Arquitetura

    React Native / Expo
            |
            | REST / JSON
            v
        FastAPI
        POST /v1/chat
            |
            v
        Módulo RAG
        Retrieval
        Grounding
        Qdrant
        LLM provider

O aplicativo não contém regras de negócio do RAG. Ele conhece apenas o contrato público da API.

REST é o transporte inicial porque o endpoint já existe, é simples de testar e atende a demonstração. WebSocket fica reservado para uma necessidade concreta de streaming ou comunicação bidirecional contínua.

## Estado atual da 0.5.21

Implementado:

- scaffold Expo/React Native;
- configuração multiplataforma Android/iOS/web;
- primeira superfície visual do chat;
- campo de pergunta e botão Enviar;
- tipos TypeScript equivalentes a ChatRequest, ChatResponse e ChatSource do FastAPI;
- buildChatRequest para mapear o modelo do cliente para o contrato REST;
- sendChatMessage para POST em /v1/chat;
- testes com Jest/React Native Testing Library;
- typecheck TypeScript na CI.

Ainda não implementado nesta versão:

- conexão da tela com o cliente REST;
- estado de carregamento;
- renderização da resposta;
- fontes/citações na interface;
- configuração por ambiente da URL do backend.

Esses itens pertencem à próxima etapa de integração funcional.

## Primeira versão demonstrável planejada

A interface deverá evoluir para conter:

- cabeçalho do projeto;
- conversa entre usuária e assistente;
- mensagem inicial explicando o propósito do chatbot;
- campo de texto e envio;
- estado de carregamento;
- rich-text;
- fontes citadas e páginas consultadas;
- links quando suportados pelas fontes;
- indicador de grounding/fallback;
- painel técnico opcional para a banca mostrando modelo, citações, retrieval e métricas relevantes;
- posteriormente, gatilhos de lembrete/agendamento conforme os fluxos institucionais forem modelados.

O painel técnico é recurso de apresentação e diagnóstico, não requisito da experiência final da usuária.

## Integração futura com Se Cuida Mulher

A interface de demonstração não deve criar dependências no backend.

Quando o Se Cuida Mulher for integrado:

- se a stack for compatível, componentes do cliente poderão ser reaproveitados;
- se a stack for diferente, apenas a camada cliente/adaptadora precisa mudar;
- o FastAPI e o módulo RAG permanecem consumíveis pelo mesmo contrato.

## Fora do escopo inicial

- autenticação de usuárias;
- histórico persistente;
- banco transacional de conversas;
- streaming de tokens;
- fallback automático entre providers;
- alteração de corpus, embeddings ou Qdrant;
- ingestão automática sem aprovação;
- integração definitiva com o Se Cuida Mulher.


## Integração funcional — 0.5.22

A 0.5.22 conecta a tela ao backend real mantendo o mesmo contrato REST.

Implementado:

- CORS restrito/configurável no FastAPI para Expo Web;
- URL da API configurável por `EXPO_PUBLIC_RAG_API_BASE_URL`;
- padrão web local em `http://localhost:8000`;
- cliente REST conectado ao botão Enviar;
- mensagem da usuária renderizada na conversa;
- estado `Buscando resposta...`;
- resposta textual do `/v1/chat` renderizada;
- bloqueio de envio vazio ou com menos de 2 caracteres;
- bloqueio de novo envio enquanto a chamada está em andamento;
- tratamento de erro de rede na interface;
- `ChatApiError` para HTTP não-2xx, preservando status e `detail` do FastAPI.

Configuração de ambiente:

    # web na mesma máquina
    EXPO_PUBLIC_RAG_API_BASE_URL=http://localhost:8000

    # Android Emulator
    EXPO_PUBLIC_RAG_API_BASE_URL=http://10.0.2.2:8000

    # dispositivo físico
    EXPO_PUBLIC_RAG_API_BASE_URL=http://IP_DA_MAQUINA:8000

Para Expo Web, a origem usada pelo navegador também precisa constar em `CORS_ALLOWED_ORIGINS` no backend.

A 0.5.22 ainda mostra a resposta como texto simples. Rich-text, cartões de fontes/citações e apresentação de grounding pertencem às versões seguintes.


## Rich-text e fontes — 0.5.23

A 0.5.23 melhora a apresentação das respostas sem alterar o contrato do FastAPI.

Implementado:

- renderização Markdown nativa no cliente com `@ronradtke/react-native-markdown-display`;
- negrito, listas e demais elementos suportados deixam de aparecer como marcadores crus;
- seção `Fontes consultadas` abaixo da resposta;
- cartões contendo:
  - identificador da citação, por exemplo `[1]`;
  - nome do documento;
  - página;
  - trecho da fonte quando disponível;
- a interface principal mostra apenas fontes cujo `citation_id` realmente aparece em `citation_ids`;
- fontes recuperadas mas não citadas permanecem fora da experiência principal.

Essa distinção evita confundir retrieval com atribuição: uma fonte pode ter sido recuperada para contexto e ainda assim não ter sido usada na resposta final.

A biblioteca escolhida é JS-only e não depende de WebView nem de módulo nativo específico, preservando Android, iOS e Web dentro do mesmo cliente Expo. No Jest, o pacote precisa ser explicitamente transpilado em `transformIgnorePatterns`.

Ainda não faz parte da 0.5.23:

- painel técnico com todas as fontes recuperadas;
- visualização de score de retrieval para a usuária final;
- deep-link para PDFs locais;
- histórico persistente;
- sessões multi-turn.


## Grounding e fontes recuperadas — 0.5.24

O primeiro refinamento da 0.5.24 usa o campo `grounded` já existente no contrato para tornar o estado da resposta mais claro.

### Resposta com grounding estrutural válido

A interface exibe:

    Citações verificadas
    As afirmações informativas estão acompanhadas de referências do corpus.

A seção `Fontes consultadas` continua mostrando somente fontes presentes em `citation_ids`.

Esse texto não deve ser interpretado como garantia clínica nem como prova de entailment semântico; ele representa o gate estrutural de citações implementado no backend.

### Grounding inválido com fontes recuperadas

Quando o backend recuperou trechos, mas a resposta final não passou na validação de citações:

    Citações não verificadas
    Não foi possível validar as citações desta resposta.
    Consulte as fontes recuperadas abaixo.

A interface então mostra:

    Fontes recuperadas para consulta

Esses cartões não exibem badge `[citation_id]`, porque não devem ser apresentados como citações efetivamente usadas na resposta.

### Nenhuma fonte relevante

Quando `grounded=false` e `sources=[]`, a interface mostra:

    Sem base documental suficiente

e não cria seção de fontes vazia.

Nenhuma mudança de backend ou de contrato foi necessária.
