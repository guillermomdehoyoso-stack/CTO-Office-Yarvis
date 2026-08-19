# Third and Final Adversarial Review — Canonical Identity Provisioning Foundation Design

**Review date:** 2026-08-19

**Decision:** **Amendment Required**

## Scope and guard

This review assesses only the proposed Foundation design and its first and
second reviews. It applies the requested ratifiability guard: findings below
are limited to security, coherence, auditability, or unequivocal future
implementation. No stylistic preference is a finding. This review grants no
Design Authority, implementation authority, contract allocation, provisioning,
OAuth, Gmail, WhatsApp, data mutation, or external access.

## Final closure matrix

| Earlier finding | Final result | Evidence | Status |
| --- | --- | --- | --- |
| M-001 — cross-aggregate lifecycle, merge, and split | Resolver effects, non-destructive merge/split, quarantine, historical preservation, and no hidden cascade are specified. | §§16.3–16.4. | **Open via T-001** because two proposed Person/Organization state terms are not coherently bounded against current architecture. |
| M-002 — cardinality, normalization, issuer compromise | Exact human-interactive cardinality, `issuer + normalized_subject`, version/provenance, collision precheck, issuer suspension, no destructive reassignment, and human-approved recovery are specified. | §§16.1–16.2. | Closed. |
| M-003 — concurrency/idempotency | Equivalent and conflicting receipts, locking/versioning, restrictive-state precedence, unique final defense, audit, and reconciliation are consistent. | §16.4. | Closed. |
| M-004 — retention/legal hold/privacy | Data classes, future ratified retention, legal-hold fields and precedence, redaction, purpose-bound audited access, and fail-closed conflict treatment are specified. | §16.5. | Closed. |
| M-005 — operability | Safe health, collision/issuer/quarantine/compensation/replay/break-glass/account-takeover/cross-tenant/retention alerts, runbooks, restore, DR, and deterministic criteria are specified. | §16.7. | Closed. |
| N-001 — bootstrap/break-glass | 30-day/day-14 bootstrap, four-hour break-glass, separation of duties, automatic expiry/revocation, and non-bypass constraints are explicit. | §16.6. | Closed. |
| E-001 — Person/Principal cardinality clarity | Current optional persistence is separated from proposed human-interactive cardinality; legacy is fail closed. | §16.1. | Closed. |
| C-001 — Principal lifecycle vocabulary | Principal is now explicitly limited to F-011-compatible `active`/`disabled`; terminal `revoked` remains Membership-only. | §§5 and 16.3; ADR-014. | Closed. |
| C-002 — service Principal non-preclusion | Human-interactive scope is stated and service Principals remain deferred/unimplemented rather than prohibited. | §16.1 and §17. | Closed. |
| N-002 — missing operational alerts | Account-takeover, cross-tenant-denial anomaly, and retention/deletion conflict alerts and runbooks were added. | §16.7. | Closed. |
| E-002 — repeated open decisions | The Email-First variant limits its open policy decisions to issuer, recovery-code expiry/attempts, cooldown, and human recovery authority. | §13. | Closed. |

## Email-First Human Identity Variant verification

| Criterion | Result | Evidence |
| --- | --- | --- |
| Email is access identifier, not primary key or Organization authority | Pass | §17.1 preserves canonical Person/Principal IDs and expressly withholds Organization authority. |
| Mailbox control is not employment, Organization, Membership, or role proof | Pass | §17.1 states the exact limitation. |
| `verified_email` binding is governed | Pass | §17.1 specifies type, normalized subject, internal issuer pending ratification, and receipt-only provenance; §§4 and 16.2 make unknown/pending issuer use fail closed. |
| Email change cannot transfer authority implicitly | Pass | §17.2 requires future authorization, verification, idempotency, audit, prior-binding revocation, and no silent authority transfer. |
| Recovery cannot create Membership or elevate role | Pass | §17.2 prohibits Membership, role, and Organization-authority change. |
| Recovery-code controls | Pass | §17.2 specifies one-time use, hash-only storage, single delivery, rotation invalidation, human separation of duties, cooldown/review, and no exclusive reliance on primary email. §13 retains only expiry, attempts, cooldown, and human recovery authority as policy open items. |
| Gmail/OAuth/intake non-authority | Pass | §17.3 expressly withholds Gmail API, OAuth, mailbox reading, labels, and synchronization; Amendment 014 remains the independent Gmail path. |
| WhatsApp deferred | Pass | §17.3 places it after Gmail and limits reuse to already-ratified patterns. |
| Biometrics/passkeys out of scope | Pass | §13 and §17.3 explicitly defer biometrics, Face ID, WebAuthn, passkeys, and Authenticator Credentials. |

## Global consistency verification

The design remains horizontal and reusable: it carries no Netpay, Energía
Fotónica, Marketing, Gmail, or WhatsApp vertical authority. Semantic contract
families have no IDs and preserve Proposed → Assigned → Authorized →
Implemented sequencing. It remains compatible with F-011's trusted envelope,
tenant isolation, existing active/revoked Membership semantics, and
`AuthorityChanged`. Legacy state is non-authoritative and fail closed.

Idempotency, concurrency, compensation, audit, retention/legal hold, and DR
controls are mutually consistent: no recovery or restore reactivates authority
automatically. The document continues to withhold implementation, provisioning,
catalog allocation, code, migrations, OAuth, Gmail, and external access.

## New finding

| ID | Severity | Evidence | Risk | Required correction | Affected gate |
| --- | --- | --- | --- | --- | --- |
| T-001 | MAJOR | §5 makes `suspended` a proposed Person lifecycle state. §16.3 then treats `Person suspended` and `Organization suspended or revoked` as operating conditions. ADR-014/F-011 ratify Principal `active`/`disabled`, Membership `active`/terminal `revoked`, and Organization activity evaluation, but they do not ratify a Person state machine or Organization `suspended`/`revoked` states. | The proposed resolver cannot be implemented unambiguously without inventing persistent Person/Organization states or applying unspecified external conditions. That risks inconsistent fail-closed behavior and unauthorized lifecycle expansion. | Replace these terms with explicitly defined, non-state authority-evaluation conditions derived from an already-authorized future policy, **or** defer them pending a separate ratified Person/Organization lifecycle decision. The design must state the exact resolver input and fail-closed outcome without adding Person/Organization states in this Foundation slice. Do not alter F-011/ADR-014 through this document. | Design ratification; future architecture/catalog gate. |

## Final count and decision

BLOCKER 0; MAJOR 1; MINOR 0; EDITORIAL 0; OBSERVATION 0.

**Amendment Required.** Apart from T-001, the design has sufficient evidence
for a Design Authority Only ratification package, including the Email-First
Human Identity Variant. The minimum permitted action is to amend only the
proposed design to close T-001, then perform one narrowly scoped confirmation
review. This decision does not authorize catalog allocation, implementation,
provisioning, OAuth, Gmail, WhatsApp, database activity, or role assignment.

## Explicit non-effects

This review changes no reviewed document, code, catalog, contract, migration,
configuration, data, or authority. It does not access PostgreSQL, Docker, SQL,
Gmail, or OAuth; it does not modify or stage
`apps/api/src/yarvis_api/api/authentication.py`; and it creates no commit or
push.
