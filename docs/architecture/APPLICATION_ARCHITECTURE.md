# YARVIS
# Application Architecture

## Version 1.0

**Status:** Draft for Ratification
**Authority:** Derived from the Yarvis Constitution, Platform Engineering Overview, Bounded Contexts, and Context Interaction Model
**Purpose:** Define the canonical, implementation-neutral application architecture through which Yarvis bounded contexts expose, coordinate, and execute application behavior while preserving domain ownership, authority boundaries, contracts, invariants, provenance, identity, governance, and traceability.

> **How must the application be organized so that software execution preserves the canonical ownership and interaction model of Yarvis?**

## 1. Position in Phase IV

This artifact translates `PLATFORM_ENGINEERING_OVERVIEW.md`, `BOUNDED_CONTEXTS.md`, and `CONTEXT_INTERACTION_MODEL.md` into an application structure. It does not alter the ten ownership assignments, select technology, or define a deployment topology.

> **Application components coordinate behavior; they do not redefine domain authority.**
>
> **Application services orchestrate use cases; bounded contexts preserve canonical semantics and invariants.**
>
> **Infrastructure adapts technologies to the application; the application must not depend on infrastructure-specific semantics.**
>
> **Every authoritative mutation must terminate inside the context that owns the affected canonical state.**
>
> **Application boundaries must preserve context boundaries.**
>
> **Cross-context coordination must use explicit contracts.**
>
> **Persistence is an implementation concern, not a source of domain authority.**
>
> **Application convenience must not create hidden shared ownership.**
>
> **Dependency direction must point toward greater architectural stability.**
>
> **Internal composition may be shared; domain authority may not.**

## 2. Architectural Style and Modular Monolith First

Yarvis begins as a **modular monolith** containing explicit context modules. Shared runtime, process, transaction infrastructure, or technical libraries do not imply shared domain authority. In-process calls still traverse public application contracts. A context is extracted only when evidence shows material divergence in scalability, availability, security, regulatory isolation, deployment cadence, runtime dependency, operational ownership, or failure isolation; it is never extracted merely because microservices are fashionable.

## 3. Canonical Layer Model

```text
Interface → Application → Domain
Infrastructure implements inward-owned ports and may depend inward
```

| Layer | Responsibilities | Must not own |
| --- | --- | --- |
| Domain | canonical objects, aggregates where applicable, entities, value objects, domain services/policies, invariants, authoritative transitions, semantic domain events, domain validation | interfaces, adapters, persistence/vendor/transport semantics |
| Application | use cases, commands/queries/events, workflow coordination, authorization invocation, transaction/idempotency coordination, ports, traces, application error translation | canonical business invariants or hidden cross-context state |
| Interface | inbound contract translation, output presentation, transport-neutral validation, authentication-context intake, protocol adaptation, user/system/operator surfaces | authoritative domain decisions or business policy |
| Infrastructure | persistence, external-system, transport, scheduling, document/file, telemetry, and notification adapters; technical port implementations and vendor isolation | canonical policy, authority, or domain truth |

The Domain depends on none of Application, Interface, Infrastructure, vendors, persistence frameworks, or transport protocols. Application does not depend on concrete infrastructure implementations. Repositories and ports are owned inward; adapters implement them outward.

## 4. Modules, Boundaries, and Composition

Each bounded context maps to one or more `ApplicationModule`s with an explicit public boundary and protected internal boundary. An `ApplicationModule` contains `application_module_id`, name, bounded context, purpose, owned use cases, exposed application contracts, internal application services, domain model reference, inbound/outbound ports, dependencies, transaction boundaries, consistency guarantees, authorization/provenance/traceability responsibilities, prohibited dependencies, extraction readiness, status, version, provenance, metadata.

Public boundaries expose stable application contracts only. Internal domain models, persistence representations, vendor models, and unrestricted repositories do not cross module boundaries. Module composition shares bootstrapping and technical composition, never authority.

## 5. Application Services, Use Cases, and Handlers

`ApplicationService`: `application_service_id`, name, owning module, use cases coordinated, inputs/outputs, domain capabilities/ports invoked, authorization, transaction/idempotency/failure/uncertainty/correlation/provenance requirements, prohibited responsibilities, status, version, provenance, metadata.

