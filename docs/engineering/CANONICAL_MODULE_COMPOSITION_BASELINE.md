# YARVIS
# Canonical Module Composition Baseline

## Status: Implemented Engineering Baseline - F-005A Canonical Module Composition

## 1. Purpose and Sources

F-005A closes the composition gap between the Module Registry and the ratified Tier 1 interaction-contract owners. It adds explicit, empty technical context-module declarations only; it does not add domain behavior, handlers, routes, persistence, contracts, or dispatch.

The source authorities are `BOUNDED_CONTEXTS.md` context IDs and ownership, `TECHNICAL_BLUEPRINT.md` executable context-module structure, `APPLICATION_ARCHITECTURE.md` module composition rules, and `INTERACTION_CONTRACT_CATALOG.md` Tier 1 owners.

## 2. Canonical Module Baseline

`apps/api/src/yarvis_api/canonical_modules.py` owns the explicit immutable baseline:

| Context ID | Technical module ID | Display name | Tier 1 owner |
| --- | --- | --- | --- |
| `identity` | `identity` | Identity | yes |
| `governance` | `governance` | Governance | yes |
| `relationship` | `relationship` | Relationship | yes |
| `observation_evidence` | `observation_evidence` | Observation & Evidence | yes |
| `knowledge` | `knowledge` | Knowledge | yes |
| `decision_intelligence` | `decision_intelligence` | Decision Intelligence | no |
| `execution` | `execution` | Execution | yes |
| `automation` | `automation` | Automation | no |
| `mission_control` | `mission_control` | Mission Control | yes |
| `netpay_merchant_operations` | `netpay_merchant_operations` | Netpay Merchant Operations | yes |

The ten modules satisfy the blueprint's context-module composition baseline. The eight marked Tier 1 owner cover every ratified Tier 1 contract owner exactly once. Capabilities remain owned by their context; this technical declaration does not encode, alter, or implement them.

## 3. Identifier, Dependencies, and Bootstrap Semantics

Module IDs are the ratified context IDs and conform to the stable lower-case dotted, hyphenated, or underscored module-ID convention. They are not import paths or runtime state. The baseline encodes no module dependencies: the ratified relationships are contract-mediated context interactions, not direct composition or startup dependencies. Adding registry dependencies would therefore invent technical coupling.

`create_app(modules=None)` composes this canonical baseline. `create_app(modules=<iterable>)` composes exactly the supplied declarations. `create_app(modules=())` intentionally constructs an explicitly empty sealed registry for isolated tests. Every application owns its own sealed registry; explicit injection cannot leak into subsequent applications.

No canonical module currently registers a route, initializes a database, starts a worker or scheduler, creates a handler, invokes a service, or changes business state.

## 4. F-006 Enablement and Deferrals

F-006 can now validate each Tier 1 contract's `owner_module_id` against an explicit canonical module baseline. Contract definitions, contract metadata, contract handlers, message bindings, buses, persistence, and dispatch remain deferred. The baseline is not a plugin mechanism, dynamic discovery mechanism, service locator, or feature-flag system.

## 5. Validation and Closing Statement

Focused tests prove exact module IDs, uniqueness, sealing, no route hooks, default composition, explicit injection, explicit empty composition, and per-application isolation. Architecture conformance verifies the baseline is explicit and technical. Quality, full backend tests, Compose startup, and neutral HTTP smoke tests provide the remaining evidence.

F-005A preserves the modular-monolith rule: context identity is available for governed composition and future contract ownership validation, while all domain authority and behavior remain within their future context implementations.
