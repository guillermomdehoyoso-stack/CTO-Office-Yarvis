# Second Adversarial Review — Canonical Identity Provisioning Foundation Design

**Review date:** 2026-08-18

**Decision:** **Amendment Required**

## Scope and basis

This review assesses only the proposed Foundation design and its first review.
It contrasts their terminology and proposed semantics with the ratified F-011
and ADR-014 boundaries. It creates no authority: no contract, catalog change,
issuer, subject, Person, Principal, Identity Binding, Membership, role,
implementation, provisioning, OAuth, Gmail, database action, or runtime gate.

## Closure matrix

| Prior finding | Result | Evidence | Status |
| --- | --- | --- |
| M-001 — cross-aggregate lifecycle and merge/split | The resolver-effect matrix, non-destructive behavior, Person merge, and Person split controls are present. | Design §16.3. | **Open via C-001:** its conditions use states not represented consistently in the state machines and introduce a Principal `revoked` term incompatible with current F-011 state vocabulary. |
| M-002 — binding cardinality, normalization, issuer compromise | Exact Person/Principal/Binding cardinalities, canonical `issuer + normalized_subject`, version capture, collision precheck, issuer suspension, and human-approved recovery are present. | §§16.1–16.2. | Closed, subject to C-002 scope clarification. |
| M-003 — concurrency and race behavior | Same-key replay/conflict, distinct-key collision, locks/versioning, restrictive-state precedence, unique final defense, receipts, correlation, and reconciliation are specified. | §16.4. | Closed. |
| M-004 — retention, legal hold, privacy/access | Data classes, future ratified retention, legal-hold fields, redaction, purpose-bound audited access, and fail-closed deletion conflict are specified. | §16.5. | Closed. |
| M-005 — operability and testable acceptance | Allowlisted health, required runbooks, workflow/replay/restore/DR behavior, and deterministic criteria are specified. | §16.7. | **Open via N-002:** three alert conditions previously required by the first review are absent. |
| N-001 — bootstrap/break-glass bounds | Thirty-day/day-14 bootstrap and four-hour/one-business-day break-glass constraints, no self-approval, automatic expiry/revocation, and no bypass are explicit. | §16.6. | Closed. |
| E-001 — Person/Principal clarity | Exact productive cardinality and current-model/legacy distinction are explicit. | §16.1. | **Open via C-002:** “productive Principal” is undefined against F-011's requirement not to preclude service principals. |

## Integral verification

| Area | Result | Evidence |
| --- | --- | --- |
| Cardinality and legacy fail-closed | Pass, subject to C-002 | §16.1 provides all requested Person/Principal/Binding cardinalities and legacy handling. |
| Normalization and issuer compromise | Pass | §16.2 makes normalization issuer-specific, deterministic, versioned and auditable, and makes issuer compromise non-dispatchable without destructive reassignment. |
| Cross-aggregate effects | Partial | §16.3 clearly separates immediate resolver blocking from later audited transition, preserves terminal Membership revocation, history, quarantine, and tenant isolation; C-001 remains. |
| Concurrency and idempotency | Pass | §16.4 is internally consistent: receipt replay, conflict, locking/versioning, restrictive precedence, audit, and reconciliation align. |
| Retention and privacy | Pass | §16.5 separates data classes, governs holds, retains historic explanation safely, requires redaction and purpose-bound audit, and declines to invent a duration. |
| Bootstrap and break-glass | Pass | §16.6 meets the required bounds and preserves tenant isolation, audit, provenance, and fail-closed controls. |
| Operability and recovery | Partial | §16.7 supplies safe health, six required alerts, runbooks, receipt/workflow recovery, restore revalidation, DR non-reactivation, and measurable criteria; N-002 remains. |
| Horizontal architecture and governance | Partial | The design remains vertical-neutral, semantic-contract-only, and preserves review → ratification → catalog → gate → implementation; C-002 needs compatibility clarification. |
| Current authority boundary | Pass | §§2, 11, 15, and 16 withhold implementation, catalog IDs, provisioning, OAuth, Gmail, and authority. |

