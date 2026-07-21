# CTO Office / Yarvis

## YARVIS

Operational Memory for Real Operations

**Yarvis remembers what humans should not have to.**

An Operational Evidence Consolidation and Operational Memory System designed to organize, connect, and preserve operational evidence, transforming operational chaos into actionable, explainable, and verifiable operational knowledge.

Current implementation phase: **E-001 Engineering Foundation — F-001 Repository Normalization**. Architecture is in [docs/architecture](docs/architecture); engineering guidance is in [docs/engineering](docs/engineering).

Backend requirement: **Python 3.12**. Canonical local setup and run command: `docker compose up -d --build`. For an editable backend environment, run from `apps/api`: `python -m pip install -r requirements-dev.txt` followed by `python -m pip install -e .`. Canonical backend test command: `docker compose exec api sh -lc "pip install -q -r requirements-dev.txt && pytest -ra"`.

From `apps/api`, the baseline quality commands are `ruff check`, `ruff format --check`, and `pyright`. Their initial scope is the new architecture-conformance code; legacy remediation is deferred to a later approved conformance work package.

**Elevator pitch:** Yarvis reduces operational entropy by transforming distributed evidence into trusted operational memory.

## Visión general de Yarvis

Yarvis es la capa operativa de CTO Office para convertir el trabajo del fundador en un sistema de ejecución auditable: capturar intakes, organizar casos, revisar documentos, evaluar cumplimiento, generar alertas y coordinar conversaciones con contexto verificable. El producto combina una API FastAPI, PostgreSQL, migraciones Alembic y un frontend React/Vite para ofrecer una experiencia operativa mínima pero reproducible.

## Estructura del repositorio

- docs/: visión, negocio, arquitectura, producto, decisiones, engineering y estándares.
- apps/api/: API FastAPI, modelos SQLAlchemy, rutas, migraciones Alembic y pruebas backend.
- apps/web/: frontend React + Vite + React Router + TanStack Query.
- docker-compose.yml: servicios api, postgres y web.
- README.md: guía de ejecución, arquitectura y operaciones.

## Principios arquitectónicos

- Modelar primero el dominio y luego la implementación.
- Preferir un monolito modular sobre una arquitectura distribuida prematura.
- Mantener PostgreSQL como fuente de verdad para casos, evidencia, alertas y eventos.
- Requerir confirmación humana para acciones sensibles y para contextualizar intakes.
- Mantener el almacenamiento documental fuera del alcance del bloque actual; los adjuntos se registran como metadatos, no como binarios.

## Resumen de los Bloques 1–6

- Bloque 1: base técnica inicial, API FastAPI, health check, PostgreSQL y Docker Compose.
- Bloque 2: intake manual, evidencia, eventos de dominio y bitácora operativa.
- Bloque 3: catálogos, clasificación de intakes y checklists configurables por caso.
- Bloque 4: revisión de cumplimiento, vigencia de documentos, alertas operativas y siguientes acciones.
- Bloque 5: base operativa para casos, organizaciones, personas y trazabilidad.
- Bloque 6: Mission Control, Cases, Case Detail, Yarvis Conversation, Organizations, People, Conversational Intake con confirmación de contexto y validación frontend/backend.

## Ejecutar el entorno local

Requisitos:

- Docker
- Docker Compose

```bash
docker compose up -d
```

Servicios disponibles:

- Frontend: http://localhost:5173
- API: http://localhost:8000/docs
- PostgreSQL: localhost:5432

Para detener los servicios sin borrar los datos de PostgreSQL:

```bash
docker compose down
docker compose up -d
```

El volumen `pgdata` se conserva y las migraciones siguen aplicándose sobre el mismo estado.

## Migraciones Alembic

La API no crea tablas automáticamente. Para aplicar el esquema versionado:

```bash
docker compose exec api alembic upgrade head
```

La migración activa de conversaciones está en:

- apps/api/migrations/versions/20260712_05_conversations.py

Para revisar el estado actual del head:

```bash
docker compose exec api alembic current
```

## Catálogos