`UseCaseDefinition`: `use_case_id`, name, owning context, initiator, business intent, input/output contract, preconditions, required authority, domain operations, contexts involved, transaction/consistency/idempotency expectations, failure and business outcomes, emitted events, traceability/provenance, status, version, metadata.

`CommandHandlerDefinition`, `QueryHandlerDefinition`, and `EventHandlerDefinition` identify owner, contract, initiating input, invoked domain capability, authorization, idempotency, traceability, failure/uncertainty semantics, resulting events/projections, status, version, provenance, metadata.

Application services coordinate use cases but never become an anemic replacement for domain behavior. Command handlers invoke owner-domain transitions. Query handlers have no hidden mutation. Event handlers treat foreign events as assertions: they may update projections, initiate local commands, create observations, trigger workflow steps, or create attention signals, but never mutate another context’s canonical state. Notifications remain distinct from domain events.

## 6. Workflows, Policies, Ports, Adapters, and Repositories

`WorkflowCoordinator` records coordinator, process purpose/state, participating contexts, contracts, authorization, cancellation/compensation/terminal/uncertainty behavior, traceability, status, provenance, metadata. It may own process state only when that process state is a distinct governed concept. Orchestration coordinates; choreography reacts to owner-produced assertions; neither creates shared canonical state.

Domain services and domain policies express domain semantics. Application policies coordinate application concerns. Specifications express reusable, explicit decision criteria. Organizational authority and governance policies are evaluated through Governance contracts or stable policy abstractions; local domain policy never redefines organizational authority.

`ApplicationPort`: `application_port_id`, name, owning layer/module, direction, purpose, semantic contract, accepted operations/results, error/uncertainty/identity/authorization/provenance/temporal semantics, compatibility policy, status, version, metadata. `AdapterDefinition` records an implementing adapter, protected semantics, external translation, supported port, failure mapping, provenance/identity handling, status, metadata.

`RepositoryPort` gives access only to aggregates or canonical persistence boundaries, not generic table access. `UnitOfWorkDefinition` includes `unit_of_work_id`, owner module, purpose, participating aggregates/canonical objects, transaction and consistency boundaries, commit/rollback conditions, emitted events, conceptual publication expectations, idempotency, failure and audit semantics, status, provenance, metadata.

## 7. Transactions, Consistency, and Recovery

A unit of work aligns with one owned consistency boundary and does not span bounded contexts by default. Cross-context consistency uses explicit contracts, events, governed workflows, compensation, or declared eventual consistency; distributed transactions are never assumed. Shared transaction infrastructure grants no cross-context authority.

Retries respect idempotency and duplicate delivery cannot create duplicate authoritative effects. Cancellation, reversal, and compensation remain distinct. Historical state is not deleted to simulate reversal. `TransactionPolicy`, `IdempotencyPolicy`, and cancellation/revocation policies declare scope, conditions, owner, temporal meaning, failure behavior, and provenance.

## 8. Error, Uncertainty, Identity, Authorization, and Governance

`ApplicationErrorDefinition` declares validation failure, authorization failure, invariant violation, conflict, unavailable dependency, stale projection, uncertain result, rejected command, execution failure, or infrastructure failure. Infrastructure failure never means absence of business reality. Failure propagation preserves the source, uncertainty, retryability, and affected contract.

Authorization is enforced at the target application boundary and again at the domain boundary where required. Upstream claims are verified, not blindly trusted. Identity references resolve through Identity contracts; modules do not create alternate identity systems. Governance policy, delegation, authority, and revocation remain governed by Governance contracts.

## 9. Provenance, Evidence, Time, and Auditability

Application boundaries capture provenance when data, commands, or assertions enter Yarvis. Correlation and causation propagate through use cases and context interactions. `ApplicationTrace` records initiating actor, authority, intent, use case, participating modules, domain transitions, emitted events, execution/evidence/outcome references, failures, start/end, status, provenance, metadata. Technical logs never substitute for governed traces.