## New contradiction and completeness findings

| ID | Severity | Evidence | Impact | Exact correction | Affected gate |
| --- | --- | --- | --- | --- | --- |
| C-001 | MAJOR | §5 models Person only as `candidate`, `verified-profile`, `linked`, or `rejected`, and Principal only as `pending`, `active`, `disabled`, or `quarantined`. §16.3 nonetheless makes `Person suspended` and `Principal ... revoked` operative conditions. ADR-014 ratifies Principal as `active`/`disabled`, while terminal `revoked` belongs to Membership. | The lifecycle is not deterministic: a future resolver cannot know whether Person suspension or Principal revocation is a state, an alias, or a pending workflow condition. Reusing `revoked` for Principal risks contradicting the accepted F-011 ownership/state model. | Amend §5 and §16.3 with one consistent proposed state/effect vocabulary. Preserve ratified Principal `active`/`disabled` and Membership `active`/terminal `revoked`; either define a prospective Person suspension state and its permitted transitions, or express it as a governed Person lifecycle condition. Do not introduce Principal `revoked` as a state without separate ratified architectural change. | Design ratification; later catalog and implementation gates. |
| C-002 | MAJOR | §16.1 says each “productive Principal” belongs to exactly one Person, but does not define productive. ADR-014 says the identifier model must not preclude service principals, while service principals remain deferred. | A literal reading could make any future productive non-human/service Principal invalid, silently narrowing a ratified extensibility requirement. | Define the cardinality rule as applying to human-interactive Principals in this Foundation slice, and state the service-Principal category remains deferred and unimplemented; or provide a future explicit non-human Principal policy that preserves the ADR-014 non-preclusion requirement. Keep no service Principal creation authority. | Design ratification; future architecture/catalog gate. |
| N-002 | MINOR | §16.7 alerts collision, issuer suspension, quarantine/stuck workflow, compensation/audit failure, repeated replay, and break-glass. The first review's M-005 correction also required account-takeover signal, cross-tenant denial anomaly, and retention-conflict alert coverage; none is named. | The design's otherwise strong operational controls leave three known abuse/failure conditions without a required detection and runbook path. | Add those three controlled alert conditions with conceptual severity/destination and future runbook action, using safe non-PII telemetry only. | Design ratification; future security/operability gate. |
| E-002 | EDITORIAL | §13 still lists Person linkage, multiple active bindings, normalization versioning, break-glass duration, and workflow retention as open decisions, although §16.1, §16.2, §16.5, and §16.6 have resolved or bounded them and §16 says it prevails. | The explicit precedence avoids a semantic conflict, but a ratification reader can mistake settled controls for undecided design. | Remove or recast those items as residual decisions only (for example, proof classes and steward assignment), retaining §16 as the authoritative proposed rule. | Design ratification. |

## Threat and authority check

Account takeover is contained by binding/issuer suspension, but N-002 requires
alert coverage. Replay, collision, cross-tenant binding, compensation, and
reconciliation controls are coherent. Issuer compromise and normalization drift
are now fail closed. Insider-abuse controls are materially strengthened by
separation of duties and bounded break-glass. No condition authorizes present
implementation or bypasses tenant isolation, audit, closed-role validation, or
F-011's trusted-envelope/`AuthorityChanged` boundary.

## Severity count and decision

BLOCKER 0; MAJOR 2; MINOR 1; EDITORIAL 1; OBSERVATION 0.

**Amendment Required.** The prior M-002, M-003, M-004, and N-001 corrections
are closed; M-001, M-005, and E-001 need the bounded corrections above before
the design is ratifiable. The next minimum permitted action is to amend only
the proposed design, followed by another independent documentary review. No
catalog allocation, implementation, provisioning, OAuth, Gmail, database
access, or role assignment is permitted.

## Explicit non-effects

This review changes no existing document, code, contract, catalog, migration,
configuration, data, or authority. It does not access PostgreSQL, Docker, SQL,
Gmail, or OAuth; it does not modify or stage
`apps/api/src/yarvis_api/api/authentication.py`; and it creates no commit or
push.
