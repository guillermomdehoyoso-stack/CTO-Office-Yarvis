# Current Sprint

## Identity

**Current work package:** Netpay Operational Radar — executive-priority manual operational vertical.
**Current authorization:** F-011 Identity and Authority Envelopes Slices A–I
under active IG-006 as clarified by Amendment 002. F-011 is In Progress;
F-016 and F-017 remain unstarted. E–G are limited to the existing Radar
identity/authority migration and require their mapping and preflight gates.

**Work package:** F-013 — Test and Conformance Foundation (closed)
**Authorization:** Technical Blueprint, Architectural Decision Trace, F-013 design, and EP-001.

## Goal

The active goal is the usable, synchronous and workspace-scoped Netpay Radar:
merchant registration, manual pasted-text requests, checklists, PENDIENTE ON/OFF,
filters and append-only operational history. See
[Netpay Operational Radar](../engineering/NETPAY_OPERATIONAL_RADAR.md).

Deliver deterministic Foundation conformance controls for explicit registry
ownership, architectural import boundaries, F-012 observability isolation, and
the synchronous Intake reference integration without adding runtime capability.

## Closure status

F-013 is closed: implementation, final validation, and focused review are
approved. This is not a Foundation closure and does not initiate or authorize
F-011, F-016, or successors. The closure evidence is recorded in
[F-013 Test and Conformance Foundation Closure](../engineering/F-013_TEST_AND_CONFORMANCE_FOUNDATION_CLOSURE.md).

## Completed scope

- Deterministic tests for canonical registry ownership and sealed composition.
- Architectural import controls for F-012 observability isolation.
- Synchronous Intake trace integration controls that reject deferred runtime
  dependencies.
- Quality-authority coverage verification for the architecture-conformance
  suite.

## Validation evidence

- Inventory: 475 tests; integral result: 475 passed, 0 failed, 0 skipped,
  0 xfail, and 0 omitted.
- F-013 focused conformance suite: 5 passed; affected architecture, registry,
  canonical-contract, and F-012 suites: 51 passed.
- Ruff and Pyright on the F-013 suite passed; Pyright reported 0 errors and
  0 warnings.
- Docker API build, `python -m compileall src`, Alembic head/current
  `20260805_30`, and `git diff --check` passed; the latter reported LF-to-CRLF
  warnings only.

## Explicitly deferred

F-016, F-017, F-010, F-014, F-015, C07–C09, workers,
queues, Event Dispatch, Notification Dispatch, Data Governance retention, and
all new business capabilities remain unauthorized. IG-006 authorizes no new
Radar capability, only the existing Radar authority migration bounded by
Amendment 002.

## Next package

No successor package is initiated. F-011 is In Progress for Slices A–I under
IG-006 and Amendment 002. E–G require approved real mappings and preflight
before backfill or cutover; H and I retain their sequential evidence gates.
Amendment 003 remains a
dependency-graph correction only and does not independently authorize F-016.
