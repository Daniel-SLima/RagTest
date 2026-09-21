# Front-end de demonstração do RagTest

## Objetivo

Criar uma aplicação web independente para apresentar o chatbot do TCC funcionando antes de integrá-lo ao aplicativo Se Cuida Mulher.

## Stack

- Next.js 16.3
- React 19.2
- TypeScript
- Tailwind CSS 4
- shadcn/ui com Base UI para os componentes visuais
- Vitest + Testing Library para testes de unidade/componente
- Playwright para testes E2E quando a interface estiver funcional
- FastAPI/Qdrant continuam como backend e camada RAG

## Arquitetura proposta

O navegador não chamará o FastAPI diretamente na primeira versão. O front terá uma rota server-side `/api/chat` que encaminha a requisição para o backend definido por `RAG_API_BASE_URL`.

Isso permite:

- evitar CORS na demonstração inicial;
- não expor detalhes internos do backend ao navegador;
- trocar a URL do backend por ambiente;
- manter o contrato visual desacoplado do futuro Se Cuida Mulher.

## Primeira versão da interface

A demonstração deverá ter:

- cabeçalho do projeto;
- área principal de conversa;
- mensagem inicial explicando o propósito do chatbot;
- campo de texto e botão de envio;
- estado de carregamento;
- resposta renderizada de forma legível;
- fontes citadas e páginas consultadas;
- indicador de resposta grounded;
- mensagem clara quando o backend usar fallback seguro;
- painel técnico opcional para apresentação, mostrando modelo, citations, retrieval e rate limits quando disponíveis.

O painel técnico não será o foco para o usuário final; ele existe para facilitar a apresentação e defesa do TCC.

## Fora do escopo inicial

- autenticação de usuários;
- histórico persistente;
- integração com banco de dados;
- integração visual com o Se Cuida Mulher;
- streaming de tokens;
- fallback automático entre providers;
- alteração de corpus, embeddings ou Qdrant.
