# Auditoria estruturada segura 0.7.0-A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar auditoria operacional estruturada, minimizada e não bloqueante ao backend 0.6.0, com `request_id`, eventos de sessão/chat, normalização segura de falhas e nenhum conteúdo funcional ou documental nos eventos/logs de auditoria.

**Architecture:** Um middleware ASGI gera um UUID opaco por requisição, instala-o em `request.state` e devolve `X-Request-ID`, incluindo respostas de erro e exposição CORS para clientes web. Rotas produzem eventos tipados por meio de um `AuditSink` injetável; um fallback de middleware cobre erros de validação/dependência que ocorrem antes da função da rota, garantindo no máximo um evento de chat por requisição. O sink JSON usa somente uma allowlist fechada e falhas do sink são capturadas sem alterar resposta, lease, persistência ou chamadas ao LLM.

**Tech Stack:** Python 3.12, FastAPI/Starlette, dataclasses imutáveis, `logging`, JSON determinístico, pytest/pytest-asyncio, `caplog`, Ruff 0.16.8, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-09-22-auditoria-estruturada-0.7.0-a-design.md`

## Global Constraints

- O contrato funcional de `POST /v1/chat` permanece compatível com a 0.6.0; a única adição pública deste recorte é o header de resposta `X-Request-ID`.
- `request_id`, `event_id` e `session_id` são UUIDs opacos; o `request_id` é sempre gerado pelo backend e um header recebido do cliente é ignorado.
- `AuditEvent` não possui `payload`, `message`, `details` ou qualquer campo genérico.
- Eventos e logs de auditoria não podem conter pergunta, resposta, prompt, histórico, excerpt, source, filename, conteúdo documental, headers de autorização, API keys, tokens, URLs com credenciais, corpo HTTP bruto ou traceback com esses valores.
- `JsonLogAuditSink` escreve uma linha JSON parseável no logger `ragtest.audit`; falha de emissão é registrada somente como diagnóstico sanitizado no logger `ragtest.audit.internal`.
- `chat.completed` de uma sessão só é emitido depois da persistência bem-sucedida do turno; falha de persistência produz `chat.failed` e não cria turno parcial.
- Cada `POST /v1/chat` produz no máximo um evento de auditoria: exatamente um `chat.completed` ou `chat.failed` quando o request alcança a API, inclusive 422 e falha de dependência.
- A emissão de auditoria nunca chama o LLM, retrieval, embeddings, Qdrant ou fallback de provider.
- Não usar `ragtest-ingest --recreate`, `docker compose down -v`, reindexação, alteração de parâmetros de retrieval, alteração de embeddings, alteração do corpus ou mutação da collection `ragtest_documents`.
- Testes não usam provider externo nem conteúdo de `data/source/chatscm/*.docx`.
- O SQLite funcional da 0.6.0 continua podendo armazenar o histórico previsto; a proibição deste plano vale para eventos e logs, não para a remoção do contrato funcional de sessões.
- Autenticação/autorização, retenção final, criptografia, backups/WAL, TLS, rate limiting, headers de produção, exposição do Qdrant, auditoria de dependências e conformidade LGPD final ficam explicitamente em 0.7.0-B.

## Review Focus

- Erro de provider com corpo HTTP contendo sentinels sensíveis: somente status/classe estáveis podem chegar ao evento, resposta e logs; cobrir em Task 4.
- Falha antes da execução da rota, especialmente 422 e dependência que retorna 503: deve receber `request_id` e um único `chat.failed`; cobrir em Tasks 3 e 7.
- Sink que lança exceção depois de um turno de sessão: resposta e persistência devem permanecer intactas; cobrir em Task 7.
- Header `X-Request-ID` enviado pelo cliente: deve ser ignorado, e o UUID novo deve ser mantido em `request.state`, resposta e evento; cobrir em Task 3.
- Evento de sessão/chat construído a partir de `ChatResponse` ou `SessionResponse`: nenhum campo funcional deve ser serializado por acidente; cobrir em Tasks 1, 5 e 6.

## Ajustes obrigatórios na especificação antes do código

Os pontos abaixo são decisões de contrato propostas pela revisão. Devem ser confirmados pelo usuário antes da implementação funcional; o plano já assume estes valores para evitar ambiguidade:

1. `AuditEvent` será uma dataclass `frozen=True, slots=True`, sem campos extras, com `event_id`, `timestamp`, `request_id`, `event_type`, `outcome`, `operation` e `duration_ms` obrigatórios. `session_id`, `provider`, `model`, `status_code`, `error_code`, `error_type`, `grounded`, `source_count`, `citation_count`, `citation_retry_count`, `retrieval_query_count` e `turn_count` serão opcionais e omitidos do JSON quando `None`.
2. `timestamp` será timezone-aware UTC serializado em ISO-8601 com sufixo `Z`; `duration_ms` será inteiro não negativo calculado com `time.monotonic()` e arredondamento determinístico ao milissegundo.
3. `event_type` será limitado a `session.created`, `session.read`, `session.deleted`, `chat.completed` e `chat.failed`; `outcome` será `success` ou `failure`; `operation` será limitado a `session.create`, `session.read`, `session.delete` e `chat`.
4. A taxonomia mínima será: `404/session_not_found/session`, `409/session_busy|session_conflict/session`, `410/session_expired/session`, `422/validation_error/validation`, `502/provider_error|internal_error/provider|unhandled`, `503/provider_unavailable/provider`. O status HTTP público continuará seguro e compatível com a semântica 0.6.0; qualquer mudança adicional de status exigirá decisão separada.
5. Falhas de validação e dependência antes da função da rota serão cobertas pelo middleware de auditoria como `chat.failed`, sem copiar o `detail` do FastAPI ou da exceção.
6. `provider` será somente o rótulo configurado (`gemini`, `groq` ou `ollama`) e `model` somente o nome configurado; não serão derivados de URL, payload, headers ou resposta do provider.
7. `JsonLogAuditSink` usará `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` e emitirá exatamente uma string sem quebra de linha no logger `ragtest.audit`.
8. A sanitização dos erros/logs crus de Groq/Ollama é parte mínima da 0.7.0-A (decisão A deste pedido), porque o fluxo de `chat.failed` e o critério de ausência de conteúdo não podem coexistir com corpo HTTP bruto, `str(exc)` bruto ou traceback de provider. Governança ampla dos logs permanece em 0.7.0-B.

## Mapa de arquivos

Arquivos novos:

- `app/observability/__init__.py`: exporta os tipos públicos mínimos do pacote.
- `app/observability/audit.py`: `AuditEvent`, `AuditSink`, `JsonLogAuditSink` e `safe_emit`.
- `app/observability/errors.py`: normalização de exceções/status para classes estáveis e detalhes públicos seguros.
- `app/observability/middleware.py`: geração de `request_id`, header de resposta e fallback de `chat.failed` pré-rota.
- `tests/test_audit_contract.py`: contrato, imutabilidade e serialização.
- `tests/test_audit_sink.py`: sink JSON e falhas não bloqueantes.
- `tests/test_request_id.py`: middleware, erros e CORS.
- `tests/test_audit_sessions.py`: eventos das rotas de sessão.
- `tests/test_audit_chat.py`: eventos de sucesso, sessão/stateless e contagens.
- `tests/test_audit_errors.py`: taxonomia e falhas pré-rota.
- `tests/test_provider_log_privacy.py`: regressões de Groq/Ollama/decomposição sem conteúdo bruto.

Arquivos modificados:

- `app/main.py`: inicializa o sink, registra middleware e expõe `X-Request-ID` via CORS.
- `app/api/dependencies.py`: fornece o sink a partir de `app.state`.
- `app/api/routes/chat.py`: marca emissão, normaliza falhas e emite `chat.completed`/`chat.failed`.
- `app/api/routes/sessions.py`: emite eventos após criação, leitura e exclusão bem-sucedidas.
- `app/llm/groq_provider.py`: remove corpo HTTP bruto de exceções e logs de retry.
- `app/llm/ollama_provider.py`: remove corpo HTTP bruto de exceções e logs de retry.
- `app/rag/decomposition.py`: remove `exc_info=True` e registra somente diagnóstico sanitizado.
- `README.md`: documenta header, eventos, limites e distinção entre auditoria e histórico funcional.
- `docs/CONTEXTO_CONTINUIDADE.md`: registra implementação/verificação reais da 0.7.0-A somente após os gates.
- `docs/decisoes-tecnicas.md`: registra a decisão de auditoria minimizada e sanitização limitada de provider.
- `docs/dificuldades-tcc.md`: somente se surgir falha reproduzível nova; não criar registro preventivo.

## Task 0: Aprovar os ajustes de contrato e manter o recorte isolado

**Files:**
- Modify: `docs/superpowers/specs/2026-09-22-auditoria-estruturada-0.7.0-a-design.md` após aprovação do usuário.
- No production code, tests, corpus or Qdrant changes in this task.

**Interfaces:**
- Consumes: findings desta revisão e o contrato 0.6.0.
- Produces: especificação com taxonomia, fronteira de eventos, serialização, CORS e decisão A/B explícitas.

- [ ] **Step 1: Confirm the specification changes with the user**

  Confirm the eight adjustments listed above, especially the choice that provider error sanitization is the bounded 0.7.0-A work and that authentication/retention/LGPD remain 0.7.0-B.

- [ ] **Step 2: Verify no sidequest code is in the implementation branch**

  Run:

  ```powershell
  git status --short --branch
  git diff --name-only HEAD..sidequest/ragtest-demo
  git merge-base --is-ancestor sidequest/ragtest-demo HEAD
  ```

  Expected: current branch is `feature/audit-0.7.0`, the sidequest has exclusive files, and the sidequest ref is not an ancestor of the current branch.

- [ ] **Step 3: Stop if approval is not explicit**

  Do not create implementation files, provider patches, schema migrations, dependency changes or Qdrant commands until the user approves the adjusted contract.

## Task 1: Implement the closed immutable AuditEvent contract

**Files:**
- Create: `app/observability/__init__.py`
- Create: `app/observability/audit.py`
- Create: `tests/test_audit_contract.py`

**Interfaces:**
- Consumes: UUIDs, UTC datetimes and result metadata supplied by routes.
- Produces: `AuditEvent`, `AuditEventType`, `AuditOutcome`, `AuditOperation`, `AuditEvent.to_dict()` and `AuditEvent.to_json()`.

- [ ] **Step 1: Write the failing contract tests**

  Start with tests that import the not-yet-existing module:

  ```python
  import json
  from dataclasses import FrozenInstanceError
  from datetime import UTC, datetime
  from uuid import UUID

  import pytest

  from app.observability.audit import AuditEvent

  REQUEST_ID = UUID("00000000-0000-0000-0000-000000000001")

  def test_event_is_immutable_and_serializes_only_allowlisted_fields() -> None:
      event = AuditEvent(
          event_id=UUID("00000000-0000-0000-0000-000000000002"),
          timestamp=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
          request_id=REQUEST_ID,
          event_type="chat.completed",
          outcome="success",
          operation="chat",
          duration_ms=7,
          provider="groq",
          model="openai/gpt-oss-120b",
          grounded=True,
          source_count=2,
          citation_count=2,
          citation_retry_count=0,
          retrieval_query_count=1,
      )

      with pytest.raises(FrozenInstanceError):
          event.duration_ms = 8

      payload = json.loads(event.to_json())
      assert payload["timestamp"] == "2026-09-24T12:00:00Z"
      assert payload["request_id"] == str(REQUEST_ID)
      assert payload["duration_ms"] == 7
      assert "question" not in payload
      assert "answer" not in payload
      assert "prompt" not in payload
      assert "source" not in payload
      assert "excerpt" not in payload

  def test_event_omits_none_and_rejects_invalid_duration() -> None:
      event = AuditEvent(
          event_id=UUID("00000000-0000-0000-0000-000000000002"),
          timestamp=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
          request_id=REQUEST_ID,
          event_type="session.created",
          outcome="success",
          operation="session.create",
          duration_ms=0,
      )

      assert "session_id" not in event.to_dict()
      with pytest.raises(ValueError, match="duration_ms"):
          AuditEvent(
              event_id=event.event_id,
              timestamp=event.timestamp,
              request_id=event.request_id,
              event_type="session.created",
              outcome="success",
              operation="session.create",
              duration_ms=-1,
          )
  ```

- [ ] **Step 2: Run the focused test to verify RED**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_contract.py -v`

  Expected: FAIL during import because `app.observability.audit` does not exist.

- [ ] **Step 3: Implement the minimum contract**

  Use `dataclass(frozen=True, slots=True)`, `Literal`/enum validation, aware UTC normalization, UUID string conversion, omission of `None`, explicit allowlisted field construction, non-negative integer checks and deterministic JSON serialization. Do not add a catch-all dictionary or accept arbitrary keyword fields.

- [ ] **Step 4: Run the focused test to verify GREEN**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_contract.py -v`

  Expected: PASS, with no event field capable of carrying functional/document content.

- [ ] **Step 5: Commit the isolated contract**

  ```powershell
  git add app/observability/__init__.py app/observability/audit.py tests/test_audit_contract.py
  git commit -m "feat: define minimized audit event contract"
  ```

## Task 2: Implement the interchangeable sinks and non-blocking emission guard

**Files:**
- Modify: `app/observability/audit.py`
- Create: `tests/test_audit_sink.py`

**Interfaces:**
- Consumes: `AuditEvent`.
- Produces: `AuditSink.emit(event)`, `JsonLogAuditSink.emit(event)` and `safe_emit(sink, event)`.

- [ ] **Step 1: Write the failing sink tests**

  Test one parseable JSON line, the logger name, deterministic key ordering, and an exception containing a sensitive sentinel that must not be copied to the internal log:

  ```python
  import json
  import logging
  from unittest.mock import Mock

  from app.observability.audit import AuditEvent, JsonLogAuditSink, safe_emit

  def test_json_sink_emits_one_parseable_deterministic_line(caplog) -> None:
      event = make_completed_event()
      sink = JsonLogAuditSink()

      with caplog.at_level(logging.INFO, logger="ragtest.audit"):
          sink.emit(event)

      record = next(record for record in caplog.records if record.name == "ragtest.audit")
      assert json.loads(record.message)["event_type"] == "chat.completed"
      assert record.message == event.to_json()
      assert "question" not in record.message
      assert "excerpt" not in record.message

  def test_sink_failure_is_swallowed_and_does_not_log_exception_text(caplog) -> None:
      sink = Mock()
      sink.emit.side_effect = RuntimeError("PROMPT_SECRET EXCERPT_SECRET")
      event = make_completed_event()

      with caplog.at_level(logging.WARNING, logger="ragtest.audit.internal"):
          assert safe_emit(sink, event) is False

      assert "PROMPT_SECRET" not in caplog.text
      assert "EXCERPT_SECRET" not in caplog.text
      assert "RuntimeError" in caplog.text
  ```

- [ ] **Step 2: Run the focused test to verify RED**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_sink.py -v`

  Expected: FAIL because `JsonLogAuditSink` and `safe_emit` do not exist.

- [ ] **Step 3: Implement the minimum sink behavior**

  Send only `event.to_json()` to `logging.getLogger("ragtest.audit").info`. Catch `Exception` in `safe_emit`, return `False`, and log only a fixed message plus `type(exc).__name__` to `ragtest.audit.internal`; never interpolate `str(exc)`, `repr(event)` or serialized event data in the failure log.

- [ ] **Step 4: Run the focused test to verify GREEN**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_sink.py -v`

  Expected: PASS and exactly one audit record per explicit `emit` call.

- [ ] **Step 5: Commit the sink boundary**

  ```powershell
  git add app/observability/audit.py tests/test_audit_sink.py
  git commit -m "feat: add safe interchangeable audit sinks"
  ```

## Task 3: Add request ID middleware and CORS exposure

**Files:**
- Create: `app/observability/middleware.py`
- Modify: `app/main.py`
- Create: `tests/test_request_id.py`
- Modify: `tests/test_cors.py`

**Interfaces:**
- Consumes: an ASGI `Request` and the configured FastAPI application.
- Produces: `request.state.request_id`, response `X-Request-ID`, `Access-Control-Expose-Headers: X-Request-ID`, and request timing state for the audit fallback.

- [ ] **Step 1: Write failing middleware tests**

  Cover a normal response, a client-supplied spoofed header, a 422 response and a browser preflight/expose check:

  ```python
  from uuid import UUID

  from fastapi.testclient import TestClient

  def test_backend_generates_request_id_and_ignores_client_header() -> None:
      with TestClient(app) as client:
          response = client.get(
              "/health",
              headers={"X-Request-ID": "00000000-0000-0000-0000-000000000099"},
          )

      request_id = UUID(response.headers["X-Request-ID"])
      assert request_id != UUID("00000000-0000-0000-0000-000000000099")

  def test_request_id_exists_on_validation_error() -> None:
      with TestClient(app) as client:
          response = client.post("/v1/chat", json={"message": "x"})

      UUID(response.headers["X-Request-ID"])
      assert response.status_code == 422

  def test_cors_exposes_request_id() -> None:
      with TestClient(app) as client:
          response = client.options(
              "/v1/chat",
              headers={
                  "Origin": "http://localhost:8081",
                  "Access-Control-Request-Method": "POST",
              },
          )

      assert response.headers["access-control-expose-headers"] == "X-Request-ID"
  ```

- [ ] **Step 2: Run the focused test to verify RED**

  Run: `.\.venv\Scripts\pytest.exe tests/test_request_id.py tests/test_cors.py -v`

  Expected: FAIL because no middleware/header/expose configuration exists.

- [ ] **Step 3: Implement middleware and registration**

  Generate `uuid4()` per request, ignore the incoming header, set `request.state.request_id`, measure elapsed time with `time.monotonic()`, set `X-Request-ID` on every response returned by the app, and add `expose_headers=["X-Request-ID"]` to CORS. Preserve the existing allowed origins and methods.

- [ ] **Step 4: Run the focused test to verify GREEN**

  Run: `.\.venv\Scripts\pytest.exe tests/test_request_id.py tests/test_cors.py -v`

  Expected: PASS for success, validation error and CORS exposure, with no client-controlled correlation ID accepted.

- [ ] **Step 5: Commit request correlation**

  ```powershell
  git add app/observability/middleware.py app/main.py tests/test_request_id.py tests/test_cors.py
  git commit -m "feat: correlate requests with backend generated ids"
  ```

## Task 4: Normalize errors and remove raw Groq/Ollama provider logging

**Files:**
- Create: `app/observability/errors.py`
- Modify: `app/api/routes/chat.py`
- Modify: `app/llm/groq_provider.py`
- Modify: `app/llm/ollama_provider.py`
- Modify: `app/rag/decomposition.py`
- Create: `tests/test_audit_errors.py`
- Create: `tests/test_provider_log_privacy.py`

**Interfaces:**
- Consumes: current session exceptions, `LLMServiceUnavailableError`, provider HTTP errors and unexpected exceptions.
- Produces: `NormalizedError(status_code, error_code, error_type, public_detail)` and sanitized provider logger messages.

- [ ] **Step 1: Write failing normalization and privacy tests**

  Test the stable taxonomy and inject the same sentinel into fake provider error bodies, exception messages and decomposition failures:

  ```python
  def test_provider_error_normalizes_without_raw_detail() -> None:
      normalized = normalize_exception(
          RuntimeError("PROMPT_SECRET EXCERPT_SECRET https://private.invalid")
      )

      assert normalized.status_code == 502
      assert normalized.error_code == "provider_error"
      assert normalized.error_type == "provider"
      assert normalized.public_detail == "LLM provider request failed."
      assert "PROMPT_SECRET" not in normalized.public_detail

  def test_unexpected_error_uses_stable_internal_class() -> None:
      normalized = normalize_exception(ValueError("ANSWER_SECRET"))
      assert normalized.error_code == "internal_error"
      assert normalized.error_type == "unhandled"
      assert "ANSWER_SECRET" not in normalized.public_detail

  def test_groq_http_body_is_not_logged(caplog, monkeypatch) -> None:
      error = HTTPError(
          url="https://provider.invalid/chat",
          code=503,
          msg="Service unavailable",
          hdrs={},
          fp=BytesIO(b"PROMPT_SECRET EXCERPT_SECRET ANSWER_SECRET"),
      )
      monkeypatch.setattr("app.llm.groq_provider.urlopen", raise_error(error))

      with caplog.at_level(logging.WARNING):
          with pytest.raises(LLMServiceUnavailableError):
              asyncio.run(_provider(retries=0).generate(system_prompt="p", user_prompt="q"))

      assert "PROMPT_SECRET" not in caplog.text
      assert "EXCERPT_SECRET" not in caplog.text
      assert "ANSWER_SECRET" not in caplog.text
  ```

  The Ollama test is identical against its endpoint and the decomposition test asserts that `exc_info` is absent and the sentinel is not in `caplog.text`.

- [ ] **Step 2: Run the focused tests to verify RED**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_errors.py tests/test_provider_log_privacy.py -v`

  Expected: FAIL because raw provider details are currently part of `_GroqRequestError`/`_OllamaRequestError`, retry logging interpolates the exception, and route normalization does not exist.

- [ ] **Step 3: Implement stable normalization and bounded sanitization**

  Map recognized session/provider/validation exceptions to the agreed table. Replace raw HTTP body concatenation with status-only provider errors, keep retry eligibility from the numeric status, log only provider/model/status/retry index/delay, remove `exc_info=True` from decomposition fallback, and return fixed public details. Do not change retrieval, provider selection, retry counts or LLM payloads.

- [ ] **Step 4: Run focused and existing provider tests**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_errors.py tests/test_provider_log_privacy.py tests/test_groq_provider.py tests/test_ollama_provider.py -v`

  Expected: PASS with no sensitive sentinel in response or captured logs; existing provider behavior remains green without network access.

- [ ] **Step 5: Commit error hardening**

  ```powershell
  git add app/observability/errors.py app/api/routes/chat.py app/llm/groq_provider.py app/llm/ollama_provider.py app/rag/decomposition.py tests/test_audit_errors.py tests/test_provider_log_privacy.py
  git commit -m "fix: sanitize provider errors for audit-safe failures"
  ```

## Task 5: Wire the sink and emit successful session lifecycle events

**Files:**
- Modify: `app/main.py`
- Modify: `app/api/dependencies.py`
- Modify: `app/api/routes/sessions.py`
- Create: `tests/test_audit_sessions.py`

**Interfaces:**
- Consumes: `AuditSink`, request state, `ConversationService` snapshots and monotonic timing.
- Produces: `session.created`, `session.read` and `session.deleted` events with no session content.

- [ ] **Step 1: Write failing session-event tests**

  Use an in-memory test sink through a dependency override and assert only UUID/count metadata:

  ```python
  def test_create_session_emits_minimized_event(client, audit_sink, service) -> None:
      service.create_session.return_value = empty_snapshot_with_three_turns()
      override_audit_sink(audit_sink)

      response = client.post("/v1/sessions")

      assert response.status_code == 201
      event = audit_sink.events[-1]
      assert event.event_type == "session.created"
      assert event.session_id == SESSION_ID
      assert event.outcome == "success"
      assert event.turn_count is None
      serialized = event.to_json()
      assert "PERGUNTA_SECRET" not in serialized
      assert "RESPOSTA_SECRET" not in serialized
      assert "EXCERPT_SECRET" not in serialized

  def test_read_session_contains_only_turn_count(client, audit_sink, service) -> None:
      service.get_session.return_value = empty_snapshot_with_three_turns()
      override_audit_sink(audit_sink)

      response = client.get(f"/v1/sessions/{SESSION_ID}")

      assert response.status_code == 200
      event = audit_sink.events[-1]
      assert event.event_type == "session.read"
      assert event.turn_count == 3
      assert "question" not in event.to_json()
      assert "sources" not in event.to_json()
  ```

- [ ] **Step 2: Run the focused test to verify RED**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_sessions.py -v`

  Expected: FAIL because the sink dependency and lifecycle event calls do not exist.

- [ ] **Step 3: Initialize and inject one sink**

  Create `JsonLogAuditSink` once in `lifespan`, store it in `app.state.audit_sink`, expose `get_audit_sink(request)`, and use the dependency in session routes. Build each event from UUID/count metadata rather than response models or turns.

- [ ] **Step 4: Emit only after successful lifecycle operations**

  Emit `session.created` after `create_session` returns, `session.read` after `get_session` returns, and `session.deleted` after `delete_session` completes. Failed 404/410 operations do not emit a successful lifecycle event; their response still receives `X-Request-ID`.

- [ ] **Step 5: Run the focused test to verify GREEN**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_sessions.py -v`

  Expected: PASS with no functional session contract change and no content fields in events.

- [ ] **Step 6: Commit session lifecycle auditing**

  ```powershell
  git add app/main.py app/api/dependencies.py app/api/routes/sessions.py tests/test_audit_sessions.py
  git commit -m "feat: audit successful session lifecycle events"
  ```

## Task 6: Emit chat.completed for stateless and persisted chats

**Files:**
- Modify: `app/api/routes/chat.py`
- Create: `tests/test_audit_chat.py`

**Interfaces:**
- Consumes: `ChatResult`, `CompletedConversationTurn`, `request.state.request_id`, provider label and `AuditSink`.
- Produces: one `chat.completed` event with provider/model, duration, grounding and count metadata.

- [ ] **Step 1: Write failing success-event tests**

  Cover both modes and assert that the event is independent of answer/source content:

  ```python
  def test_stateless_chat_emits_completed_event(client, audit_sink, fake_dependencies) -> None:
      response = client.post("/v1/chat", json={"message": "PERGUNTA_SECRET"})

      assert response.status_code == 200
      event = only_event(audit_sink, "chat.completed")
      assert event.session_id is None
      assert event.grounded is True
      assert event.source_count == 1
      assert event.citation_count == 1
      assert event.citation_retry_count == 0
      assert event.retrieval_query_count == 1
      assert "PERGUNTA_SECRET" not in event.to_json()
      assert "RESPOSTA_SECRET" not in event.to_json()
      assert "EXCERPT_SECRET" not in event.to_json()

  def test_session_chat_emits_after_turn_persistence(client, audit_sink, service) -> None:
      response = client.post(
          "/v1/chat",
          json={"message": "PERGUNTA_SECRET", "session_id": str(SESSION_ID)},
      )

      assert response.status_code == 200
      assert service.completed_before_audit is True
      event = only_event(audit_sink, "chat.completed")
      assert event.session_id == SESSION_ID
  ```

- [ ] **Step 2: Run the focused test to verify RED**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_chat.py -v`

  Expected: FAIL because chat routes do not receive a sink or emit events.

- [ ] **Step 3: Add safe success emission**

  Add `Request` and `AuditSink` dependencies to the route, capture `time.monotonic()` at route entry, build only allowlisted metrics from `ChatResult`, and mark `request.state.audit_event_emitted` before calling `safe_emit`. For session mode, perform this only after `ConversationService.run_turn` returns.

- [ ] **Step 4: Verify no audit-induced provider work**

  Assert the fake LLM call count and retrieval calls are identical with and without the sink; event construction must not access prompts, answer text, hit content, source paths or the session response.

- [ ] **Step 5: Run focused tests to verify GREEN**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_chat.py tests/test_chat.py tests/test_chat_sessions.py -v`

  Expected: PASS, including the existing stateless/session regressions.

- [ ] **Step 6: Commit successful chat auditing**

  ```powershell
  git add app/api/routes/chat.py tests/test_audit_chat.py
  git commit -m "feat: audit completed stateless and session chats"
  ```

## Task 7: Cover chat.failed, pre-route errors and sink non-blocking behavior

**Files:**
- Modify: `app/observability/middleware.py`
- Modify: `app/api/routes/chat.py`
- Create: `tests/test_audit_errors.py` if not completed in Task 4; otherwise extend it.
- Create: `tests/test_audit_sink.py` if not completed in Task 2; otherwise extend it.

**Interfaces:**
- Consumes: normalized errors, response status, request state and `safe_emit`.
- Produces: one `chat.failed` for route failures, validation failures, dependency failures and unexpected exceptions.

- [ ] **Step 1: Write failing failure-path tests**

  Cover recognized session/provider failures, 422 before route entry, dependency failure before route entry and one sink failure:

  ```python
  @pytest.mark.parametrize(
      ("status", "error_code", "error_type"),
      [
          (404, "session_not_found", "session"),
          (409, "session_busy", "session"),
          (410, "session_expired", "session"),
          (503, "provider_unavailable", "provider"),
          (502, "provider_error", "provider"),
      ],
  )
  def test_chat_failure_emits_stable_classification(
      client, audit_sink, configure_failure, status, error_code, error_type
  ) -> None:
      configure_failure(status)

      response = client.post("/v1/chat", json={"message": "PERGUNTA_SECRET"})

      assert response.status_code == status
      event = only_event(audit_sink, "chat.failed")
      assert event.status_code == status
      assert event.error_code == error_code
      assert event.error_type == error_type
      assert "PERGUNTA_SECRET" not in event.to_json()
      assert "DETAIL_SECRET" not in event.to_json()

  def test_validation_error_is_a_single_pre_route_chat_failed(client, audit_sink) -> None:
      response = client.post("/v1/chat", json={"message": "x"})

      assert response.status_code == 422
      events = [event for event in audit_sink.events if event.event_type == "chat.failed"]
      assert len(events) == 1
      assert events[0].error_code == "validation_error"

  def test_sink_failure_does_not_change_session_chat_or_persistence(
      client, failing_audit_sink, service
  ) -> None:
      response = client.post(
          "/v1/chat",
          json={"message": "PERGUNTA_SECRET", "session_id": str(SESSION_ID)},
      )

      assert response.status_code == 200
      assert service.completed_before_audit is True
      assert service.release_called is False
  ```

- [ ] **Step 2: Run the focused tests to verify RED**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_errors.py tests/test_audit_sink.py -v`

  Expected: FAIL because there is no pre-route fallback, no failure emission, and the test fixtures cannot observe normalized event state.

- [ ] **Step 3: Add one-emission state and middleware fallback**

  Route-level success/failure paths set `request.state.audit_event_emitted=True` before `safe_emit`. The middleware checks `/v1/chat` responses after `call_next`; if no event was marked and the response status is 4xx/5xx, it emits one failure using only status-to-class mapping. It must not copy response bodies or validation details.

- [ ] **Step 4: Preserve leases and responses when the sink fails**

  Wrap every emission with `safe_emit`; never place emission inside the session transaction, never call `release` because of a sink exception, and never retry the provider. Assert that the same HTTP response and persisted turn are returned.

- [ ] **Step 5: Run focused and session regression tests to verify GREEN**

  Run: `.\.venv\Scripts\pytest.exe tests/test_audit_errors.py tests/test_audit_sink.py tests/test_chat_sessions.py tests/test_sessions_api.py -v`

  Expected: PASS with one event per chat request, stable errors and unchanged 0.6.0 session semantics.

- [ ] **Step 6: Commit failure auditing and non-blocking behavior**

  ```powershell
  git add app/observability/middleware.py app/api/routes/chat.py tests/test_audit_errors.py tests/test_audit_sink.py
  git commit -m "feat: audit normalized chat failures without blocking requests"
  ```

## Task 8: Document verified behavior and run the complete regression gate

**Files:**
- Modify: `README.md`
- Modify: `docs/CONTEXTO_CONTINUIDADE.md`
- Modify: `docs/decisoes-tecnicas.md`
- Modify: `docs/dificuldades-tcc.md` only when a new reproducible failure exists.

**Interfaces:**
- Consumes: verified implementation and command output from Tasks 1–7.
- Produces: public usage documentation, decision traceability and an accurate continuation checkpoint.

- [ ] **Step 1: Write documentation assertions as a review checklist**

  Confirm the documentation states: events are metadata-only; history remains functional SQLite data; `X-Request-ID` is backend-generated; `grounded=true` remains structural citation coverage; provider raw errors are not logged; 0.7.0-B is not implemented; no claim of LGPD compliance is made.

- [ ] **Step 2: Update documentation from evidence only**

  Add event examples without question/answer/source values, document the stable error classes and CORS header, record the branch/commit/PR state, and record that corpus/embeddings/Qdrant were not changed. Do not copy secrets, CHATSCM content or raw logs into documentation.

- [ ] **Step 3: Run the complete backend and frontend gates**

  Run:

  ```powershell
  .\.venv\Scripts\pytest.exe
  .\.venv\Scripts\ruff.exe check .
  docker compose config --quiet
  Set-Location frontend
  npm test -- --runInBand
  npm run typecheck
  Set-Location ..
  git diff --check
  git status --short --branch
  ```

  Expected: backend 149 existing tests plus new audit tests pass; Ruff passes; Docker config passes; frontend remains 13/13 and typecheck passes; no corpus/Qdrant files appear in the diff.

- [ ] **Step 4: Perform the manual local acceptance without external providers**

  Use TestClient/fake dependencies to verify one `X-Request-ID`, one event, no forbidden fields, sink failure tolerance and session/stateless compatibility. Do not call Groq, Gemini or Ollama and do not run ingestion.

- [ ] **Step 5: Update the continuation checkpoint only after verification**

  Mark each item as `implementado`, `aguardando validação` or `verificado` from actual output. Do not claim production LGPD compliance or provider data-egress enforcement.

- [ ] **Step 6: Commit the verified documentation and regression result**

  ```powershell
  git add README.md docs/CONTEXTO_CONTINUIDADE.md docs/decisoes-tecnicas.md docs/dificuldades-tcc.md
  git commit -m "docs: record verified structured audit contract"
  ```

## Final acceptance criteria

The implementation is accepted only when all conditions below are evidenced by tests or a documented local check:

1. `AuditEvent` is immutable, typed, closed and serializes deterministically with UTC timestamp, UUIDs and non-negative duration.
2. JSON events contain only the allowlisted fields and never contain question, answer, prompt, history, excerpt, source, filename, provider body, authorization, API key, token or traceback content.
3. `JsonLogAuditSink` emits one parseable line to `ragtest.audit`; sink failure is swallowed and its internal log contains no event or exception text.
4. Every response, including 4xx/5xx, has a backend-generated UUID in `X-Request-ID`; a client-supplied ID is ignored; Expo Web can read the response header through CORS exposure.
5. Successful session create/read/delete operations emit the corresponding event only after success; `session.read` carries only `turn_count` and no turn content.
6. Stateless and session chat success emit `chat.completed`; the session variant emits only after turn persistence.
7. Provider/session/validation/unexpected failures emit one `chat.failed` with stable status/code/type and no raw `detail`.
8. 422 validation and dependency failures occurring before route execution still produce one `chat.failed` through the middleware fallback.
9. Groq/Ollama HTTP bodies, raw exception strings and decomposition tracebacks are absent from captured logs and public error details; only bounded sanitized diagnostics remain.
10. Sink failure does not change HTTP response, session lease, persisted turn, provider call count, retry count or fallback behavior.
11. Existing backend/frontend tests, new tests, Ruff and `docker compose config --quiet` pass without provider calls, ingestion, reindexing or Qdrant mutation.
12. Documentation distinguishes implemented/verified audit behavior from the explicitly deferred 0.7.0-B security/privacy governance and makes no LGPD compliance claim.

## Deferred 0.7.0-B scope

The following are findings and future work, not silent additions to this plan: authentication and authorization for bearer session UUIDs; provider source-egress policy that technically blocks unreviewed CHATSCM documents; retention/deletion guarantees including SQLite WAL/backups; encryption and access control; TLS, rate limiting, security headers and Qdrant exposure; dependency lock/audit governance; CLI/stdout redaction beyond the audit sink; durable audit storage, querying, dashboards, export and final LGPD policy.

## Authorization and stop conditions

Pause and ask the user before:

- changing the public JSON contract or changing existing HTTP status semantics beyond the approved `X-Request-ID` header;
- adding authentication, authorization, source-egress enforcement or retention/crypto behavior;
- executing any provider call with new or unreviewed document content;
- reading, printing, staging or sending `.env` values/API keys;
- modifying corpus files, embeddings, retrieval parameters, Qdrant collection/schema/points or ingestion commands;
- merging, cherry-picking or incorporating `sidequest/ragtest-demo`.

## Plan self-review

- Spec coverage: objective, scope exclusions, minimization, UUIDs, sink abstraction, event set, session ordering, error normalization, monotonic duration, non-blocking failures, tests, documentation and no-provider/no-reindex gates are mapped to Tasks 1–8.
- Placeholder scan: all implementation steps name files, interfaces, commands and expected outcomes; no `TBD`, `TODO` or unspecified edge-case instruction is required.
- Type consistency: later tasks consume `AuditEvent`, `AuditSink`, `safe_emit`, `NormalizedError` and middleware state defined in earlier tasks.
- Review focus: provider-error sentinels (Task 4), pre-route errors (Tasks 3 and 7), sink failure (Task 7), spoofed request ID (Task 3), and functional-content isolation (Tasks 1, 5 and 6) each have explicit tests.