Evidence lineage remains linked to its source contracts. Valid-time, transaction-time, recording time, freshness, historical status, and uncertainty remain explicit when material. Auditability requires enough traceability to reconstruct the governed action without turning local logs into canonical truth.

## 10. Read Models, Projections, and Background Work

Read models may combine contexts but remain non-authoritative unless explicitly owned as canonical projections. `ProjectionHandlerDefinition` declares projection owner, source contracts, refresh/freshness/synchronization behavior, uncertainty, retention, and prohibited mutation. Projection refresh must not bypass source contracts.

`BackgroundJobDefinition` declares owning module, purpose, trigger/schedule, required authority, idempotency, traceability, cancellation/revocation, failure/retry behavior, status, provenance, metadata. Scheduled work and long-running processes use the same owner-directed contracts. Human-in-the-loop flows make review, approval, delegation, and escalation explicit.

Mission Control components compose situation projections, apply attention rules, manage work surfaces, and route intervention requests only. Automation components evaluate eligibility, manage sessions/tasks, schedule work, invoke authorized Execution contracts, and track automation state only. Execution components preserve plans, authorization, attempts, evidence, outcome, compensation, reversal, cancellation, and revocation. Decision Intelligence performs no hidden execution; Knowledge creates no decisions; Observation & Evidence promotes no active knowledge outside its contract.

## 11. External Interfaces, Composition, and Operational Boundaries

Inbound interfaces normalize external requests and authentication context into application contracts. Outbound interfaces are ports. External-system adapters and anti-corruption adapters translate vendor models, identifiers, errors, provenance, and temporal meaning without letting vendor semantics enter the Domain unchanged. Configuration selects adapters but does not redefine semantics; secrets remain infrastructure concerns and never enter domain objects. Privacy and observability boundaries must preserve authorization, minimization, traceability, and non-disclosure of governed data.

Operational Domain modules own domain-specific use cases and objects such as merchants, customers, projects, installations, cases, contracts, and service obligations. Platform modules do not absorb that ownership for reuse.

## 12. Module-Level Analysis

| Context module | Principal use-case family / inbound contracts | Outbound ports and dependencies | Boundary, projections, extraction readiness |
| --- | --- | --- | --- |
| Identity | resolve/correct identity; Party/identifier commands | governance, evidence, domain references | canonical identity; identity-reference projections; low |
| Governance | evaluate/grant/revoke/delegate authority | Identity and policy references | authority enforcement; revocation propagation; low |
| Relationship | assert/supersede non-governance relationship | Identity/domain references | temporal relation projection; low |
| Observation & Evidence | acquire/validate/contextualize/evidence handoff | sources, artifacts, Identity/Relationship, Knowledge contract | lineage projections; medium |
| Knowledge | promote/dispute/supersede/expire/retract | Evidence, Identity, Governance references | governed knowledge projections; medium |
| Decision Intelligence | assess/recommend/approve/decide | Knowledge, Governance, Domains, Execution command | Situation projections; medium |
| Execution | plan/authorize/attempt/execute/outcome/compensate | Decision, Governance, Domains, Automation | execution/outcome projections; medium |
| Automation | assess eligibility/session/task/gate | Governance and Execution contracts | automation state projections; medium |
| Mission Control | compose attention/queue/handoff | read contracts from all contexts; owner commands | projected only; medium |
| Operational Domains | domain subject/obligation lifecycle | platform and external boundary contracts | canonical domain projections; context-specific |

## 13. Required Matrices

| Matrix | Governing rule |
| --- | --- |
| Context-to-module | Each of the ten contexts maps to explicit modules and public boundaries. |
| Application dependency | Interface → Application → Domain; Infrastructure implements inward ports. |
| Use-case and command-handler ownership | Owner module accepts transitions over its canonical state. |
| Query-handler responsibility | Answer is canonical/projected/derived/cached/historical/uncertain and side-effect free. |
| Event-handler responsibility | Foreign assertion may drive local work, never foreign mutation. |
| Port-and-adapter | Ports are inward-owned; adapters isolate technology/vendor semantics. |
| Transaction boundary | One owned consistency boundary per unit of work by default. |
| Authorization enforcement | Target module and required domain boundary verify authority. |
| Projection maintenance | Projection has owner, sources, freshness, uncertainty, and no source mutation. |
| Module-extraction readiness | Extraction requires concrete divergence evidence, not fashion. |
| Architectural conformance | Dependency, import, command, query, event, repository, adapter, model-leakage, and authorization rules are tested. |

