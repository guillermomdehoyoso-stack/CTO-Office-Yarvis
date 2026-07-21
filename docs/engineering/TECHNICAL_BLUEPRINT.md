# YARVIS
# Technical Blueprint

## Status: Draft for Engineering Review

## 1. Purpose, Authority, Scope, and Non-Goals

This blueprint defines how the first executable Yarvis implementation will be constructed so E-001 Engineering Foundation can begin and E-002 Inbox First can be prepared without reopening ratified semantics.

It is subordinate to the Constitution, conceptual and operational architecture, Platform Engineering, Application Architecture, Interaction Contract Baseline v1.0, and Architectural Decision Trace. It selects mechanisms only; it does not alter domain semantics, ownership, authority, contracts, lifecycle, time, provenance, evidence, or human-control requirements.

**Governing question:** How will ratified Yarvis architecture be implemented as a secure, observable, testable, evolvable modular application capable of the first Netpay Inbox First slice?

Non-goals: microservices, Kubernetes, service mesh, distributed broker, multiple databases by default, universal event sourcing, vector database, autonomous-agent framework, generic operational-domain model, sophisticated frontend, cloud lock-in, or a change to ratified artifacts.

## 2. Repository Inspection Summary and Existing Baseline

The current repository contains `apps/api` (Python 3.12 FastAPI, SQLAlchemy, Alembic, psycopg, pytest), `apps/web` (React 18, Vite 6, TypeScript, TanStack Query, Vitest), Docker Compose with PostgreSQL 16, `.env.example`, migrations, backend/frontend tests, and existing operational modules/routes. No CI configuration, worker framework, scheduler framework, static type checker, linter, formatter configuration, or engineering index was found. The existing API is a valuable implementation baseline but is not authority over the ratified module boundaries; migration to the target structure must be incremental and non-destructive.

## 3. Technology Decision Method and Selected Stack

Decisions favor the existing stack, one-machine/small-server operation, E-001/E-002 needs, modular-monolith boundaries, and reversible replacement.

| Decision | Selection | Rationale / constraints preserved | Exit strategy |
| --- | --- | --- | --- |
| Language/runtime | Python 3.12 | existing API runtime; typed, mature, Codex-friendly | preserve ports/contracts for later runtime replacement |
| Application framework | FastAPI | existing API, validation, async interface support | framework confined to Interface/Infrastructure |
| Schema validation | Pydantic supplied by FastAPI | existing compatible contract binding | bindings remain derived from registry |
| Database | PostgreSQL 16 | existing Compose, transactions, JSON metadata, durable jobs/projections | one canonical relational store initially |
| Persistence mapping | SQLAlchemy 2.0 | existing mapping baseline | repositories own aggregates, not ORM models |
| Migration | Alembic | existing versioned migrations | migration files reflect persistence only |
| API protocol | JSON over HTTP | existing FastAPI boundary and minimum operator interface | endpoint is not canonical contract |
| Background work | PostgreSQL-backed durable job table plus separate Python worker process | no broker; durable, traceable, one-machine operation | replace worker adapter without changing contracts |
| Scheduler | dedicated worker loop with database-backed schedules | avoids a second scheduling technology; trigger is never authority | scheduler adapter may change later |
| Documents | local filesystem object store under configured root; PostgreSQL metadata/reference/fingerprint only | existing document repository and confidential-data control | object-storage adapter through inward port |
| Authentication | local development principal adapter; signed production identity provider is Open before production | separates authentication from identity/authorization | production adapter behind inbound port |
| Authorization | Governance/target-boundary policy adapter, initially explicit application policy service | preserves target verification | replace policy source without changing envelopes |
| Testing | pytest/httpx; Vitest/Testing Library | existing suites | contract/architecture suites added |
| Static quality | Ruff + Pyright; Prettier/ESLint for web | fast, deterministic gates | config only after E-001 work package |
| Observability | structured JSON logs, persisted ApplicationTrace, health/readiness, metrics endpoint, trace IDs | no vendor lock-in; critical-contract trace requirement | telemetry adapter later |
| Containers/CI | Docker Compose; GitHub Actions | existing local topology; no CI presently | CI is portable workflow |

## 4. Part I — Runtime Blueprint

### Application bootstrap, process model, configuration, and lifecycle

One API bootstrap composes registered modules; one worker bootstrap processes durable jobs and schedules. Required configuration is parsed and validated at startup; invalid required configuration fails startup safely. Shutdown stops intake, marks worker claim release/finish behavior, and preserves traceable work state.

Environment profiles: local, test, production. `.env.example` remains local-only. Configuration selects adapters, never domain semantics. Secrets are injected by environment/secret store adapters, redacted from logs, and never enter domain objects.

