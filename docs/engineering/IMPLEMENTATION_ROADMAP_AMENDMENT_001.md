# YARVIS
# Implementation Roadmap Amendment 001

## Status

**Proposed for Engineering Review**

This amendment is not yet ratified. It does not replace the current Engineering
Roadmap or Technical Blueprint until it is ratified through the applicable
engineering-review process.

## 1. Purpose and Scope

The original Engineering Foundation roadmap remains architecturally valid. This
amendment synchronizes its implementation plan with repository evidence through
the completion of F-009 Command Dispatch. It clarifies the remaining work needed
to close E-001 Engineering Foundation and establishes planning controls for
future operational-domain extensions.

Engineering Foundation now has a stable kernel: repository normalization,
runtime and dependency controls, configuration, application bootstrap, module
and contract registries, persistence runtime, Unit of Work, and synchronous
owner Command Dispatch are established. F-009 was deliberately implemented as
synchronous owner Command Dispatch. Query, Event, and Notification runtime
capabilities remain separate work.

This amendment does not reopen F-009, alter architecture, change bounded-context
ownership, or reinterpret contract authority. It refines implementation
sequencing, package scope, dependencies, exit criteria, and documentary
governance only.

## 2. Authority and Documentary Control

Roadmap governance follows this hierarchy:

```text
Ratified Architecture
        |
Technical Blueprint
        |
Implementation Epics
        |
Ratified Roadmap Amendments
        |
Consolidated Roadmap Baseline
        |
Work-Package Designs and Baselines
        |
Implementation and Post-Implementation Evidence
```

The Constitution and ratified architecture remain the highest authorities.
Interaction Contract authority, the Architectural Decision Trace, the Technical
Blueprint and its ratified review, and ratified component baselines remain
binding on this amendment.

Roadmap amendments are append-only planning corrections. Earlier documents
remain historical evidence; they are neither erased nor silently reinterpreted.
A consolidated roadmap baseline may be created only after ratification. Future
operational domains require an explicit epic or domain-extension amendment
before implementation. They may reuse platform patterns, but must not reuse
another domain's canonical model by default.

## 3. Implementation Evidence Reviewed

This assessment reviewed observable repository evidence rather than relying only
on planned wording:

- the current source package structure under `apps/api/src/yarvis_api`;
- the application composition root and typed application state;
- explicit module and contract registries;
- PostgreSQL-oriented persistence runtime and migration baseline;
- context-local Unit of Work implementation;
- the `dispatch` package, Command envelope, handler registry, and dispatcher;
- architecture and focused foundation tests;
- Ruff and Pyright quality configuration;
- Docker Compose API and PostgreSQL runtime definitions; and
- Git history through `7d341bc Engineering Foundation: establish command dispatch`.

The evidence shows an executable Foundation kernel. It does not show a Query
runtime, durable Event runtime, Notification delivery runtime, worker,
scheduler, Foundation-wide trace implementation, or CI quality gate. Those
capabilities remain planned.

## 4. Engineering Foundation Status