Los catálogos se cargan de forma idempotente con:

```bash
docker compose exec api python -m yarvis_api.catalogs
```

Esto inicializa tipos de caso, tipos de documento y reglas base para los checklists.

## Casos, Checklists, Evidencia, Alertas y Mission Control

- Crear un caso mediante `POST /cases`.
- Crear una checklist para un caso con `POST /cases/{case_id}/checklists`.
- Registrar cumplimiento con `POST /case-checklists/{id}/requirements/{requirement_id}/fulfill`.
- Validar o rechazar el cumplimiento con los endpoints de `requirement-fulfillments`.
- Registrar evidencia en `POST /cases/{case_id}/evidence`.
- Revisar la bitácora inmutable en `GET /cases/{case_id}/events`.
- Evaluar el estado operativo con `POST /cases/{case_id}/evaluate-operational-state`.
- Consultar resumen y atención en `GET /mission-control/summary` y `GET /mission-control/attention-items`.

## Conversational Intake

El flujo conversacional permite capturar texto o adjuntos desde una conversación, crear un IntakeItem y confirmar el contexto asociado al caso.

### Flujo recomendado

1. Abrir http://localhost:5173 y navegar a "Yarvis Conversation".
2. Crear o seleccionar una conversación vinculada a Organización, Persona y Caso.
3. Enviar un mensaje; se crea un IntakeItem a partir del texto.
4. Registrar adjuntos como metadatos (sin binarios).
5. Confirmar contexto para enlazar el IntakeItem con el Caso y crear Evidence cuando corresponda.
6. Revisar el evento asociado en la vista de detalle del Caso.

### Confirmación de contexto

```bash
curl -X POST http://localhost:8000/intake/{intake_id}/confirm-context -H "Content-Type: application/json" -d '{"organization_id":"...","person_id":"...","case_id":"...","evidence_type":"document"}'
```

## Frontend React

El frontend usa React, Vite, React Router y TanStack Query. La aplicación principal vive en `apps/web/src/App.tsx` y el punto de entrada mínimo en `apps/web/src/main.tsx`.

Pantallas principales:

## Sprint 7.2 Highlights

- Observation Engine foundation: SourceRecord, DocumentRecord, Observation, ResolutionDecision, OperationalPolicy, PolicyEvaluation, AttentionItem.
- Deterministic operational policy endpoints and seed catalog for NetPay inactivity/churn/critical-sales/asset-recovery.
- NetPay import adapter now emits observation records with provenance.
- Mission Control summary now includes unresolved observations, identity conflicts, duplicates, policy matches, insufficient-data evaluations, and pending human approvals.

## Sprint 7.2 Explicit Non-Scope

- No Gmail activation.
- No WhatsApp integration.
- No Google Drive integration.
- No Portal NetPay automation.
- No tax calculations.

## Sprint 7.3A Highlights

- Controlled Data Intake backend endpoints for multipart upload, parsing, preview, and confirmation.
- Local document repository adapter with safe storage references and SHA-256 duplicate detection.
- Deterministic XLSX intake and NetPay mapping proposals.

- Mission Control
- Cases
- Case Detail
- Yarvis Conversation
- Organizations
- People

## Pruebas backend

```bash
docker compose exec api sh -lc "pip install -q -r requirements-dev.txt && pytest -ra"
```

Las pruebas usan la base separada `yarvis_test`; Pytest la crea y trunca entre ejecuciones.

## Pruebas frontend

```bash
docker compose exec web sh -lc "npm install && npm test"
```

## Uso NetPay Operations Inbox

1. Importar correo NetPay normalizado:

```bash
curl -X POST http://localhost:8000/netpay/import-email -H "Content-Type: application/json" -d '{"gmail_message_id":"gmail-001","gmail_thread_id":"thread-001","from_address":"operaciones@netpay.mx","to_addresses":["netpay@empresa.com"],"cc_addresses":[],"reply_to_addresses":[],"delivered_to":"netpay.ops@empresa.com","subject":"Folio NP-2026-001 Guia 1234567890 envio","body":"Folio NetPay: NP-2026-001\nGuia: 1234567890\nStore ID: STO-100\nSerie TPV: TPV-ABC-01","received_at":"2026-07-13T12:00:00Z"}'
```

