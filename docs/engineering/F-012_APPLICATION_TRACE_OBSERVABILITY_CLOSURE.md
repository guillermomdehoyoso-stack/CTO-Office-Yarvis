# F-012 — Application Trace Observability Closure

**Status:** Complete — implementation, integral validation, and independent review approved.
**Authority:** Technical Blueprint and its formal review; [F-012 Errors, Traces, Logs, Metrics Design](F-012_ERRORS_TRACES_LOGS_METRICS_DESIGN.md); and [EP-001](EP-001_ENGINEERING_GOVERNANCE_AND_DEVELOPMENT_PRACTICES.md).
**Scope:** Engineering Foundation F-012 Errors, Traces, Logs, Metrics only.
**Non-authorizing:** This closure does not initiate or authorize F-013, F-011, F-016, F-017, F-010, F-014, F-015, C07–C09, workers, queues, schedulers, Query Dispatch, Event Dispatch, Notification Dispatch, or another successor capability.

## 1. Closure Decision

**APPROVED.** F-012 is complete. The increment provides the authorized reusable technical observability primitives: compatible typed application errors, sanitization and structured redacted logging, append-only Application Trace persistence, liveness and readiness, bounded in-memory technical metrics, and the deterministic Intake reference integration.

This decision closes F-012 implementation and its technical validation. It does not close Engineering Foundation, alter the canonical contract baseline, introduce a public trace API, or create authority for a successor work package.

## 2. Implemented Scope

- `TraceReference` is an immutable scalar-only value. Its `reference_type` is required, trimmed, and limited to the closed authorized set; arbitrary mappings, nested values, payloads, state, requests, responses, headers, credentials, content, and oversized fields are rejected as typed validation failures.
- `TraceRecorder.begin()` persists a `started` entry immediately with `sequence = 1` through the independent technical trace session.
- Terminal entries are `succeeded` or `failed` with `sequence = 2`. Invalid terminal references are rejected before terminal append, preserving only the already persisted `started` entry.
- `result_reference`, `retry_reference`, and `compensation_reference` are PostgreSQL `JSONB` values. Valid references support the six named fields—type, identifier, contract ID, contract version, owner context, and relation—with each permitted scalar field accepted at 255 characters without truncation.
- PostgreSQL enforces trace lifecycle invariants: `started` only at sequence 1; terminal entries only at sequence 2 and only after a prior `started`; one entry per trace/sequence; no entries after a terminal; and append-only immutability through UPDATE/DELETE rejection.
- Recursive secret redaction is deep and idempotent, including quoted `Authorization: Bearer` forms, while retaining useful non-secret context.
- Deterministic Intake is the only synchronous reference integration. Its command, idempotency, event, rollback, and Unit of Work semantics remain authoritative; traces are best-effort technical records only.

## 3. Validation Evidence

The final technical checkpoint recorded the following approved evidence:

| Validation | Result |
| --- | --- |
| Final inventory | 470 tests |
| Integral regression | 470 passed; 0 failed; 0 skipped/xfail; 0 omitted |
| F-012 focused tests | 17 passed |
| Alembic round trip | `20260805_30 -> 20260804_29 -> 20260805_30` passed |
| Alembic terminal state | head/current restored to `20260805_30` |
| Docker compile | passed |
| `python -m compileall src` | passed |
| `git diff --check` | passed; LF-to-CRLF warnings only |
| Manual demonstrations | passed |
| Final independent review | **APPROVED** |

The focused F-012 evidence covers closed-type and normalized `TraceReference` validation; immediate started persistence; started/succeeded and started/failed flows; rejection of invalid terminal references without a partial terminal row; JSONB maximum-reference round trip; direct PostgreSQL lifecycle rejection; append-only UPDATE/DELETE protection; recursive secret redaction; denied-by-default inspection; readiness/liveness and metrics; and deterministic Intake replay.

## 4. Migration and Database Evidence

Migration `20260805_30_application_trace_observability` introduces `application_traces`, its JSONB reference columns, indexes, lifecycle checks, unique `(trace_id, sequence)` constraint, transition trigger, and immutability trigger.

The approved PostgreSQL round trip verified that downgrade removed the F-012 table, indexes, triggers, and functions, and that re-upgrade recreated them. At the restored head/current revision `20260805_30`, the database rejects:

- a `started` entry outside sequence 1;
- a terminal entry outside sequence 2;
- a terminal entry without the prior `started` entry for the same trace;
- a second terminal entry or any later entry; and
- UPDATE or DELETE of an existing trace row.

## 5. Scope Audit

F-012 adds no F-013 Foundation-wide conformance controls, worker runtime, queue, scheduler, or deferred dispatch behavior. It adds no Query Dispatch, Event Dispatch, Notification Dispatch, public trace route, authenticated F-011 authority envelope, canonical interaction contract, canonical business state, retention or purge mechanism, or change to Intake business semantics.

Trace persistence uses an independent technical session and does not reuse a Command Unit of Work. A trace-recording failure is observable and does not turn a business success into failure or conceal the original business exception.

## 6. Deferred Work

The following remains deferred and unauthorized:

- F-013 Test and Conformance Foundation;
- F-011 Identity and Authority Envelopes, including authenticated trace-inspection authority;
- F-016 Query Dispatch and all later Foundation work packages;
- workers, queues, schedulers, Event Dispatch, Notification Dispatch, and any post-command dispatch behavior;
- Data Governance retention, disposition, access review, and any trace purge mechanism; and
- any successor implementation without its own governing authorization.

## 7. Findings and Next Governance Decision

The final independent review records no pending findings:

- **BLOCKER:** 0
- **MAJOR:** 0
- **MINOR:** 0
- **EDITORIAL:** 0

No successor is opened by this closure. F-013 is not initiated by, and receives no implementation authorization from, this document. Any future work remains subject to the governing dependency path and a separate authorized engineering gate.
