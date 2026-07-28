# WS-006A — Process Domain Foundation

## Status

Implemented engineering increment; pending validation and review.

## Purpose

WS-006A establishes the tenant-owned, generic backend model for versioned operational processes. It deliberately models process structure only; it does not introduce a visual designer, a BPMN runtime, process instances, automation, or domain-specific process seeds.

## Model and Ownership

`ProcessDefinition` is owned by one Organization and represents one immutable version of a named process. A definition begins in `draft`, may be published once its graph is valid, and may later be retired. A `ProcessStage` and `ProcessTransition` are owned by the definition version and inherit its organization. Composite database foreign keys and service validation keep transitions within their own definition/version and tenant.

The supported stage types are `start`, `work`, `wait`, `decision`, and `terminal`. Stage keys and display order are each unique within a definition version. Metadata is optional JSON object data, stored only through the existing typed JSONB pattern.

## Invariants and Versioning

- Only drafts accept stage and transition mutations.
- Publishing requires exactly one `start` stage and at least one `terminal` stage.
- A published or retired definition is immutable. There is no delete endpoint for a definition version.
- Changes after publication require `CreateProcessVersion`, which clones the definition graph into the next draft version of the same organization/name.
- A transition can reference only stages of the same definition/version; cross-definition and cross-tenant references are rejected before persistence.
- Definitions, stages, and transitions are tenant-scoped. Cross-organization reads and mutations return `404` rather than disclosing resource existence.

## Endpoints

All endpoints are rooted at `/process-definitions`.

- `POST /` creates a draft.
- `GET /` and `GET /{id}` provide governed reads.
- `POST /{id}/stages`, `PUT`/`DELETE /{id}/stages/{stage_id}` mutate a draft graph.
- `POST /{id}/transitions`, `PUT`/`DELETE /{id}/transitions/{transition_id}` mutate a draft graph.
- `POST /{id}/publish` publishes a valid draft.
- `POST /{id}/retire` retires a published version.
- `POST /{id}/versions` creates the next draft version from a published or retired version.

`process.definition.manage` authorizes mutations; `process.definition.read` authorizes reads. The authenticated principal's `organization_id` is the exclusive ownership source.

## Events

WS-006A reuses the generic append-only `DomainEvent` store. Process events are recorded in the same Unit of Work as the associated lifecycle mutation:

- `process_definition.created`
- `process_definition.version_created`
- `process_definition.published`
- `process_definition.retired`

This is process lifecycle evidence, not a second Event Store or a process Timeline API.

## Interaction Contracts

The application binds `IC-PROCESS-CMD-001` through `IC-PROCESS-CMD-010`, `IC-PROCESS-QRY-001` through `IC-PROCESS-QRY-002`, and `IC-PROCESS-EVT-001` through `IC-PROCESS-EVT-004`. Their authority and ownership are recorded in the canonical interaction catalog.

## Deferred Scope

No frontend, graph designer, BPMN, process-instance runtime, SLA, notifications, automation, AI behavior, or Energía Fotónica/Netpay-specific process definition is included in this increment.