2. Listar casos NetPay y pendientes:

```bash
curl http://localhost:8000/netpay/service-cases
curl http://localhost:8000/netpay/service-cases/pending
```

3. Confirmar investigación manual:

```bash
curl -X PATCH http://localhost:8000/netpay/service-cases/{id}/investigation -H "Content-Type: application/json" -d '{"case_type":"installation","customer_name":"Cliente","merchant_name":"Comercio","address":"Domicilio","store_id":"STO-100","device_serial":"TPV-ABC-01","movement_type":"outbound","notes":"confirmado","investigation_status":"confirmed"}'
```

4. Registrar envío/recolección:

```bash
curl -X POST http://localhost:8000/netpay/service-cases/{id}/shipments -H "Content-Type: application/json" -d '{"tracking_number":"TRK-001","carrier":"DHL","direction":"outbound","status":"shipped"}'
```

5. Consultar inventario de terminales:

```bash
curl http://localhost:8000/netpay/devices
```

## Build frontend

```bash
docker compose exec web sh -lc "npm run build"
```

## Operación y troubleshooting básico

- Si los servicios no arrancan, revisar `docker compose ps` y `docker compose logs api web postgres`.
- Si una migración falla, validar que PostgreSQL esté saludable y volver a ejecutar `alembic upgrade head`.
- Si una prueba de backend falla por conexión, verificar que `postgres` responda y que la base `yarvis_test` exista.
- Si el frontend no carga, confirmar que `http://localhost:5173` y `http://localhost:8000/docs` estén accesibles.
- Si se necesita reiniciar desde cero de forma segura, detener servicios con `docker compose down` y conservar `pgdata`.

## Operación manual, evidencia y bitácora

Tras aplicar migraciones, se puede registrar texto recibido y asociarlo a un caso:

```bash
curl -X POST http://localhost:8000/intake -H "Content-Type: application/json" -d '{"source_type":"manual_text","content_type":"text/plain","text_content":"Cliente solicitó cambio de servicio"}'
curl -X POST http://localhost:8000/intake/{intake_id}/link-case/{case_id}
```

Registrar evidencia sin almacenar archivos binarios y consultar la bitácora inmutable:

```bash
curl -X POST http://localhost:8000/cases/{case_id}/evidence -H "Content-Type: application/json" -d '{"evidence_type":"photo","title":"Fotografías de preparación"}'
curl http://localhost:8000/cases/{case_id}/events
```

## Revisión, vigencia y alertas

Revisar y validar un cumplimiento usando su fecha documental, o rechazarlo con un motivo:

```bash
curl -X POST http://localhost:8000/requirement-fulfillments/{id}/review -H "Content-Type: application/json" -d '{"confirmed_by":"operador"}'
curl -X POST http://localhost:8000/requirement-fulfillments/{id}/validate -H "Content-Type: application/json" -d '{"document_date":"2026-07-12T00:00:00Z","reviewed_by":"operador"}'
curl -X POST http://localhost:8000/requirement-fulfillments/{id}/reject -H "Content-Type: application/json" -d '{"rejection_reason":"documento ilegible"}'
```

Evaluar y gestionar el estado operativo:

```bash
curl -X POST http://localhost:8000/cases/{case_id}/evaluate-operational-state
curl http://localhost:8000/cases/{case_id}/alerts
curl -X POST http://localhost:8000/alerts/{alert_id}/acknowledge
curl -X POST http://localhost:8000/alerts/{alert_id}/resolve
curl http://localhost:8000/cases/{case_id}/next-action-suggestions
curl -X POST http://localhost:8000/next-action-suggestions/{id}/accept
```

Las vigencias de 30/90 días son reglas operativas configurables, no afirmaciones legales universales. Los cambios posteriores del catálogo no reescriben cumplimientos ya validados; una recalculación futura requerirá una acción explícita y auditable.
