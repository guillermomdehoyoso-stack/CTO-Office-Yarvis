# F-013 Test and Conformance Foundation Design

**Status:** Implementation authorized — pending implementation and independent review.
**Scope:** Engineering Foundation F-013 only.

## Authority and Boundary

F-013 implements the Foundation conformance controls required by the Technical
Blueprint §6 and §9, the Architectural Decision Trace
`ADT-APPLICATION-001`, `ADT-OWNERSHIP-001`, `ADT-CONTRACT-001`, and
`ADT-TRACE-001`, and the F-013 position in the ratified Foundation completion
path. It follows F-012 because its controls require the typed error and trace
vocabulary already provided by F-012.

The package is a test and conformance foundation. It does not create an
interaction contract, domain model, persistence model, migration, public route,
or runtime dispatch capability. It does not implement F-011 identity or target
authorization, F-016 Query Dispatch, F-017 Event or Notification Dispatch,
workers, queues, schedulers, CI, or a Foundation demonstration.

## Purpose and Observable Result

F-013 makes the active Foundation composition auditable through deterministic,
repository-local conformance tests. The observable result is a focused suite
that rejects drift in the four controls it owns:

1. explicit module and contract registry composition;
2. architectural import and ownership boundaries;
3. F-012 technical-observability boundaries; and
4. absence of later runtime capability in the Foundation composition.

The controls run with the normal backend test suite and use the existing Ruff
and Pyright authority for the architecture-test surface. F-013 does not expand
quality-tool scope over legacy or F-012 runtime files, because that would turn
this conformance increment into unrelated remediation.

## Canonical Inputs and Debt Assessment

The canonical contract projection is the ratified 55-member Runtime Baseline
V1. `FOUNDATION-DEBT-001` is closed by the accepted F-006/F-013 reconciliation;
there is no remaining ambiguity in the projection count, membership, owner, or
metadata used by this package. F-013 therefore neither changes
`canonical_contracts.py` nor reopens historic Tier-1 totals.

The package consumes the existing explicit `ModuleRegistry`, `ContractRegistry`,
canonical module projection, canonical contract projection, F-009 dispatcher,
and F-012 trace recorder. It creates no alternative registry, contract ID, or
binding path.

## Controls and Invariants

### Registry and ownership

- The canonical module and contract projections remain explicit declarations;
  registries are per-application and sealed.
- Every canonical contract owner remains a registered canonical module.
- Contract lifecycle and operational status remain independent registry metadata.
- The conformance suite does not infer ownership from a database table, route,
  import path, or adapter.

### Dependency and import boundaries

- Domain models do not import FastAPI, bootstrap composition, persistence
  infrastructure, process environment, or application state.
- The dispatch package remains transport-independent and contains no ambient
  execution tracking, automatic discovery, legacy database dependency, worker,
  queue, scheduler, Query Dispatch, Event Dispatch, or Notification Dispatch
  runtime.
- F-012 observability is a technical dependency: it does not import FastAPI,
  bootstrap composition, the command dispatcher, or application services.

### Trace conformance

- Trace references remain typed, scalar-only values under F-012; F-013 verifies
  their closed reference vocabulary is not bypassed by a parallel trace model.
- The Intake reference integration remains synchronous and writes traces through
  `TraceRecorder`; it does not acquire a worker, queue, or post-command dispatch
  path.
- Conformance tests inspect source structure and public composition only; they
  do not make trace persistence a business transaction or alter F-012 semantics.

## Actors, Authority, and Errors

The actor is the engineering validation process. No external caller, identity,
organization, authorization decision, or public error contract is introduced.
Failures are pytest assertions that identify the violated repository invariant;
they are not runtime application errors.

## Determinism and Persistence

The conformance suite uses explicit source paths, AST inspection, and existing
in-memory registry projections. It creates no business data or persistent
state, has no idempotency or concurrency behavior, and requires no migration.
Input order is explicit wherever a registry projection is inspected.

## Implementation Slices

| Slice | Files | Control | Focused evidence | Risk controlled |
| --- | --- | --- | --- | --- |
| C1 | `tests/architecture/test_foundation_conformance.py` | explicit registry, ownership, baseline and lifecycle/status controls | architecture/conformance suite | hidden registry or owner drift |
| C2 | same suite | AST import and composition prohibition rules | architecture/conformance suite | layer leakage and ambient runtime state |
| C3 | same suite | F-012 observability boundary and existing architecture-test quality authority | architecture/conformance suite plus Ruff/Pyright | trace or quality-control bypass |
| C4 | focused test updates only if required | Intake remains synchronous; no later dispatch/runtime appears | architecture/conformance suite | premature F-011/F-016/F-017/worker scope |

## Acceptance Criteria

F-013 is acceptable only when:

1. all Foundation conformance controls run in the ordinary backend test suite;
2. registry, owner, import, trace-boundary, and deferred-runtime rules above
   are represented by focused deterministic tests;
3. the F-013 architecture-conformance suite is covered by the configured Ruff
   and Pyright scopes;
4. no migration, database state, runtime route, contract, worker, queue, or
   dispatch capability is added; and
5. focused validation, one final full regression, compilation, and
   `git diff --check` pass before closure.

## Deferred Work

F-011 remains the owner of authenticated identity and target authorization.
F-016 remains the owner of Query Dispatch. F-017 remains the owner of Event and
Notification Dispatch. F-010 remains the owner of workers and schedulers, and
F-014 remains the owner of CI. F-013 supplies conformance evidence only and
does not authorize any of those capabilities.