### Module registry, dependency injection, and dispatch

Each of the ten contexts has a registered module or documented placeholder: Identity, Governance, Relationship, Observation & Evidence, Knowledge, Decision Intelligence, Execution, Automation, Mission Control, and Netpay Merchant Operations. Interface → Application → Domain; Infrastructure implements inward-defined ports. Dependency injection occurs only in composition roots. No module imports another context’s Domain internals.

Commands resolve by stable contract ID/version to exactly one owner handler. Queries resolve to handlers declaring canonical/projected/derived/cached/historical/uncertain classification and freshness. Events are persisted owner assertions and consumed idempotently by local handlers. Notifications are non-authoritative delivery requests and are never promoted to Event truth.

### Background work, scheduling, retries, cancellation, and human control

The worker consumes durable jobs with contract ID/version, correlation/causation, initiating principal, authority summary, retry policy, result/failure, and trace reference. A worker claims one eligible job through a PostgreSQL row lock with skip-locked semantics and a bounded lease; expired leases become explicitly retryable and retain their prior trace. The scheduler persists schedules and creates jobs only; its trigger grants no authority. Mutating work revalidates authorization where required. Retries use idempotency keys. Cancellation, compensation, and reversal are distinct governed commands. Human confirmation gates remain enforced by owner application flow before high-impact work.

## 5. Part II — Persistence and Information Blueprint

| Information class | Initial persistence | Authority rule |
| --- | --- | --- |
| Canonical state | PostgreSQL context-owned tables/repositories | table never defines ownership; module does |
| Contract/event record | append-only PostgreSQL records with contract ID/version | owner assertion only |
| Execution evidence / audit / trace | append-only records linked by correlation | technical success is not business outcome |
| Projection | PostgreSQL read model with source/checkpoint/generated_at/freshness/staleness/uncertainty/unavailable | never canonical truth |
| Document/binary | configured filesystem object; DB metadata/fingerprint/reference | inbound artifact, not canonical claim |
| Provenance/temporal metadata | relational metadata and references | valid time, record time, source, confidence retained |
| Ephemeral work | durable job state with bounded retention | not a domain authority |

Repositories are inward-owned ports, context-scoped, and aggregate/canonical-boundary specific. A Unit of Work covers one owning context and local transaction. Cross-context workflows use durable owner events, projections, and compensation; no hidden distributed transaction. Event publication uses a transactional outbox record in the same local transaction as the owner transition, then idempotent worker dispatch. Duplicate event/job delivery is tolerated by contract idempotency.

Migrations remain Alembic. Each migration is additive/forward-compatible where possible, reversible only when safe, and tested against empty and upgrade paths. Backups use PostgreSQL logical backup plus document-store backup with restore verification; deletion/retention is governed by policy and preserves required audit/provenance history.

External material enters only as Source Artifact/Observation with source, fingerprint, provenance, confidence, valid/record time, and validation state. It cannot mutate Netpay or other canonical state before validation and owner command assertion.

## 6. Part III — Engineering Blueprint

### Executable target repository structure

```text
apps/api/
  src/yarvis_api/
    bootstrap/                 # composition, module registry, configuration
    shared/{contracts,tracing,errors,security,ports}/
    contexts/
      identity/{domain,application,interface,infrastructure}/
      governance/{domain,application,interface,infrastructure}/
      relationship/{domain,application,interface,infrastructure}/
      observation_evidence/{domain,application,interface,infrastructure}/
      knowledge/{domain,application,interface,infrastructure}/
      decision_intelligence/{domain,application,interface,infrastructure}/
      execution/{domain,application,interface,infrastructure}/
      automation/{domain,application,interface,infrastructure}/
      mission_control/{domain,application,interface,infrastructure}/
      netpay_merchant_operations/{domain,application,interface,infrastructure}/
    infrastructure/{persistence,worker,scheduler,documents,telemetry}/
    main.py
  migrations/ tests/{unit,application,integration,architecture,e2e}/
apps/web/                       # retained; minimum operator UI/API client
docs/{architecture,engineering}/
docker-compose.yml .env.example
```

Existing `models`, `schemas`, `services`, `api/routes`, and `storage` are retained during incremental relocation behind context public boundaries; no mass rename is part of E-001. Existing migrations remain. E-001 adds bootstrap/shared/context shells, contract registry, worker/scheduler adapters, conformance tests, and CI files; full context relocation is deferred to slice implementation.

### Contract binding, errors, identity, authorization, security, and privacy

The canonical registry is machine-readable metadata maintained once and loaded at bootstrap. Binding adapters map registry IDs/versions to command, query, event, and notification handlers. Registry validation detects duplicate IDs, owner/version/lifecycle/status violations, missing consumer/use-case/trace rules, and binding drift. API/file/message forms are derived serializers only.

