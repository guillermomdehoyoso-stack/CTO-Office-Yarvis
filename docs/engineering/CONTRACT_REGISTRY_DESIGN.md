# YARVIS
# Contract Registry Design

## Status: Ratified Engineering Design

## Amendment History

| Amendment | Status | Summary |
| --- | --- | --- |
| `CONTRACT-REGISTRY-AMENDMENT-001` | Ratified engineering-design alignment | Aligns F-006 projection metadata with the Tier 1 catalog without changing architectural authority, contract identity, ownership, or runtime scope. |

## 1. Work-Package Identity and Name

**Work package:** F-006 — Contract Registry  
**Phase:** Design Ratification only

## 2. Purpose

F-006 defines the engineering design for one explicit, per-application Contract
Registry. The registry holds governed technical metadata for Yarvis Interaction
Contracts. It makes the ratified Tier 1 contract baseline mechanically
validatable during composition without making the registry a source of domain
truth or a runtime dispatch mechanism.

The registry preserves the catalog's operational language: a contract has one
owner, one owning capability, a stable semantic identity, an independently
governed version, and explicit lifecycle and operational status.

## 3. Architectural Authority

Authority is ordered as follows:

1. `YARVIS_CONSTITUTION.md`
2. Ratified Foundation, Platform, Platform Engineering, and Application
   Architecture artifacts
3. `INTERACTION_CONTRACT_CATALOG.md`
4. `INTERACTION_CONTRACT_REVIEW.md`
5. `ARCHITECTURAL_DECISION_TRACE.md`
6. `TECHNICAL_BLUEPRINT.md` and `TECHNICAL_BLUEPRINT_REVIEW.md`
7. This design

This design specializes the ratified interaction-contract model. It must not
reinterpret ownership, authority, lifecycle semantics, or the catalog's
canonical metadata.

## 4. Terminology

An **Interaction Contract** is the canonical, governed semantic agreement by
which Yarvis requests action, obtains governed information, asserts an
owner-governed occurrence, or communicates non-authoritative information.

The **Contract Registry** is a technical, machine-readable projection of
governed contract metadata. The Markdown catalog remains the architectural
authority. A registry entry neither creates canonical reality nor grants
execution, mutation, dispatch, or handler authority.

**Owner module** is the canonical technical module that owns the contract. It
is distinct from a consumer, transport, application service, or adapter.

## 5. Contract Kinds

F-006 supports exactly these canonical contract kinds:

| Contract type | Meaning |
| --- | --- |
| `Command` | Governed intent directed to an authoritative owner. |
| `Query` | Request for governed information with no authoritative side effect. |
| `Event` | Assertion that an owner-governed occurrence happened. |
| `Notification` | Informational communication that is never an authoritative domain assertion. |

The identifier abbreviations `CMD`, `QRY`, `EVT`, and `NTF` occur only in the
ratified identifier convention. They are not substitute contract kinds.

## 6. Identity and Versioning

`interaction_contract_id` is the stable, globally unique semantic identifier.
It follows the catalog convention:

```text
IC-{OWNING-CONTEXT}-{TYPE}-{SEQUENCE}
```

Examples include `IC-IDENTITY-QRY-001` and `IC-NETPAY-CMD-001`. The identifier
is semantic, deployment-stable, and contains no version.

`version` is a separate semantic-version value in the exact
`MAJOR.MINOR.PATCH` form, where each component is a non-negative decimal
integer with no leading zero except `0`. F-006 has no prerelease, build,
compatibility-negotiation, or migration implementation. The Tier 1 baseline is
`1.0.0`.

A material ownership change is not an ordinary compatible evolution. It
requires the catalog's major-version analysis or a new contract before a
registry projection may be changed.

## 7. Ownership Model

Each registry definition declares exactly one:

- `owner_module_id` — a Module Registry identifier;
- `owning_context` — the catalog's bounded-context owner; and
- `owning_capability` — the owner capability within that context.

The registry validates that `owner_module_id` exists in the same sealed
application Module Registry. It does not infer ownership from an identifier,
Python import path, display name, handler, payload, or external system.

The owner module is the technical projection of the owning context for F-006.
The registry does not claim that a technical module, consumer, or provider may
mutate a foreign context's canonical state.

## 8. Exact Metadata Model

The future immutable `InteractionContractDefinition` projection must contain
the following fields and no binding fields in F-006:

| Field | Required meaning and validation |
| --- | --- |
| `interaction_contract_id` | Stable catalog identifier; unique within a registry and conformant to the catalog convention. |
| `version` | Separate semantic version in the F-006 format. |
| `contract_type` | One of the four governed contract kinds. |
| `owner_module_id` | Existing Module Registry module identifier. |
| `owning_context` | Nonblank catalog owning-context name. |
| `owning_capability` | Nonblank catalog owning capability. |
| `name` | Nonblank canonical contract name/title. |
| `semantic_purpose` | Nonblank catalog-aligned purpose. |
| `lifecycle` | Architectural governance state. |
| `operational_status` | Independently governed operational availability state. |
| `criticality` | Architectural and operational impact classification. |
| `primary_consumer_or_use_case` | Nonblank catalog-faithful text from the Tier 1 “Primary consumer/use case” column. It is not an authorization rule. |
| `architectural_steward` | Optional governance metadata. It may be `None`; when present, it is nonblank and uses ratified terminology. |
| `traceability_references` | Optional immutable collection. It defaults to `()`; every supplied entry is nonblank. |