`ModuleDependencyDefinition`, `ArchitecturalConformanceRule`, and `ContextExtractionAssessment` record respectively dependency direction/contract/prohibited coupling; rule/evidence/result/exception; and extraction drivers, cost, risk, readiness, reviewer, provenance, status.

## 14. Architectural Conformance, AI Boundaries, and Prohibited Patterns

Conformance tests verify module dependency direction, prohibited imports, context access, command/event ownership, query side-effect freedom, repository ownership, adapter isolation, internal-model leakage, and authorization enforcement. Dependency injection preserves inward direction. Shared technical libraries cannot become a mutable shared domain model.

AI may propose services, map use cases, detect layer/domain leakage, transaction risks, ports, adapters, hidden mutations, authorization gaps, overly broad services, and conformance tests. AI may not redefine ownership, move invariants into application services, invent authority, create shared cross-context repositories, make projections authoritative, infer unestablished transaction guarantees, choose technology here, or silently resolve findings. The architecture remains usable without AI.

Prohibited patterns include cross-context repository access; application services owning invariants; domains depending on infrastructure; interfaces containing authoritative rules; foreign mutation by event handlers; Mission Control bypassing commands; Automation bypassing Execution; Decision executing; Knowledge deciding; Observation promoting knowledge directly; duplicated governance/identity; platform absorption of domain state; vendor-model leakage; authoritative projections; background jobs bypassing authorization; in-process contract bypasses; and hidden shared kernels.

## 15. Architecture Findings and Recommendation

| Finding | Severity | Affected module/context | Evidence, control, prior amendment |
| --- | --- | --- | --- |
| APP-001 | NONE | all | Layer and contract rules prevent application services from becoming domain owners. Enforce by conformance tests; no amendment. |
| APP-002 | NONE | Mission Control, Automation, Execution, DI | Explicit owner commands prevent bypass and Decision-to-Execution collapse. Enforce public boundaries; no amendment. |
| APP-003 | MINOR | all projection consumers | Projected reads require freshness/source/uncertainty to avoid false authority. Make required in Query Model; no amendment. |
| APP-004 | MINOR | external adapters, O&E, Domains | External input requires translation, validation, and owner assertion. Make required in Event Catalog; no amendment. |
| APP-005 | MINOR | modular monolith modules | Shared runtime could tempt in-process contract bypass. Enforce import/boundary conformance; no amendment. |

There are **0 BLOCKER**, **0 MAJOR**, and **3 MINOR** findings. The modular-monolith-first recommendation **remains valid with controls**: enforce public module contracts, projection semantics, external-input validation, and architecture conformance.

## 16. Open Questions, Follow-On Artifacts, and Ratification

Open questions are named contract granularity, domain-specific consistency thresholds, projection freshness classes, privacy classifications, and extraction evidence thresholds. They do not alter prior ownership.

The recommended next artifact is a **unified Interaction Contract Catalog** containing named command, event, and query contracts as coordinated views of the same context boundary. `EVENT_CATALOG.md`, `COMMAND_CATALOG.md`, and `QUERY_MODEL.md` may be published as separately navigable sections or documents, but must share one canonical taxonomy, ownership, versioning, correlation, temporal, provenance, and compatibility model. `TECHNICAL_BLUEPRINT.md` follows only after that catalog.

Ratification requires confirmation of layer direction, explicit public module boundaries, owner-directed mutation, unit-of-work boundaries, trace/provenance propagation, and the three MINOR controls. This document does not choose languages, frameworks, ORM, engines, brokers, endpoints, topology, repository layout, package names, schemas, vendors, frontend, CI/CD, or infrastructure products.

## 17. Closing Statement

Yarvis application architecture turns governed context semantics into executable software organization. Composition may be shared inside the modular monolith; canonical ownership, authority, and provenance remain explicit, singular, and traceable.
