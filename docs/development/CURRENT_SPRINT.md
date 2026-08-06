# Current Sprint

## Identity

**Work package:** F-012 — Errors, Traces, Logs, Metrics (closed)
**Authorization:** Technical Blueprint, its formal review, Roadmap Amendments 001 and 002, and EP-001.

## Goal

Deliver the reusable technical observability primitives required by F-012 without
implementing Query Dispatch, identity/authority envelopes, worker runtimes, or
later Foundation capabilities.

## Closure status

F-012 is closed: implementation, integral validation, and independent review
are approved. This is not a Foundation closure and does not initiate or
authorize F-013, F-011, F-016, or successors. The closure evidence is recorded
in [F-012 Application Trace Observability Closure](../engineering/F-012_APPLICATION_TRACE_OBSERVABILITY_CLOSURE.md).

## Completed scope

- Compatible typed application errors and sanitized HTTP translation.
- Append-only technical trace persistence with independent sessions and
  deny-by-default inspection.
- Structured redacted logging, process liveness, dependency readiness, and
  in-memory technical metrics.
- Deterministic Intake as the reference vertical integration.

## Validation evidence

- Inventory: 470 tests; integral result: 470 passed, 0 failed, 0 skipped/xfail,
  and 0 omitted.
- F-012 focused tests: 17 passed.
- Alembic round trip `20260805_30 -> 20260804_29 -> 20260805_30` passed and
  head/current was restored to `20260805_30`.
- Docker compile, `python -m compileall src`, and `git diff --check` passed;
  the latter reported LF-to-CRLF warnings only.
- Manual demonstrations and final independent review: **APPROVED**.

## Explicitly deferred

F-013, F-011, F-016, F-017, F-010, F-014, F-015, C07–C09, workers,
queues, Event Dispatch, Notification Dispatch, Data Governance retention, and
all business capabilities remain unauthorized.

## Next package

No successor package is initiated. Any future package requires its own
authorized engineering gate. Amendment 003 remains a dependency-graph
correction only and does not independently authorize F-016.