The Identity Envelope carries authenticated principal, canonical identity reference when resolved, ambiguity, source, correlation, and provenance. The Authorization Envelope carries requested/represented principal, target context, authority source/scope/constraints/effective interval/delegation/revocation verification. Target modules verify authorization; connectivity, authentication, syntax, and external IDs are insufficient.

Errors are typed: validation, authorization, invariant, conflict, unavailable dependency, stale projection, uncertain result, rejected command, execution, and infrastructure. Responses disclose only permitted information. Privacy classification is carried by contracts; logs/traces redact secrets and sensitive payloads.

### Observability and test/conformance

Critical-contract traces record actor/context, authorization decision, contract ID/version/owner, correlation/causation, canonical object, start/end/failure, result/events, provenance/evidence, retries and compensation. Logs are structured; metrics cover health, readiness, queue, handler latency/failure/retry, projection freshness, and contract conformance. ApplicationTrace is inspectable through authorized interface.

| Control | Static | Unit | Integration/runtime | Operational/human |
| --- | --- | --- | --- | --- |
| layer/context imports and repository ownership | yes | — | — | review gate |
| owner command/event/query/notification semantics | — | yes | yes | contract audit |
| external input/owner assertion | — | yes | yes | provenance review |
| projection integrity | — | yes | yes | freshness monitoring |
| lifecycle/status independence | yes | yes | registry load | release review |
| critical traces | — | yes | end-to-end | trace inspection |
| Netpay Inbox First reconstruction | — | — | yes | controlled demonstration |

Unit tests cover pure domains and policies; application tests cover handlers/UoW; contract tests cover registry/bindings/compatibility; integration tests cover PostgreSQL/adapters/workers; architecture tests enforce dependency and ownership rules; E2E tests cover vertical slices. Fixtures are synthetic/anonymized. Quality gates: Ruff, Pyright, pytest, web type/test/build, migration-upgrade test, architecture conformance, and contract registry validation.

## 7. Part IV — Delivery Blueprint

Local development uses Docker Compose API, PostgreSQL, web, and an added worker process after E-001. Test uses isolated PostgreSQL database and temporary document root. Initial production is one server/small deployment running API, worker, PostgreSQL, document volume, backups, and restricted ingress; no microservices or broker. CI runs backend/frontend quality gates, migrations, registry/conformance tests, and image/build validation. Releases use forward-compatible migration, health/readiness gate, rollback to prior executable version only when database compatibility permits, and runbooks for migration failure, job retry, projection rebuild, document restore, and trace investigation.

## 8. Architecture-to-Control and Runtime Matrices

| Decision Trace | Concrete neutral control | Implementation evidence |
| --- | --- | --- |
| ADT-OWNERSHIP-001 / ADT-APPLICATION-001 | context module boundaries and prohibited-import test | architecture suite |
| ADT-EVIDENCE-001 | artifact→Observation→validation→owner command gate | intake lineage test |
| ADT-DATA-001 / ADT-EXECUTION-001 | local UoW + transactional outbox + idempotent consumer | transaction/retry test |
| ADT-PROJECTION-001 | projection integrity fields | projection freshness test |
| ADT-CONTRACT-001 | registry/binding validation | registry conformance |
| ADT-TRACE-001 | ApplicationTrace and critical trace fields | E2E trace reconstruction |
| ADT-MISSION-001 | read projection + public owner command | no-mutation test |
| ADT-NETPAY-001 | owner-directed vertical chain | controlled slice demo |

## 9. E-001 Engineering Foundation Work Packages and Backlog

