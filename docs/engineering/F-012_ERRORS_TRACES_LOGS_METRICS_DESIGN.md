# F-012 Errors, Traces, Logs, Metrics Design

**Status:** Implemented — Pending Independent Review
**Scope:** Engineering Foundation F-012 only

## Authority and boundary

F-012 implements the reusable technical primitives authorized by the Technical
Blueprint sections 4, 6, and 9; its formal review; Roadmap Amendments 001 and
002; and EP-001. It does not implement F-013 conformance, F-011 identity and
authority envelopes, F-016 Query Dispatch, event or notification dispatch,
workers, queues, or a public trace API.

The Runtime Baseline remains 55 contracts. The Tier-1 catalog remains 116
identities, of which 61 are outside that baseline. This increment neither
changes `canonical_contracts.py` nor creates a canonical interaction contract.

## Errors and HTTP translation

`ApplicationErrorCode` retains compatibility codes and adds the required
categories: invariant violation, stale projection, uncertain result, rejected
command, execution failure, and infrastructure failure. Central HTTP
translation maps typed failures to stable statuses and sanitizes public
messages and details. Dependency, execution, infrastructure, transient, and
internal failures use a generic public message. SQL, stack traces, credentials,
sensitive headers, full payloads, and internal dependency diagnostics are not
exposed.

## Critical trace

`ApplicationTrace` stores append-only technical trace entries:

```text
started -> succeeded
        -> failed
```

Each entry records contract ID/version/owner/context, actor and organization
reference when available, correlation and causation, authorization decision,
sanitized object/result/event/evidence/provenance references, and optional
retry or compensation references. It deliberately does not store canonical
business state or complete input payloads.

The trace adapter owns an independent technical session. It does not reuse a
Command Unit of Work and therefore cannot change command commit, rollback,
idempotency, or event semantics. A trace persistence failure is counted and
emitted through sanitized structured logging, but does not turn a business
success into a failure. If both business execution and trace persistence fail,
the original business exception is preserved.

Migration `20260805_30` provides the table, constraints, indexes, and a
PostgreSQL trigger that rejects UPDATE and DELETE. The repository only appends;
inspection is read-only.

## Inspection and authority

`TraceInspectionService` accepts an injected `TraceInspectionAuthorizer` and
can retrieve by trace ID or correlation ID. Bootstrap composes a deny-all
authorizer. There is no public route or canonical contract. F-011 is the later
owner of authenticated Identity/Authorization Envelope integration and target
authority decisions.

## Logging, health, readiness, and metrics

Structured observability events pass through recursive redaction. The bounded
in-memory `ObservabilityMetrics` snapshot is an internal test/inspection
mechanism; it deliberately has no actor, organization, object, payload, or
secret labels. It provides counters, duration aggregates, and gauges. Queue and
retry metrics are extension points only; no corresponding runtime exists here.

Text redaction and reference validation are separate controls. Redaction uses
explicit case-insensitive patterns for password/passwd/pwd, token variants,
Authorization Bearer/Basic values, API keys, secrets, and cookies with `:` or
`=` separators, including repeated values in one message. Trace references are
immutable scalar-only `TraceReference` values with at most six named fields:
type, identifier, contract ID/version, owner context, and relation. Arbitrary
mappings, nested values, payloads, state, requests, responses, headers,
credentials, content, and oversized fields are rejected as typed validation
failures rather than retained in masked form. Reference collections contain
only these values, are normalized to immutable tuples, preserve input order, and
are capped by `MAX_TRACE_REFERENCES = 32` per event, evidence, or provenance
collection. Duration metrics retain constant-size count, total, minimum,
and maximum aggregates rather than an unbounded sample list.

`/health` is process liveness only. `/ready` additionally requires an active
lifecycle, sealed module/contract/handler registries, a non-disposed persistence
runtime, and `SELECT 1` PostgreSQL connectivity. An unavailable dependency
returns sanitized HTTP 503.

## Reference integration and verification

Deterministic Intake is the vertical reference integration. Its existing
idempotency, events, rollback, and Unit of Work behavior remain authoritative;
the service writes only sanitized started/terminal technical trace entries.
This is not a claim of universal adoption. F-013 may later define broader
conformance controls.

Validation covers typed/public errors, recursive redaction, started/succeeded
and started/failed traces, independent trace-persistence failure, PostgreSQL
append-only protection, allowed and denied inspection, liveness/readiness,
metrics snapshots, Intake replay, migration upgrade/downgrade/re-upgrade, and
affected bootstrap, dispatcher, Unit of Work, authentication, registry, and
repository-structure regressions.

## Retention restriction

Append-only storage is not an authorization for indefinite retention. F-012
implements neither purge nor a definitive retention policy. Data Governance
must authorize retention, disposition, access review, and any future purge
mechanism before production use.

## Deferred work

F-011 supplies authenticated authority decisions for trace inspection. F-013
may extend conformance validation. F-016 and successors remain out of scope.
No worker, queue, scheduler, event-dispatch, notification-dispatch, or query
dispatch behavior is introduced by F-012.
