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
