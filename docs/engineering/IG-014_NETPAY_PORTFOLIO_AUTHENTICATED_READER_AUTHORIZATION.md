# IG-014 — Netpay Portfolio Authenticated Reader Authorization

## Status

**RATIFIED — IMPLEMENTATION AUTHORITY; OPERATIONAL TRANSITION NOT EXECUTED**

**Date:** 2026-10-22
**Roadmap authority:** [Amendment 027](IMPLEMENTATION_ROADMAP_AMENDMENT_027.md)
**Contract authority:** [F-011 Governance Contract Amendment 002](F-011_GOVERNANCE_CONTRACT_AMENDMENT_002.md)

Implement the exact composite role and `IC-GOVERNANCE-CMD-010`, including an
explicit expected-role compare, row lock, Organization isolation, idempotent
receipt, compatible `AuthorityChanged` event and transactional invalidation of
the target's active sessions. Revision `20261022_54` may extend only the closed
command-type check and must descend directly from `20261021_53`.

Conformance must prove exact capabilities; Inbox preservation; Master and
Portfolio reads; denial of Master mutation, sensitive and reconciliation
access; equivalent replay; incompatible-key conflict; expected-role conflict;
real concurrent requests; foreign-Organization concealment; revoked-Membership
denial; self-escalation denial; one receipt/event; and session invalidation.
Migration upgrade, downgrade before any receipt, and re-upgrade run only on a
synthetic disposable PostgreSQL database. Static checks and affected contract
validation apply.

Applying the command to the local operational Membership is a later checkpoint.
It requires an independently authenticated, active same-Organization actor with
both existing Governance Membership capabilities. The current Inbox operator
is not presumed to have that authority. No table edit or authentication bypass
is permitted.

## Current conformance result

Implementation conformance is **PASS** on 2026-10-22 under the synthetic,
isolated procedure recorded in
[`netpay-portfolio-authenticated-reader-ig014-conformance-20261022.txt`](evidence/netpay-portfolio-authenticated-reader-ig014-conformance-20261022.txt).
The operational transition is **BLOCKED**: read-only inventory found only the
target `netpay_inbox_operator` Membership and no distinct actor with both
required Governance capabilities. This does not weaken the implementation PASS
or authorize direct table editing, bootstrap reuse or self-escalation.

The 2026-10-23 continuation also verified that the target Principal has no OIDC
binding and cannot start a productive session. Existing founder/local
provisioning cannot solve this gate: both admit only
`netpay_operations_operator`, which exceeds the approved scope and lacks the
Governance capabilities required by CMD-010. They remain disabled. The bounded
implementation remains technically conformant; operational use requires a
separately authorized identity-binding and least-privilege administrative
bootstrap extension plus a real, distinct OIDC identity.