| Work package | Original purpose | Current status | Evidence | Remaining gap | Blocks E-001 completion |
| --- | --- | --- | --- | --- | --- |
| F-001 Repository normalization | establish repository and quality baseline | Completed | `79fd8b8`; canonical package and quality configuration | none within F-001 | no |
| F-002 Runtime/dependency baseline | establish executable runtime authority | Completed | `1cd5167`; Python and dependency authorities | none within F-002 | no |
| F-003 Configuration | typed validated configuration | Completed | `2732918`; `config.py` and configuration tests | production policy decisions remain outside F-003 | no |
| F-004 Application bootstrap | isolated application composition and lifecycle | Completed | `9f16576`; `bootstrap.py`, typed state, health route | worker bootstrap is later work | no |
| F-005 Module registry | explicit application-module registration | Completed | `269ca80` and canonical module composition baseline | future context modules remain deferred | no |
| F-006 Contract registry | canonical contract metadata and validation | Completed | `7da6607`; sealed registry and canonical projection | runtime bindings beyond Commands remain planned | no |
| F-007 Persistence infrastructure | per-application runtime and migration baseline | Completed | `7d0b8a8`; PostgreSQL runtime, Alembic, tests | repositories are domain work | no |
| F-008 Unit of Work | local transactional boundary | Completed | `101fbeb`; `OperationScope` and `UnitOfWork` | transactional outbox use is later Event work | no |
| F-009 Dispatch | owner interaction execution | Completed | `7d341bc`; Command envelope, handler registry, dispatcher, tests | Command Dispatch only; no Query, Event, or Notification runtime | no |
| F-010 Worker/scheduler | durable jobs and scheduled triggers | Pending | no worker or scheduler implementation evidence | job model, execution loop, and schedule trigger | yes |
| F-011 Identity/authority envelopes | principal and target authorization | Pending | no envelope or target-authorization implementation evidence | identity and authorization envelopes and target checks | yes |
| F-012 Errors/traces/logs/metrics | typed operational diagnostics | Pending | current health route and local exceptions are insufficient | typed errors, structured logs, critical traces, readiness, metrics | yes |
| F-013 Test/conformance foundation | Foundation-wide conformance controls | Partially Completed | architecture tests, focused tests, Ruff, Pyright, pytest | complete Foundation controls for ownership, contracts, traces, and new runtimes | yes |
| F-014 Local environment/CI | repeatable delivery and quality gates | Partially Completed | local Docker Compose API/PostgreSQL readiness | CI gate, reproducible worker validation, release gate | yes |
| F-015 Foundation demonstration | integrated non-business proof | Pending | no complete Foundation demonstration evidence | all F-010 through F-014 exit evidence | yes |

## 5. F-009 Scope Clarification

F-009 owns the following implemented Foundation capability:

- synchronous `CommandEnvelope` handling;
- explicit Command Handler Registry;
- owner-handler resolution;
- context-local Unit of Work use;
- committed-only Command completion;
- explicit rollback semantics;
- payload isolation;
- dependency-direction enforcement;
- bootstrap integration; and
- the Dispatch error hierarchy.

F-009 does not own Query Dispatch, durable Event Dispatch, event consumption,
transactional outbox processing, Notification Dispatch, worker execution,
scheduler execution, authorization-policy semantics, or full observability.

This is a scope clarification, not a defect and not a reopening of the ratified
Dispatch baseline. Commands express a mutation request to the owning context;
their transaction mechanics remain owned by the Unit of Work. Dispatch does not
become a universal interaction bus.

## 6. New Work Packages

### F-016 - Query Dispatch

**Purpose:** Establish query routing and query-result semantics independently
from mutating Command Dispatch.

**Planning scope:** `QueryEnvelope`; stable query contract identity and version;
explicit handler registration; exactly one valid handler resolution; result
classification as canonical, projected, derived, cached, historical, or
uncertain; freshness and staleness metadata where applicable; unavailable and
uncertain states; no mutation authority; no implicit reuse of Command Unit of
Work; bootstrap integration; and architecture/conformance tests.

**Dependencies:** F-006 Contract Registry; reusable F-009 composition patterns
without semantic coupling; F-012 trace/error primitives; and F-013 conformance
foundation.

**Acceptance criteria:** duplicate or missing query handlers are rejected;
results expose required classification metadata; projected results expose
freshness and uncertainty; query execution cannot mutate canonical state; no
cross-context repository access is introduced; and failures are typed and
traceable.

No implementation design is defined by this amendment.

### F-017 - Event and Notification Foundations

**Purpose:** Establish durable owner Events and non-authoritative Notification
delivery foundations without conflating either with Commands or business
outcomes.

**Event planning scope:** owner assertion; stable contract ID and version;
correlation and causation; durable event record; transactional-outbox
compatibility; idempotent consumption; retry and failure evidence; no
distributed transaction; and no direct foreign-context mutation.

**Notification planning scope:** Notification as a delivery request;
provider-neutral delivery port; delivery state distinct from business completion;
correlation with the originating Command or Event; retry and failure visibility;
and no canonical-domain authority.

**Dependencies:** F-006 Contract Registry; F-008 Unit of Work; F-009 Command
Dispatch; F-012 observability; F-013 conformance; and F-011 authority envelopes
where a follow-up action mutates state.

