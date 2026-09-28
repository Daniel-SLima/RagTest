# Deploy de homologação

Objetivo: deixar a API acessível por HTTPS para o orientador e para o futuro app, com chave de API.
Arquivos: `docker-compose.yml` (base) + `docker-compose.prod.yml` (sobreposição) + `deploy/Caddyfile`.

## O que a configuração de produção muda

| Item | Desenvolvimento | Produção |
|---|---|---|
| Porta do Qdrant | 6333 exposta | fechada (só a rede interna do Docker) |
| Porta da API | 8000 exposta | fechada; acesso só pelo Caddy |
| HTTPS | não | Caddy com certificado automático (Let's Encrypt) |
| `API_KEYS` | opcional | obrigatório (a API não sobe sem ele) |
| `ENVIRONMENT` | development | production |

## Requisitos

- Servidor Linux com Docker (ex.: VPS com 2 vCPU e 4 GB de RAM; o modelo de embeddings e o OCR
  usam memória).
- Um domínio ou subdomínio apontando (registro A) para o IP do servidor.
- Portas 80 e 443 liberadas no firewall.

## Passo a passo

```bash
git clone https://github.com/Daniel-SLima/RagTest.git && cd RagTest
cp .env.example .env
```

No `.env`, preencha:

```
LLM_PROVIDER=groq
GROQ_API_KEY=<sua chave>
API_KEYS=seucuida:<gere-uma-chave-longa>,orientador:<outra-chave>
RAGTEST_DOMAIN=api.seudominio.com
RETRIEVAL_MODE=hybrid
```

Para gerar chaves: `openssl rand -hex 24`.

Suba e indexe:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose exec api ragtest-plan-ingestion-sync
docker compose exec api ragtest-sync-ingestion --apply
```

Teste de fora do servidor:

```bash
curl https://api.seudominio.com/ready
curl -X POST https://api.seudominio.com/v1/chat \
  -H "Content-Type: application/json" -H "X-API-Key: <chave>" \
  -d '{"message":"Quando devo fazer o preventivo?"}'
```

## Operação

| Tarefa | Comando |
|---|---|
| Ver logs (inclui auditoria JSON) | `docker compose logs -f api` |
| Atualizar para nova versão | `git pull && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build` |
| Incluir documento novo em `data/source` | `ragtest-plan-ingestion-sync` e `ragtest-sync-ingestion --apply` |
| Trocar/revogar uma chave | editar `API_KEYS` no `.env` e subir de novo |

Nunca rode `docker compose down -v` (apaga Qdrant, sessões e cache de modelos).

## Limitações

- Limite de requisições em memória (vale por contêiner).
- Sessões em SQLite num volume local; sem backup automático.
- Ambiente de homologação: sem dados reais de usuárias.