| WP / backlog | Objective and expected files | Dependencies | Size / parallel / blocking | Acceptance |
| --- | --- | --- | --- | --- |
| F-001 Repository normalization | baseline maps, `pyproject`/quality config only if adopted | none | S / yes / yes | no destructive relocation; baseline test works |
| F-002 Runtime/dependency baseline | bootstrap, shared primitives | F-001 | M / no / yes | inward dependency rule executable |
| F-003 Configuration | config profiles/secrets validation | F-002 | S / yes / yes | invalid required config fails safely |
| F-004 Application bootstrap | API/worker bootstrap and shutdown | F-002,F-003 | M / no / yes | app starts and stops safely |
| F-005 Module registry | context shells/registration | F-004 | M / yes / yes | ≥2 modules register with boundaries |
| F-006 Contract registry | shared contract metadata/bindings | F-005 | M / no / yes | Tier 1 ID/version/lifecycle/status validation |
| F-007 Database/migrations | database port, Alembic verification | F-003 | M / yes / yes | connection and upgrade verification |
| F-008 Unit of Work | context-local transaction/outbox primitive | F-007 | M / no / yes | no cross-context repository transaction |
| F-009 Command/query/event/notification dispatch | owner bindings and non-authority notification | F-006,F-008 | L / no / yes | test command/event/query/notification chain |
| F-010 Worker/scheduler | durable jobs, worker loop, schedule trigger | F-007,F-009 | M / yes / no | one safe background/scheduled job trace |
| F-011 Identity/authority envelopes | inbound principal and target verification | F-006,F-009 | M / yes / yes | unauthorized command rejected |
| F-012 Errors/traces/logs/metrics | typed errors, trace, health/readiness | F-004,F-009 | M / yes / yes | critical trace inspectable |
| F-013 Test/conformance foundation | test structure, import/ownership/registry rules | F-002,F-006 | M / yes / yes | all conformance controls run |
| F-014 Local environment/CI | Compose worker, CI quality gate | F-004,F-007,F-013 | M / yes / no | repeatable local/CI gate |
| F-015 Foundation demonstration | narrow non-business contract demonstration | F-009–F-014 | M / no / yes | all 15 required demonstration steps pass |

**E-001 backlog count: 15 implementation-ready items.** Critical path: F-001 → F-002 → F-004 → F-005 → F-006 → F-008 → F-009 → F-012/F-013 → F-015. Parallel work: F-003, F-007, F-010, F-011, F-014 after their dependencies. E-001 acceptance is the required foundation demonstration: start app; valid config; database/migration; two modules; registry; command/event/query/notification; worker/schedule; correlation/trace retrieval; conformance; health/readiness.

## 10. Initial Vertical Slice Strategy and Inbox First Readiness

Initial operator interface: **authenticated JSON API with generated FastAPI documentation**. It is the fastest safe interface because it reuses the existing repository, supports controlled demonstrations, and does not create a UI authority path. A minimal React operator surface is added only when VS-004 needs human attention use; no sophisticated frontend is required.

| Slice | Objective / contracts | Contexts | Done / deferred |
| --- | --- | --- | --- |
| VS-001 Manual Intake to Governed Observation | manual message/document; Evidence CMD-001–002/EVT-001 | O&E | provenance/fingerprint/trace demonstrated; external mailbox deferred |
| VS-002 Observation to Netpay Case Candidate | validated intake, identity/relationship/merchant/case candidate | O&E, Identity, Relationship, Netpay | ambiguity represented; automatic merge deferred |
| VS-003 Netpay Case to Pending Action | checklist/missing docs/pending-action/assignee/activity | Netpay, Execution, Governance | owner state/action trace; automation deferred |
| VS-004 Pending Action to Mission Control | attention projection/freshness/acknowledgement | Execution, Mission | no source mutation; sophisticated dashboard deferred |
| VS-005 Human Action to Traceable Outcome | completion/cancel/escalate/case update/notification | Execution, Netpay, Mission | end-to-end trace; external delivery provider deferred |

All slices traverse interface, application, domain, persistence, trace, contract, and test layers. Pending-action state is initially authoritative in **Execution**, as ratified; Netpay owns the case/checklist condition that requests the action, not its execution lifecycle. The first five slices prepare E-002 through E-005; E-006–E-008 remain unimplemented.

## 11. Risks, Findings, Open Decisions, Review, and Follow-On Work

| Finding | Severity | Evidence / resolution | Blocks E-001 | Ratified amendment |
| --- | --- | --- | --- | --- |
| TB-001 | MINOR | current repository predates target context structure; incremental adapters/shells avoid destructive rewrite | no | no |
| TB-002 | MINOR | production authentication provider not in repository; use local adapter for E-001, choose production provider before production | no | no |
| TB-003 | MINOR | existing worker/scheduler absent; DB-backed worker loop is minimum selected mechanism | no | no |
| TB-004 | NONE | no CI exists; F-014 creates quality gate | no | no |

Open decisions: production identity-provider selection (owner: Security Steward; gate: before production; not E-001 blocker); retention durations (Data Governance Steward; gate: before production); exact telemetry backend (Observability Steward; gate: before production); document storage replacement threshold (Infrastructure Steward; gate: capacity/security review). None block E-001.

Engineering review passes when BLOCKER=0, MAJOR=0, stack and structure are coherent, Tier 1 binding strategy and four carried controls are concrete, E-001 packages/demonstration and VS-001–005 are executable in principle, and no code was modified. The next action is Engineering Review and ratification of this blueprint, then start F-001.

## 12. Closing Statement

This blueprint makes the architecture executable without allowing mechanisms to redefine it: modules preserve ownership, contracts govern interactions, persistence preserves history, projections expose uncertainty, and the first Netpay Inbox First work remains traceable from source to outcome.