**Acceptance criteria:** Event and Notification semantics remain distinct; Event
persistence is compatible with the local owner transaction; duplicate delivery
cannot duplicate effects; Notification delivery success does not complete a case
or action; failures and retries are reconstructable; and no cross-context
transaction is introduced.

No detailed implementation design is defined by this amendment.

## 7. Revised Foundation Completion Sequence

The recommended sequence is:

```text
F-012 Errors, Traces, Logs, and Metrics
        |
F-013 Test and Conformance Foundation
        |
F-011 Identity and Authority Envelopes
        |
F-016 Query Dispatch
        |
F-017 Event and Notification Foundations
        |
F-010 Worker and Scheduler
        |
F-014 Local Environment and CI
        |
F-015 Foundation Demonstration
```

F-012 precedes new runtimes because later behavior must be observable. F-013
follows, and may overlap with the latter part of F-012, because conformance must
encode observable, ownership, and dependency rules. F-011 precedes operational
commands because authenticated identity is insufficient without target
authorization. F-016 remains separate from Commands because read semantics,
freshness, and uncertainty are distinct from mutation semantics.

F-017 precedes worker completion because durable Event and Notification work
defines background execution obligations. F-010 materializes durable jobs and
schedules only after Event, authority, trace, and conformance rules are explicit.
F-014 can prepare CI controls after F-013, but cannot complete until the required
runtime gates are known. F-015 is the formal integrated exit demonstration.

Valid parallelism is limited and controlled: F-013 can overlap F-012 after its
minimum typed error and trace vocabulary exists; F-014 CI preparation can overlap
F-011 through F-017 but its exit follows F-010; and F-011 design may begin during
F-013, while implementation waits for the required observable/conformance base.

## 8. Revised E-001 Exit Criteria

E-001 completes only when all of the following exist and pass:

- safe startup and shutdown;
- validated configuration;
- module registration;
- contract registration;
- PostgreSQL and migrations;
- context-local Unit of Work;
- Command Dispatch;
- Query Dispatch;
- Event foundation;
- Notification foundation;
- Identity and Authorization Envelopes;
- typed errors;
- structured logs;
- persisted or inspectable critical traces;
- health and readiness;
- Foundation conformance tests;
- durable worker execution;
- schedule-triggered job creation;
- CI quality gates; and
- a complete non-business Foundation Demonstration.

**E-001 Core Kernel may be considered complete after F-009.** E-001 Engineering
Foundation is not formally complete until F-015 passes.

## 9. E-002 Inbox First Clarification

E-002 is a minimum end-to-end integration vertical slice, not the full
implementation of E-003, E-004, or E-005. It may implement only the minimum
required capabilities across Observation and Evidence, Identity, Relationship,
Governance, Netpay Merchant Operations, Execution, and Mission Control.

The five slices remain:

- VS-001 Manual Intake to Governed Observation;
- VS-002 Observation to Netpay Case Candidate;
- VS-003 Netpay Case to Pending Action;
- VS-004 Pending Action to Mission Control; and
- VS-005 Human Action to Traceable Outcome.

Later epics deepen their bounded contexts without changing ownership proven by
this vertical slice. Execution owns the pending-action lifecycle. Netpay owns
merchant, case, checklist, and the condition requesting work. Mission Control is
projection-only. Notification delivery is not completion. External input is not
canonical truth before validation and owner assertion.

## 10. Domain Extension Governance

Before adding an Operational Domain Context, a Domain Extension Review is
required. It must answer:

1. What canonical state does the new domain own?
2. What existing platform contracts does it consume?
3. What new contracts does it own?
4. What concepts are genuinely shared rather than merely similar?
5. What cross-domain projections are non-authoritative?
6. What evidence and provenance rules apply?
7. What authority and human-control rules apply?
8. What migration or compatibility impact exists?
9. What vertical slice proves the domain independently?
10. Does the proposal improperly generalize a Netpay or Energy Fotónica model?

Platform capabilities may be reused; domain models are not shared by default.
Cross-domain work occurs through contracts, Events, and projections. A new domain
requires a roadmap amendment or new epic before implementation. Domain
registration does not automatically grant authority or persistence access.