The Tier 1 catalog provides a single “Primary consumer/use case” value. F-006
therefore preserves it as one governed text field and does not parse it into
consumers, use-case identifiers, authorization subjects, or policy bindings.
It grants no ownership or access authority.

The catalog requires architectural stewardship and traceability at the
architectural level but does not provide a per-contract mapping for the Tier 1
projection. F-006 preserves both fields as optional enrichment metadata and
does not infer or fabricate their values.

The complete semantic fields specified by the Markdown catalog remain
architectural authority. Fields such as input/output semantics, temporal
semantics, privacy classification, evidence lineage, failure semantics,
compatibility policy, dependencies, resulting contracts, and detailed
conformance rules are not runtime bindings in F-006. They remain governed in
the catalog until a later, ratified implementation work package requires a
bounded projection of them.

## 9. Governed Vocabularies

F-006 validates these exact values:

| Field | Allowed values |
| --- | --- |
| `contract_type` | `Command`, `Query`, `Event`, `Notification` |
| `lifecycle` | `Draft`, `Proposed`, `Ratified`, `Deprecated`, `Retired` |
| `operational_status` | `Planned`, `Implemented`, `Verified`, `Production`, `Suspended`, `Removed` |
| `criticality` | `Critical`, `Core`, `Operational`, `Informational` |

Lifecycle and operational status are separate values. A valid pair such as
`Ratified` / `Planned` must remain representable. F-006 validates membership in
each vocabulary; it does not introduce an unratified cross-product policy.
Retired contracts must not accept new interactions when dispatch is introduced
later; F-006 records their state but does not dispatch anything.

## 10. Registry Responsibilities and Public API

The canonical implementation authority will be
`apps/api/src/yarvis_api/contract_registry.py`. It will expose one
per-application `ContractRegistry` and a small immutable definition type.

| API | Exact behavior |
| --- | --- |
| `register(definition)` | Validate the definition and add it before sealing; reject duplicate identifier and unknown owner. |
| `register_many(definitions)` | Register the supplied iterable in its explicit order using `register`. |
| `get(interaction_contract_id)` | Return the registered definition or `None` when absent, matching the existing Module Registry lookup convention. |
| `contains(interaction_contract_id)` | Return whether the identifier is registered. |
| `list()` | Return an immutable tuple in explicit registration order. |
| `list_by_kind(contract_type)` | Return an immutable, registration-ordered tuple filtered by canonical type. |
| `list_by_owner(owner_module_id)` | Return an immutable, registration-ordered tuple filtered by exact owner module ID. |
| `seal()` | Finalize the registry once; later mutation is rejected. Repeated sealing is idempotent. |
| `is_sealed` | Report whether the registry has been finalized. |

The registry does not expose lookup by payload, message type, result type,
handler, subscriber, transport, endpoint, or provider implementation.

## 11. Validation Rules

Before sealing, F-006 validates:

1. `interaction_contract_id` is nonblank, unique, and conforms to the catalog
   identifier convention.
2. `version` conforms to the F-006 semantic-version format.
3. All required text metadata fields are present and nonblank. The optional
   `architectural_steward`, when present, is nonblank. The optional immutable
   `traceability_references` collection contains only nonblank entries.
4. `contract_type`, `lifecycle`, `operational_status`, and `criticality` use
   their governed vocabularies.
5. `owner_module_id` exists in the Module Registry belonging to the same
   application composition.
6. Lifecycle is never substituted for operational status, nor operational
   status for lifecycle; each is independently validated against its own
   vocabulary.
7. Mutation is rejected after sealing.

F-006 does not validate contract dependency graphs, compatibility matrices,
payload schemas, handler drift, consumer availability, runtime implementation
readiness, or a separation of consumers from use cases. Those controls require
later ratified work and must not be implied by metadata registration.

## 12. Lifecycle, Sealing, and Isolation

Composition explicitly creates a new registry, registers the selected
definitions, validates them against that application's sealed Module Registry,
then seals the Contract Registry before application use.

Each `FastAPI` application owns its own registry snapshot. There is no mutable
process-global registry, import-time registration, package discovery, or
shared service-locator state. A sealed registry is immutable in observable
membership and order.

## 13. Bootstrap Integration

The intended public composition API after implementation is:

```python
create_app(settings=None, modules=None, contracts=None)
```

The required composition order is:

```text
Settings
  → ModuleRegistry
  → ContractRegistry
  → ApplicationState
  → route registration
```

`ApplicationState` will gain a typed `contract_registry` field. It remains a
small typed technical root, not a generic service locator. Module composition
and contract composition remain explicit independent inputs; a module must not
import the Contract Registry to self-register contracts.

