# Guia de integração — módulo RAG no app Se Cuida Mulher

O backend é independente do cliente. O app integrador (React Native, Flutter ou web) conversa
com ele por REST/JSON. Documentação interativa: `http://<host>:8000/docs` (OpenAPI).

## Endpoints

| Método | Rota | Uso |
|---|---|---|
| GET | `/health` | liveness (versão da API) |
| GET | `/ready` | readiness (Qdrant acessível) |
| POST | `/v1/sessions` | cria sessão de conversa (retorna `session_id`, expira em 7 dias) |
| GET | `/v1/sessions/{id}` | histórico da sessão |
| DELETE | `/v1/sessions/{id}` | apaga a sessão |
| POST | `/v1/chat` | pergunta → resposta com fontes, segurança e ações |
| POST | `/v1/search` | busca vetorial pura (diagnóstico) |

Toda resposta traz o header `X-Request-ID` (use em relatos de erro).

## `POST /v1/chat`

Requisição mínima:

```json
{ "message": "como agendo a mamografia?", "session_id": "UUID-opcional" }
```

Resposta (campos principais):

```json
{
  "answer": "Procure a UBS ... [1].",
  "grounded": true,
  "citation_ids": [1],
  "sources": [{ "citation_id": 1, "source": "servicos/catalogo_servicos.json", "excerpt": "..." }],
  "safety": { "triaged": false, "rule_id": null, "out_of_scope": false },
  "actions": [
    { "type": "open_link", "label": "Ver unidades de saúde", "url": "seucuida://unidades",
      "service_id": "mamografia", "suggested_in_days": null },
    { "type": "schedule_reminder", "label": "Mamografia de rastreamento: a cada 2 anos",
      "url": null, "service_id": "mamografia", "suggested_in_days": 730 }
  ]
}
```

### Como o app deve tratar cada campo

| Campo | Comportamento esperado no app |
|---|---|
| `answer` | Renderizar como Markdown; `[n]` referencia `sources[n-1]`. |
| `grounded=false` | Mostrar aviso "resposta sem fonte verificável"; não esconder as fontes recuperadas. |
| `safety.triaged=true` | Destacar como **alerta de urgência** (cor forte, botão de ligar). A resposta é fixa e não veio do LLM. |
| `safety.out_of_scope=true` | Mostrar a mensagem e sugerir perguntas do domínio. |
| `actions[].type=open_link` | Abrir `url`. `seucuida://unidades` deve ser mapeado para a tela "Unidades de Saúde" do app. |
| `actions[].type=schedule_reminder` | Oferecer "Lembrar"; criar notificação local em `hoje + suggested_in_days`. |
| `actions[].type=call_emergency` | Abrir o discador (`tel:192`). |

As ações só aparecem quando o serviço do catálogo foi **citado** numa resposta verificada, ou na
triagem de urgência. O LLM nunca gera links ou datas.

### Erros

| HTTP | Significado |
|---|---|
| 404 / 410 | sessão inexistente / expirada → criar nova sessão |
| 409 | sessão ocupada com outra resposta → aguardar e reenviar |
| 422 | requisição inválida |
| 503 | provider de IA indisponível → oferecer "tentar novamente" |
| 502 | falha do provider ou interna |

## Catálogo de serviços

`data/source/servicos/catalogo_servicos.json` define serviços, textos de agendamento, links e
lembretes. Para o município real: editar o JSON (validado por `app/catalog/services.py`), rodar
`ragtest-plan-ingestion-sync` e `ragtest-sync-ingestion --apply`. Não é preciso mudar código.

## Configuração relevante (`.env`)

| Variável | Efeito |
|---|---|
| `LLM_PROVIDER` | `gemini`, `groq` ou `ollama` (troca sem mudar o contrato) |
| `RETRIEVAL_MIN_SCORE` | limiar de fora de escopo (calibrar com `ragtest-calibrate-scope`) |
| `CORS_ALLOWED_ORIGINS` | origens web permitidas |

## Limitações atuais

- Sem autenticação: não usar dados reais de usuárias.
- Lembretes do cliente demonstrativo ficam em memória; notificações nativas são responsabilidade do app integrador.
- `grounded=true` indica cobertura de citações, não validação clínica.
