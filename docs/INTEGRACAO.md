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
| GET | `/v1/suggestions` | perguntas sugeridas para a tela inicial (vêm do catálogo) |

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
  "sources": [{ "citation_id": 1, "source": "servicos/catalogo_servicos.json",
                "title": "Catálogo de serviços do Se Cuida Mulher", "location_label": null,
                "excerpt": "..." }],
  "display": { "status": "verified", "tone": "success",
               "title": "Citações verificadas",
               "message": "As afirmações informativas estão acompanhadas de referências do corpus." },
  "safety": { "triaged": false, "rule_id": null, "out_of_scope": false },
  "actions": [
    { "type": "open_link", "label": "Ver unidades de saúde", "url": "seucuida://unidades",
      "service_id": "mamografia", "suggested_in_days": null, "due_date": null,
      "requires_host_app": true,
      "note": "Este atalho abre a tela correspondente no app Se Cuida Mulher." },
    { "type": "schedule_reminder", "label": "Mamografia de rastreamento: a cada 2 anos",
      "url": null, "service_id": "mamografia", "suggested_in_days": 730,
      "due_date": "2028-09-27", "requires_host_app": false, "note": null }
  ]
}
```

### Como o app deve tratar cada campo

**Princípio:** o app não calcula nem decide nada; só renderiza. Textos, cores (`tone`), datas e
links já vêm prontos.

| Campo | Comportamento esperado no app |
|---|---|
| `answer` | Renderizar como Markdown; `[n]` referencia `sources[n-1]`. |
| `display` | Cartão de status: `title` + `message`, cor por `tone` (`danger`, `warning`, `success`, `neutral`). `status=emergency` deve ter destaque máximo. |
| `sources[].title` / `location_label` | Rótulos prontos das fontes (`location_label` pode ser nulo). |
| `safety` | Metadados para lógica/telemetria do app (`triaged`, `rule_id`, `out_of_scope`); a exibição usa `display`. |
| `actions[].type=open_link` | Abrir `url`. Se `requires_host_app=true`, mapear `seucuida://unidades` para a tela "Unidades de Saúde" do app (clientes externos mostram `note`). |
| `actions[].type=schedule_reminder` | Botão "Lembrar: `label`"; criar notificação local em `due_date` (ISO, fuso `APP_TIMEZONE`). |
| `actions[].type=call_emergency` | Abrir o discador (`tel:192`). |

`GET /v1/suggestions` → `{"suggestions": [{"text": "...", "topic": "rastreamento"}]}`; editável em
`sugestoes` no catálogo.

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
| `APP_TIMEZONE` | fuso usado para calcular `due_date` (padrão `America/Sao_Paulo`) |

## Limitações atuais

- Sem autenticação: não usar dados reais de usuárias.
- Lembretes do cliente demonstrativo ficam em memória; notificações nativas são responsabilidade do app integrador.
- `grounded=true` indica cobertura de citações, não validação clínica.