## 14. None and Explicit Empty Iterable Semantics

After the canonical Tier 1 projection exists:

| Input | Required behavior |
| --- | --- |
| `modules=None` | Compose the F-005A canonical ten-module baseline. |
| explicit `modules` iterable | Replace that baseline for this application only. |
| `modules=()` | Compose an explicitly empty sealed Module Registry. |
| `contracts=None` | Compose the explicit canonical Tier 1 contract baseline. |
| explicit `contracts` iterable | Replace the Tier 1 baseline for this application only. |
| `contracts=()` | Compose an explicitly empty sealed Contract Registry. |

F-006 design itself introduces neither a contract baseline nor a runtime API
change. The `contracts=None` behavior begins only with the later implementation
of the approved canonical Tier 1 projection.

## 15. Canonical Tier 1 Projection Model

The eventual explicit Python projection belongs at:

```text
apps/api/src/yarvis_api/canonical_contracts.py
```

It will define an immutable ordered tuple of 37
`InteractionContractDefinition` instances, one for every Tier 1 entry in
`INTERACTION_CONTRACT_CATALOG.md`. It must be written and maintained
explicitly, not parsed from Markdown, generated dynamically, discovered by
imports, or derived from handlers. The Markdown catalog remains the
architectural authority; the Python tuple is its bounded technical projection.

The projection must retain each contract's stable identifier, `1.0.0` version,
`Proposed` lifecycle, `Planned` operational status, owner module/context/
capability, criticality, and catalog-faithful primary consumer/use-case text.
It may leave optional stewardship and traceability enrichment absent. No
contract dependency is encoded unless later ratified scope requires it.

## 16. Typed Error Model

The minimal future error hierarchy is:

```text
ContractRegistryError
├── InvalidContractDefinitionError
├── DuplicateContractError
├── UnknownContractOwnerError
└── ContractRegistrySealedError
```

`get()` returning `None` makes a separate not-found error unnecessary.
Invalid identifier, semantic version, required metadata, governed vocabulary,
and lifecycle/status misuse are all invalid-definition failures. No
`DuplicateMessageTypeError` is permitted because message bindings are deferred.

## 17. Explicit Exclusions and Deferrals

F-006 does not implement or authorize:

- payload classes, result types, or message types;
- handlers, subscribers, buses, dispatch, or routing;
- transport binding, serialization, HTTP schema binding, or API endpoints;
- persistence, database integration, transactions, outbox, or inbox pattern;
- workers, scheduler, retries, execution idempotency, or plugin loading;
- dynamic discovery, import-time registration, package scanning, or global
  registry state;
- detailed compatibility enforcement or contract dependency graph enforcement;
- steward-assignment governance, detailed traceability mapping, separation of
  consumers from use cases, authorization subjects, or policy bindings;
- domain behavior, canonical-state mutation, or runtime source-of-truth
  semantics.

## 18. Acceptance Criteria and Expected Implementation Artifacts

F-006 implementation is complete only when:

1. one typed, per-application Contract Registry exists;
2. the 37 explicit Tier 1 metadata definitions load through composition;
3. IDs, versions, kind, ownership, lifecycle, operational status, criticality,
   and catalog-faithful primary consumer/use-case text validate; optional
   stewardship and traceability enrichment validate when supplied;
4. owner-module validation uses the per-application sealed Module Registry;
5. lifecycle and operational status remain independently represented;
6. duplicate, invalid, unknown-owner, and post-seal mutation failures are
   typed and deterministic;
7. `None` and explicit-empty composition behavior is tested and isolated;
8. no bus, handler, payload binding, persistence, worker, or domain behavior is
   introduced; and
9. architecture conformance proves there is no global or import-time registry.

Expected implementation artifacts are limited to the registry implementation,
explicit canonical Tier 1 projection, focused tests, architecture-conformance
tests, bootstrap/application-state integration, and an implemented baseline
record. The exact file list remains subject to the subsequent implementation
work package.

## 19. Conformance Requirements

Conformance tests must prove per-application isolation; explicit registration;
stable registration order; `get()` absence behavior; kind and owner filtering;
duplicate rejection; invalid metadata rejection; unknown owner rejection;
sealing; canonical Tier 1 coverage of all four types; exact owner-module
coverage; independent lifecycle/operational-status representation; absence of
global registration and dynamic discovery; and no runtime resource startup
during composition.

## 20. Unresolved Decisions

There are no F-006 design blockers or required architecture amendments.

The following are intentionally deferred rather than unresolved: steward
assignment governance, detailed traceability mapping, separation of consumers
from use cases, authorization subjects, policy bindings, payload and response
schemas, bindings and handler drift, detailed compatibility and dependency
enforcement, privacy classes by consumer, freshness thresholds, and
transport/API representation. They require a later ratified work package and
must not be inferred by F-006.

## 21. Closing Statement

F-006 turns the ratified operational language into a validated technical
projection while preserving its authority boundaries. Contract metadata makes
ownership, lifecycle, readiness, and traceability inspectable; it does not
make the registry a bus, a service locator, or a replacement for the Yarvis
Reality Graph.
