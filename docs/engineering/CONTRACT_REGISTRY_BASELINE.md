# YARVIS
# Contract Registry Baseline

## Status: Implemented Engineering Baseline — F-006 Contract Registry

## 1. Work-Package Scope and Authority

F-006 implements the bounded technical projection defined by
`CONTRACT_REGISTRY_DESIGN.md` and aligned by
`CONTRACT_REGISTRY_DESIGN_AMENDMENT_001.md`. The Interaction Contract Catalog
remains the architectural authority. This baseline records metadata only; it
does not create a bus, handler binding, transport, persistence mechanism, or
domain source of truth.

## 2. Implementation Paths and Responsibilities

`apps/api/src/yarvis_api/contract_registry.py` owns immutable
`ContractDefinition`, governed vocabularies, the per-application
`ContractRegistry`, typed validation errors, and explicit registry construction.
`apps/api/src/yarvis_api/canonical_contracts.py` owns the explicit immutable
Tier 1 projection. `bootstrap.py` constructs the sealed Module Registry before
the sealed Contract Registry and stores both in typed application state.

The registry registers, retrieves, lists, filters by kind or owner, validates,
and seals metadata. It never dispatches, authorizes, serializes, routes,
persists, schedules, or executes a contract.

## 3. Metadata, Identity, and Governed Vocabularies

Required metadata is `interaction_contract_id`, `version`, `contract_type`,
`owner_module_id`, `owning_context`, `owning_capability`, `name`,
`semantic_purpose`, `lifecycle`, `operational_status`, `criticality`, and
`primary_consumer_or_use_case`. Optional metadata is
`architectural_steward` and immutable `traceability_references`.

IDs use `IC-{OWNING-CONTEXT}-{TYPE}-{SEQUENCE}` and versions use separate
`MAJOR.MINOR.PATCH` values. Contract types are Command, Query, Event, and
Notification. Lifecycle is Draft, Proposed, Ratified, Deprecated, or Retired.
Operational status is Planned, Implemented, Verified, Production, Suspended,
or Removed. Criticality is Critical, Core, Operational, or Informational.
Lifecycle and operational status are independently represented.

The Tier 1 baseline contains exactly 37 explicit definitions. Their catalog
text is preserved in `primary_consumer_or_use_case`; it is not parsed into
authorization, consumer, or use-case semantics. Steward assignment and
detailed traceability remain optional future governance enrichment.

## 4. Ownership, Sealing, and Bootstrap Semantics

Each definition names an explicit owner module. Registration validates that the
owner exists in the same supplied Module Registry. There is no global registry,
dynamic discovery, import-time registration, or service-locator behavior.

`create_app(settings=None, modules=None, contracts=None)` composes settings,
Module Registry, Contract Registry, application state, and routes in that
order. `modules=None` uses the canonical ten modules; `contracts=None` uses the
canonical 37 Tier 1 contracts. Explicit iterables replace their respective
baselines for one application, and explicit empty iterables create sealed empty
registries. Registries are isolated per application and reject mutation after
sealing.

## 5. Typed Errors, Exclusions, and Deferrals

Typed failures are `ContractRegistryError`,
`InvalidContractDefinitionError`, `DuplicateContractError`,
`UnknownContractOwnerError`, and `ContractRegistrySealedError`.

F-006 explicitly excludes payload/result/message types, handlers, bindings,
buses, dispatch, subscriptions, HTTP schemas, transport serialization,
persistence, database integration, Unit of Work, transactions, workers,
scheduler, retries, idempotency execution, authorization, dynamic discovery,
and plugins. It also defers steward assignment governance, detailed
traceability mapping, consumer/use-case separation, policy bindings,
compatibility enforcement, and contract dependency enforcement.

## 6. Validation, Files, and Readiness

Focused tests cover immutable definitions and metadata, vocabularies, ID and
version validation, owner validation, duplicate and sealing errors, filtering,
empty registries, canonical count/distribution, application isolation, default
and explicit-empty composition, neutral health, and documentation routes.
Architecture tests verify that the registry and projection are explicit
technical files without framework transport or discovery imports.

F-006 enables F-007 Database/Migrations and F-013 Test/Conformance Foundation.
It introduces no database, worker, scheduler, or business behavior.

## 7. Closing Statement

The Contract Registry makes Yarvis interaction metadata mechanically
inspectable while preserving the catalog's authority and every context's
canonical ownership.