## 11. Updated Dependency Graph

```text
E-001 Core Kernel (F-001 through F-009 complete)
 |
 +-- F-012 Errors, Traces, Logs, and Metrics
 |     +-- F-013 Test and Conformance Foundation
 |           +-- F-011 Identity and Authority Envelopes
 |           |     +-- F-016 Query Dispatch
 |           |     +-- F-017 Event and Notification Foundations
 |           |           +-- F-010 Worker and Scheduler
 |           +-- F-014 Local Environment and CI
 +------------------------------+----------------------+
                                        |
                                     F-015 Foundation Demonstration
                                        |
                              E-002 Inbox First Vertical Slice
                                        |
                 +----------------------+----------------------+
                 |                      |                      |
       E-003 Mission Control   E-004 Execution Engine   E-005 Netpay Merchant Operations
                 +----------------------+----------------------+
                                        |
                     First operational Netpay vertical jointly complete
                                        |
                       +----------------+----------------+
                       |                                 |
                 E-006 Automation              E-007 Knowledge and Intelligence
                       |
                 E-008 Energy Fotónica Operations
                 (platform-pattern reuse; no Netpay canonical-model reuse)
```

E-003, E-004, and E-005 jointly complete the first operational Netpay vertical.
E-008 consumes proven platform capabilities and governed contracts; it does not
inherit Netpay merchant, case, checklist, or other canonical state.

## 12. Risks and Controls

| Risk | Impact | Trigger | Control | Required evidence |
| --- | --- | --- | --- | --- |
| Roadmap drift | work proceeds against stale sequencing | package starts without status review | ratified amendment and consolidated baseline | review record and baseline |
| Semantic drift | implementation redefines ratified meaning | technical design changes contract semantics | architecture and contract review gate | conformance review |
| Hidden shared kernel | domain ownership erodes | reuse proposal shares domain state | Domain Extension Review | explicit owner and boundary record |
| Dispatch becomes a universal bus | transaction and authority leakage | reuse of Command Dispatch for Query/Event/Notification | separate F-016 and F-017 packages | runtime and architecture tests |
| Ownership leakage | foreign context mutates owner state | direct repository or transaction access | public-contract and UoW controls | ownership tests |
| Premature infrastructure | irreversible mechanism before semantics | worker or broker introduced before Event rules | F-017 before F-010 | design and conformance evidence |
| False Foundation completion | operational work begins without required controls | F-009 treated as full F-009 original scope | Core Kernel versus E-001 distinction | F-015 demonstration |
| CI/documentation divergence | local claims are not repeatable | quality process is manual only | F-014 CI gate and baseline updates | CI run evidence |
| Domain-model generalization | Netpay or Energy leaks into another domain | similar terms treated as shared concepts | extension review and contract boundary | domain review |
| Projection becomes operational truth | UI or read model mutates source state | projection action bypasses owner Command | projection-only and public-command controls | integration and trace tests |

## 13. Ratification Criteria

This amendment may be ratified only if:

- BLOCKER findings equal zero;
- MAJOR findings equal zero;
- no ratified semantics change;
- no ownership changes;
- F-009 remains closed;
- F-016 and F-017 remain planning packages only;
- E-001 exit remains at least as strict as the Technical Blueprint;
- E-002 remains an owner-directed vertical slice;
- domain-extension governance does not create a shared business model;
- all dependencies are coherent; and
- no implementation code was modified.

## 14. Proposed Follow-On Actions

1. Engineering Review of this amendment.
2. Correct only accepted findings.
3. Ratify the amendment.
4. Create `docs/engineering/IMPLEMENTATION_ROADMAP_BASELINE.md`.
5. Begin F-012 Design.
6. Review and ratify F-012.
7. Implement F-012.
8. Perform post-implementation audit.
9. Commit after all required gates pass.

F-012 implementation must not begin as part of this amendment.

## 15. Closing Statement

This amendment restores a single governed execution path from the completed
kernel to Foundation closure and then to Inbox First. It preserves the ratified
model while adding reviewable documentary controls for safe future domain
expansion.
