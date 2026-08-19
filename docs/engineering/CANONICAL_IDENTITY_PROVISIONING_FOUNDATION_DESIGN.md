# Canonical Identity Provisioning Foundation Design

**Status:** Proposed — design only; pending independent review and human ratification

**Date:** 2026-08-18

## 1. Problem, scope, and ownership

This prospective Core Foundation design defines the reusable, governed chain
`Person → Principal → Identity Binding → Membership`. It addresses the Partial
Path found by the Netpay MVP-2D1 discovery: the repository has bounded
Membership authority behavior, but no complete canonical Person-to-Principal
or external-identity binding lifecycle.

The design is horizontal Core work, not a Netpay, Energía Fotónica, Marketing,
Gmail, inbox, or other vertical capability. It separates a human/business
profile (Person), a durable internal authorization subject (Principal), a
verified external credential association (Identity Binding), and Organization
authority (Membership). One Principal can hold Memberships in multiple
Organizations; no membership, selector, or vertical metadata establishes human
identity.

| Concept | Proposed owner and responsibility | Non-responsibility |
| --- | --- | --- |
| Person | Identity profile with minimized human/business data. | Credential, authentication proof, role, or tenant authority. |
| Principal | Stable internal authorization subject and lifecycle. | External token/secret or Organization privilege. |
| Identity Binding | Verified Principal-to-`issuer + subject` association. | Inference from email, name, headers, or unverified claims. |
| Issuer Registry | Governed issuer allowlist, namespace, normalization, and proof policy. | Credential storage or provider runtime. |
| Membership | Principal-to-Organization role, lifecycle, and revocation. | Proof of external identity. |
| Role/authority | Closed server-controlled permission policy. | Client-declared authority or self-assignment. |

## 2. Non-goals and present non-authority

This document authorizes no implementation, real provisioning, OAuth, Gmail,
migration, canonical-contract allocation, role assignment, database access,
configuration, secret, credential store, provider integration, PostgreSQL,
Docker, SQL, code, or test. It resolves no existing Person, Principal,
Membership, issuer, subject, or Organization retrospectively.

It does not make generic `POST /people` a canonical provisioning route and does
not promote the local/test Netpay utility to a production path. Every operation,
event, authority class, state, and contract name below is **Proposed**, not
**Assigned**, **Authorized**, or **Implemented**.

## 3. Sources and current compatibility boundary

Sources are the canonical provisioning discovery and its two reviews; F-011
architecture, implementation design, Governance Contract Amendment and IG-006;
ADR-014; Amendment 014 and its reviews; and existing models, handlers, catalog,
migrations, tests, and pertinent Git history as read-only evidence.

Existing persistence has a globally unique `principals.external_subject` with
no issuer field, optional `Principal.person_id`, and one role per
Principal/Organization Membership. Existing Membership activation/revocation
uses an organization-scoped receipt and `AuthorityChanged`; that bounded path
does not create a canonical Principal or Identity Binding lifecycle.

Amendment 014 remains Gmail design authority only and grants no provisioning,
catalog, role, implementation, OAuth, or Gmail authority.

## 4. Proposed model and invariants

An Identity Binding is the canonical external identity association between an
active Principal and a normalized, verified `issuer + subject` pair. The
composite pair is the uniqueness boundary. Its safe provenance records enough
evidence to establish the association, never raw provider credentials or tokens.

An Idempotency Receipt stores authorized request scope, normalized-intent
fingerprint, authority basis, correlation metadata, outcome, and durable result
reference. A Provisioning Workflow stores durable review, execution,
quarantine, compensation, and completion state. Neither creates authority.

The mandatory invariants are:

1. Active Identity Binding is unique within canonical `issuer + subject`.
2. Unknown, disabled, ambiguous, or nonconforming issuers fail closed.
3. Email, name, headers, mailbox values, token strings, and unvalidated claims
   never create, resolve, or bind identity.
4. No Membership is active before Principal, binding provenance, Organization,
   closed role, workflow, and approval are complete and verified.
5. Every authority evaluation re-resolves active persistent Principal,
   Membership, Organization, and server-derived permissions.
6. Tenant isolation applies to mutation, query, receipt, workflow, audit, and
   recovery; foreign resources are concealed where the authority boundary needs it.
7. Membership revocation is terminal. Binding change is immutable history or an
   auditable replacement, never an implicit reassignment.
8. Collision, unknown issuer, invalid normalization, partial chain,
   conflicting replay, foreign target, or insufficient evidence fails closed.
9. No actor self-assigns a role or approves its own privileged request.

## 5. Lifecycle state machines

```text
Person:              lifecycle deferred — no Person state machine in this design
Principal:           pending → active → disabled
                           └→ quarantined
Identity Binding:    proposed → verification_pending → active → suspended → revoked
                                      └→ rejected       └→ rotation_pending → replaced
Membership:          requested → pending_verification → active → revoked
                                         └→ rejected | quarantined
Workflow:            requested → evidence_pending → approved → applying → completed
                                  └→ quarantined ← failed → compensating → compensated
```

Person is not a credential. The authoritative Person lifecycle and any effects
of Person lifecycle on authority are deferred to a separate decision; this
design creates no new Person state. Until that future ratification, Person does
not trigger an implicit cascade to Principal, Identity Binding, or Membership.
Effective authority continues to depend on the ratified Principal and
Membership states plus the existing Organization activity evaluation.
Only a complete, reviewed workflow moves a Principal to active. Principal uses
the F-011-compatible `active`/`disabled` lifecycle; it has no `revoked` state.
Only active binding resolves identity. Rebinding/rotation needs stronger
authority, fresh provenance, independent review, and immutable
predecessor/successor history. `revoked` Membership is terminal; a future return
is a new reviewed request. `quarantined` is non-authoritative and blocks
progress until deterministic reconciliation or authorized compensation.

## 6. Proposed operations

| Operation | Actor / preconditions | Receipt and effects | Audit / failure / recovery |
| --- | --- | --- | --- |
| Create/Resolve Person | Authorized Identity requestor; independent approver for privileged use; evidence policy met. | Key + fingerprint; creates only a non-authoritative candidate or resolves a verified record. | Request/evidence/outcome audit. Ambiguity, weak evidence, conflict, or replay mismatch rejects or quarantines; never activates a Principal. |
| Provision Principal | Identity executor after independent approval; verified Person rule where required; approved workflow. | Receipt creates pending Principal only. | Requested/completed/failed audit. Partial state remains pending/quarantined and is recovered only by workflow, never direct deletion. |
| Bind External Identity | Binding executor; allowed issuer, normalized verified subject, nonconflicting Principal, approved proof. | Receipt plus composite uniqueness; binding verifies before activation. | Proposed/verified/activated/rejected audit. Unknown issuer, collision, provenance failure, or conflict rejects; no fallback inference. |
| Create/Activate Membership | Governance executor and independent approver; active Principal/binding/Organization; closed valid role. | Organization-scoped receipt; requested/pending then active. | Request/approval/activation audit and compatible future `AuthorityChanged`. Incomplete chain, unknown role, foreign tenant, or missing authority fails closed. |
| Revoke Membership | Authorized Governance revoker; same Organization target; receipt. | Terminal replay-safe revocation. | Compatible `AuthorityChanged`, reason category, actor. Foreign target concealed; no implicit reactivation. |
| Rebind/Rotate Identity | Two-person Identity approval, or separately governed break-glass. | Dedicated receipt preserves predecessor/successor history. | Rotation request/proof/decision audit. Ambiguity suspends/quarantines; subject is never silently moved. |
| Reconcile/Compensate Failed Provisioning | Recovery executor plus independent reviewer; failed/quarantined workflow and approved plan. | Deterministic resume or governed compensation receipt. | Start/outcome/compensation/review audit. Unknown state or evidence stays quarantined; no direct SQL cleanup. |
| Query Provisioning Status | Authorized scoped requester/reviewer with trusted envelope. | Read-only; no receipt unless separately required. | Safe access audit. No PII, raw subject, token, or evidence payload; foreign status concealed. |

These semantic operations assign no endpoint, handler, ID, event ID, role,
permission, schema, or implementation mandate.

## 7. Authority, bootstrap, and break-glass

| Activity | Request | Approve | Execute | Review / revoke |
| --- | --- | --- | --- | --- |
| Person/Principal workflow | Identity requestor | Independent Identity approver | Controlled Identity executor | Identity reviewer / authority |
| Issuer admission or normalization | Issuer policy steward | Independent architecture/governance authority | Future policy deployment only | Security/privacy reviewer / policy authority |
| Binding/rebind | Identity requestor | Independent binding approver | Controlled Identity executor | Identity/security reviewer / authority |
| Membership and role | Governance requestor | Independent Governance approver | Governance executor | Organization/Governance reviewer / revoker |
| Break-glass | Designated emergency requestor | Separate emergency approver where available | Restricted executor | Mandatory independent review / authority |

Bootstrap is temporary, scope-limited, receipt-bound, independently reviewed,
and automatically expires. It is revoked on expiry, compromise, issuer-policy
loss, Organization-control change, or availability of separation-of-duties
review. It cannot bypass provenance, tenant isolation, closed-role validation,
receipt, audit, or later review. No bootstrap or break-glass is created or
enabled by this design.

## 8. Atomicity, idempotency, compensation, and reconciliation

Future local writes require one bounded transaction that persists the intended
state transition, receipt, and safe audit/event outbox together. A request key
is scoped to actor, authority boundary, operation, and Organization/workflow;
an equivalent replay returns its durable outcome while conflicting key reuse
fails closed.

For approval or provider-verification steps outside one transaction, the durable
workflow is the recovery boundary. It records auditable checkpoints and allows
only deterministic resume, quarantine, or governed compensation. A Membership
cannot activate before the whole chain verifies. Cleanup and revocation are
future authorized commands, never direct deletion. This is a design requirement,
not authority to implement transactions, receipts, events, compensation, or
cleanup.

## 9. Security and privacy

Future work must minimize Person data, separate profile from authentication
proof, redact issuer/subject in ordinary logs, and exclude raw provider
artifacts, headers, tokens, credentials, free text, and unnecessary PII from
health and audit projections.

| Threat | Required future control |
| --- | --- |
| Spoofing | Governed issuer policy and verified provenance; no weak-attribute inference. |
| Collision/impersonation | `issuer + subject` uniqueness, normalization, immutable/audited binding, fail closed. |
| Replay | Scoped key, canonical fingerprint, durable receipt, deterministic replay. |
| Privilege escalation | Closed roles, independent approval, no self-assignment, full-chain activation. |
| Confused deputy | Trusted evaluated envelope, authority basis, target Organization ownership check. |
| Cross-tenant binding | Tenant-scoped operations/receipts/events and foreign-target concealment. |
| Partial provisioning | Transactional boundary, workflow, quarantine, compensation, reconciliation. |

## 10. Compatibility and legacy evidence

Legacy `external_subject` without issuer is evidence only, not canonical binding
proof. Until a separately authorized migration and provenance verification,
ambiguous or nonconforming legacy state fails closed for new binding and
privileged lifecycle use. This document does not deactivate, mutate, or
reinterpret existing records.

Future governance may assess, without selecting or executing one option:

1. a separate binding representation with progressive legacy verification;
2. a canonical issuer namespace with a bounded compatibility projection; or
3. retirement of legacy resolution after authorized migration evidence.

Any option needs ratified data design, catalog allocation, implementation gate,
migration/rollback plan, testing, and historical compatibility review. Existing
active/revoked Membership semantics and `AuthorityChanged` remain constraints;
no future design may silently reactivate Membership or alter tenant ownership.

## 11. Proposed contract families and observability

| Semantic family | Purpose | Current state |
| --- | --- | --- |
| Identity provisioning command | Person/Principal lifecycle request and approval | Proposed |
| Identity binding command | Bind, suspend, revoke, rebind, rotate issuer/subject | Proposed |
| Governance membership command | Request, approve, activate, revoke closed-role Membership | Proposed |
| Provisioning status query | Tenant-scoped safe workflow state | Proposed |
| Binding lifecycle event | Safe binding/provenance state change | Proposed |
| Workflow lifecycle event | Start, success, failure, quarantine, compensation, review | Proposed |
| Authority change event | Existing Membership fact remains compatible with F-011 authority only | Assigned/ratified profile where existing authority says so |

State labels are normative for this proposal: **Proposed** means no allocation;
**Assigned** means separate catalog allocation; **Authorized** means a bounded
implementation gate; **Implemented** means validated runtime evidence. No state
implies a later state.

Future lifecycle records carry correlation ID, accountable actor, authority
basis, receipt, timestamps, causation, and controlled outcome. Health/status is
tenant-scoped and contains only controlled state/timestamps/counts/categories;
it excludes contact data, raw issuer/subject, tokens, headers, credentials,
free text, provider artifacts, and raw exceptions.

## 12. Acceptance criteria

An independent ratification review must confirm that the design:

1. preserves the Person/Principal/Binding/Membership ownership split;
2. specifies issuer-plus-subject uniqueness, allowlisting, normalization,
   provenance, immutable/audited binding, and fail-closed behavior;
3. prevents active Membership from a partial or inferred chain;
4. defines terminal revocation, quarantine, compensation, and deterministic
   reconciliation without deletion;
5. bounds every operation by authority, approval, receipt, audit, tenant, and
   recovery semantics;
6. prevents permanent bootstrap, self-authorization, and break-glass bypass;
7. preserves F-011 active/revoked Membership and `AuthorityChanged` constraints;
8. assigns no contract ID, schema, migration, role, provider, or implementation.

## 13. Open decisions

For the Email-First Human Identity Variant in §17, only the following policy
decisions remain open:

1. the final canonical name and governance policy of the internal issuer;
2. recovery-code expiry;
3. recovery attempt limits;
4. cooldown duration and conditions for sensitive changes; and
5. the competent human recovery authority.

Biometrics, Face ID, WebAuthn, passkeys, and Authenticator Credentials are not
open decisions for this cycle: they are explicitly deferred by §17. Contract
IDs, payloads, owners, and consumers remain future catalog work only after
ratification; they are not current scope decisions.

## 14. Risks and controls

| Risk | Control |
| --- | --- |
| Duplicate Person or false link | Evidence policy, independent approval, no weak inference, idempotent workflow. |
| Binding collision/suplantation | Registry, composite uniqueness, provenance, audit trail, fail closed. |
| Orphaned chain | Atomic boundary, durable workflow, quarantine, compensation, reconciliation. |
| Role escalation | Closed server validation, separation of duties, bounded bootstrap. |
| Cross-tenant disclosure | Active Membership resolution, tenant isolation, concealment, safe projections. |
| Vertical coupling | Core-owned semantics with no vertical data or policy assumptions. |

## 15. Required future sequence and explicit non-effects

```text
independent review → human ratification → catalog allocation → implementation gate
→ implementation/validation evidence → separately authorized real provisioning
```

Each arrow is a hard gate. OAuth and Gmail remain separately governed by
Amendment 014 and never follow implicitly from this foundation.

This document creates or changes no Person, Principal, Binding, issuer,
Membership, role, permission, contract, catalog entry, migration, database,
configuration, credential, secret, OAuth client, Gmail connection, code, or
test. It does not read PostgreSQL, invoke SQL, start Docker/services, access
Gmail/OAuth, or modify `apps/api/src/yarvis_api/api/authentication.py`. It does
not authorize a commit or push.

## 16. Ratification-readiness amendments — Proposed Design Only

This section resolves the design gaps identified by
`CANONICAL_IDENTITY_PROVISIONING_FOUNDATION_DESIGN_REVIEW.md`. It is part of
this proposed design and prevails over an earlier ambiguous description in this
document. All provisions in this section are **Proposed Design Only**: they do
not create authority, contracts, IDs, data, policies, implementation, or
runtime behavior.

### 16.1 Canonical cardinality and terminology

The terms in this design have exactly these meanings:

| Term | Proposed canonical meaning |
| --- | --- |
| Person | Canonical human/business profile, never a credential. |
| Principal | Internal authorization subject. Each productive human-interactive Principal belongs to exactly one canonical Person. Non-human/service Principal policy remains deferred. |
| Identity Binding | One verified association of exactly one Principal to one canonical `issuer + normalized_subject` pair. It is not a credential and cannot belong simultaneously to multiple Principals. |
| Membership | One Principal-to-Organization authority relationship, evaluated under the closed role policy. |
| Issuer Registry | Governed allowlist and policy source for issuer namespace, normalization, provenance, and lifecycle. |
| Provisioning Workflow | Durable prospective lifecycle/recovery record; it never grants authority. |
| Idempotency Receipt | Durable prospective replay/conflict record; it never grants authority. |

A Person may have zero or more human-interactive Principals where distinct
authentication or authority contexts are separately approved. A
human-interactive Principal may have multiple Identity Bindings. The global
canonical key is `issuer + normalized_subject`; the same pair cannot bind to
more than one Principal. A human-interactive Principal can authenticate only
through at least one verified, active Identity Binding. Service Principals remain
deferred and unimplemented, consistent with ADR-014; this design neither creates
them nor precludes their future separately ratified policy.

The current optional `Principal.person_id` and legacy `external_subject` field
are implementation evidence, not the adopted future cardinality. Legacy records
without a canonical Person or issuer remain non-authoritative and fail closed
for productive authentication, binding, provisioning, or privileged lifecycle
use until separately reconciled through a future authorized workflow.

### 16.2 Issuer normalization, versioning, and compromise

Issuer Registry normalization is issuer-specific, deterministic, and versioned.
Every proposed Identity Binding and Idempotency Receipt must preserve the
`normalization_version` used and the minimized provenance evidence that supports
the verified association. A version change is a separate auditable Provisioning
Workflow: it must detect collisions before any prospective activation, preserve
prior version evidence, and never renormalize silently.

If an issuer is credibly compromised, the future design requires all of these
immediate resolver effects:

1. suspend the issuer in the Issuer Registry;
2. block authentication through every Identity Binding of that issuer;
3. block new provisioning, binding, rebind, and rotation using that issuer;
4. preserve evidence and Membership history without destructive mutation;
5. make affected authority non-dispatchable immediately; and
6. neither revoke nor reassign identity automatically.

Recovery requires an investigation, rotation or reverification where supported,
and human approval under future authority. An issuer compromise, unknown issuer,
normalization drift, or pre-normalization collision is fail closed. It cannot be
used to transfer an Identity Binding between Principals.

### 16.3 Cross-aggregate effects, revocation, merge, and split

The resolver must apply the following immediate effects before any later
persisted remediation. A later state transition is permitted only through an
authorized, audited Provisioning Workflow; no hidden cascade, deletion, or
implicit reassignment is permitted.

| Upstream condition | Immediate resolver effect | Later persisted transition |
| --- | --- | --- |
| Identity Binding suspended or revoked | That authentication method is blocked. If the Principal has no other verified, active Identity Binding, the Principal is non-authenticatable and all of its Memberships are non-dispatchable. | Binding/Principal remediation only through a reviewed workflow; Memberships are neither deleted nor reassigned implicitly. |
| Principal disabled | All of its Memberships become non-dispatchable immediately. | Any persistent disablement or recovery is an authorized audited command/workflow. |
| Person lifecycle | No resolver effect is defined by this Foundation design. | Person lifecycle and any authority effect are deferred; no implicit cascade to Principal, Identity Binding, or Membership is permitted. Any future Person-based inactivation needs separate contract, authority, audit, and gate. |
| Organization fails the existing activity evaluation | Its Memberships cease to confer dispatchable authority immediately. | No Organization lifecycle is introduced or presumed. Person, Principal, and Identity Binding remain intact; Organization lifecycle normalization requires a separate decision. |
| Membership revoked | Existing terminal revocation blocks that Membership's authority. | It does not revoke Person, Principal, or Identity Binding. A later return requires a new reviewed Membership request. |

A Person merge is a reinforced-authority, separation-of-duties workflow. It
creates one canonical survivor and an auditable tombstone or alias for the
other Person, individually reviews each affected Principal and Identity Binding,
and never reassigns authority automatically. Any collision or insufficient
evidence enters quarantine.

A Person split is an exceptional workflow. Every affected Identity Binding is
quarantined and non-authoritative until reverification. Historical IDs and audit
evidence are preserved; destructive deletion and automatic authority transfer
are prohibited.

### 16.4 Concurrency, receipts, and deterministic conflicts

The future implementation must use the following implementation-neutral
concurrency semantics:

| Contention | Mandatory outcome |
| --- | --- |
| Same idempotency key and equivalent normalized payload | Return the same Idempotency Receipt and durable result. |
| Same idempotency key and different normalized payload | Fail closed as conflict; preserve the original receipt. |
| Different keys for the same `issuer + normalized_subject` | One request wins by canonical unique constraint and/or aggregate lock; the other is conflict or quarantine, never an alternative Binding. |
| Concurrent Person, Principal, or Membership lifecycle request | Use optimistic versioning or row/aggregate locking; the loser receives a deterministic conflict/quarantine outcome. |
| Concurrent activation and revocation | Revocation or the more restrictive effective state prevails. |
| Any persistence race | Unique constraints are the final defense; no retry may create a duplicate. |

Every conflict records its own correlation ID, causation, safe outcome, and
Idempotency Receipt/workflow state. Events/outbox records are emitted only for
the committed durable outcome. Reconciliation must deterministically locate and
quarantine inconsistent partial chains rather than inventing a winner.

### 16.5 Privacy, retention, legal hold, and evidence access

Future data governance classifies provisioning data as: (a) operational PII,
(b) Identity Binding and provenance evidence, (c) Idempotency Receipts and
Provisioning Workflows, and (d) safe audit events. A configurable retention
policy must be separately ratified before implementation; this design sets no
productive retention duration.

A future legal hold may override deletion/expunge only when explicit canonical
authority records `scope`, `reason`, `authority`, `started_at`, `review_at`, and
`expires_at`. It prevails while active and returns to the ratified retention
policy on expiry. This document creates, activates, or authorizes no legal hold.

PII deletion must use anonymization or pseudonymization where the immutable safe
audit boundary must remain. Evidence necessary to explain historical authority
is never silently erased. Evidence access is restricted, purpose-bound,
separation-of-duties controlled, and audited. Exports and reads are redacted;
tokens, secrets, raw claims, and raw provider artifacts remain prohibited.
Deletion/audit conflicts fail closed and require future human review rather than
unlogged retention extension or destructive cleanup.

### 16.6 Bootstrap and break-glass constraints

Any future bootstrap is limited to 30 days, requires review before day 14, has
minimum necessary scope, expires automatically, and is revoked immediately on
an authority change. Any future break-glass is limited to four hours, requires
an incident/reason, uses double approval when viable, prohibits self-approval,
has enhanced logging, requires post-use review within one business day, and
revokes automatically.

Neither path may create or modify an Identity Binding unless a future policy
explicitly authorizes that action. Neither path may disable tenant isolation,
audit, closed-role validation, provenance verification, or fail-closed behavior.
These are design constraints only, not an effective bootstrap, emergency grant,
permission, role, or authority.

### 16.7 Operability, recovery, and verification

Future health/status is limited to a closed allowlist of controlled status enum,
aggregate count, timestamp, controlled error category, correlation reference,
and receipt/workflow reference where the requester is authorized. It contains
no PII, raw issuer/subject, token, header, credential, free text, or raw
exception.

| Alert condition | Conceptual severity and destination | Required future runbook |
| --- | --- | --- |
| Identity Binding collision or normalization collision | High — Identity/Governance security response | Quarantine, evidence review, and approved resolution. |
| Issuer suspension/compromise | Critical — Identity security and accountable authority | Suspend resolver use, preserve evidence, investigate, reverify/rotate. |
| Quarantine age or stuck Provisioning Workflow | High — owning workflow reviewer | Inspect safe state, resume deterministically or compensate. |
| Compensation or audit/outbox failure | Critical — governance/operations response | Preserve non-dispatchable state, repair evidence path, reconcile. |
| Repeated replay/conflict | Medium — security/operations review | Assess abuse/race pattern; do not relax constraints. |
| Break-glass invocation or expiry | High — independent reviewer | Verify incident, scope, expiry, revocation, and post-use review. |
| Account-takeover signal | High — Identity security and human recovery authority | Suspend the affected authentication path fail closed, preserve evidence, investigate, and reverify under approved workflow. |
| Cross-tenant denial anomaly | High — Governance security response | Preserve concealment, investigate only safe aggregate evidence, and verify tenant-isolation invariants. |
| Retention or deletion conflict | High — privacy/governance authority | Preserve the fail-closed state, review legal-hold/retention basis, and authorize only auditable resolution. |

Runbooks are mandatory future implementation artifacts for each alert. Recovery
after interruption replays from the durable Idempotency Receipt and Provisioning
Workflow; database restore requires invariant verification before any authority
dispatch. Disaster recovery never reactivates authority automatically. A
deterministic reconciliation scan identifies collision, partial-chain,
quarantine, receipt, and workflow inconsistencies for controlled review.

The future implementation/validation gate must demonstrate all of these
verifiable criteria:

1. zero active Memberships with an invalid Person–Principal–Identity Binding chain;
2. zero duplicate `issuer + normalized_subject` Identity Bindings;
3. equivalent retries reproduce the recorded Idempotency Receipt/result;
4. revocation or the more restrictive state blocks dispatch immediately;
5. stuck Provisioning Workflows are detectable by safe health/alert evidence;
6. restore requires invariant revalidation before dispatch; and
7. logs and health output contain neither PII nor tokens.

### 16.8 Review closure matrix

| Review finding | Corrected section | Textual evidence | State and non-effect |
| --- | --- | --- | --- |
| M-001 — cross-aggregate lifecycle and merge/split | §16.3 | Resolver effect matrix; reviewed merge/split, quarantine, preserved history, no hidden cascade. | Proposed Design Only; no transition, data, or authority is implemented. |
| M-002 — binding cardinality, normalization, issuer compromise | §§16.1–16.2 | Exact cardinality; `issuer + normalized_subject`; versioned normalization; issuer suspension/reverification. | Proposed Design Only; no issuer, binding, policy, or migration is created. |
| M-003 — concurrency and race behavior | §16.4 | Receipt replay/conflict table; locks/versioning; restrictive-state precedence; unique final defense. | Proposed Design Only; no transaction, constraint, receipt, or event is implemented. |
| M-004 — retention, legal hold, privacy/access | §16.5 | Data classes, ratified future retention, legal-hold fields, redaction, purpose-bound evidence access, fail-closed conflicts. | Proposed Design Only; no hold, purge, storage, or access is authorized. |
| M-005 — operability and testable acceptance | §16.7 | Safe health allowlist, alerts/runbooks, recovery/disaster rules, seven validation criteria. | Proposed Design Only; no monitoring, runbook, restore, or dispatch is enabled. |
| N-001 — bootstrap/break-glass bounds | §16.6 | 30-day/day-14 bootstrap; four-hour break-glass; approval, expiry, review, and non-bypass rules. | Proposed Design Only; no emergency or bootstrap grant exists. |
| E-001 — Person/Principal cardinality clarity | §16.1 | Exact productive cardinality and explicit legacy/current-field boundary. | Proposed Design Only; current model is not modified or reinterpreted. |
| T-001 — no invented Person/Organization states | §§5 and 16.3 | Person lifecycle/effects are explicitly deferred with no cascade; `Organization fails the existing activity evaluation` replaces unratified Organization state terms. | Closed — Proposed Design Only; no Person or Organization lifecycle, transition, or authority is created. |

## 17. Email-First Human Identity Variant — Proposed MVP Scope Only

This narrowly scoped MVP variant applies only to human-interactive identity. It
does not change the Core ownership model, deferment of service Principals,
semantic-only contract status, or the hard future gate sequence in §15.

### 17.1 Email-first identity decision

Person and Principal retain their internal canonical IDs. A normalized and
verified email is the initial access identifier; it is neither a primary key nor
Organization authority. Email verification proves control of the mailbox at the
time of verification only. It does not independently prove employment,
Organization, Membership, role, Person-to-Principal linkage, or any authority.

The initial Identity Binding has these proposed attributes:

| Attribute | Proposed value |
| --- | --- |
| type | `verified_email` |
| subject | normalized email |
| issuer | Yarvis internal verification authority; its canonical name remains pending ratification |
| provenance | verification Idempotency Receipt only; verification codes and links are never retained |

Person-to-Principal linkage and Membership activation remain separately
authorized workflows. An email binding never selects an Organization, grants a
Membership, dispatches authority, or changes a role.

### 17.2 Email change and recovery

An email change requires a future authorized semantic command, fresh
verification, idempotency, audit, and revocation of the prior Identity Binding.
It is subject to the existing collision, concurrency, separation-of-duties,
quarantine, and fail-closed rules. No email change can silently transfer an
Identity Binding or authority.

The proposed MVP recovery path uses one-time recovery codes with all of these
properties:

- only a hash is stored;
- each code is delivered exactly once;
- rotation invalidates the entire prior code set;
- controlled human recovery uses separation of functions;
- sensitive changes require the future policy's cooldown and review; and
- recovery cannot depend exclusively on the primary email path.

Recovery cannot create, activate, assign, or modify a Membership, role, or
Organization authority. It can only begin a controlled identity-recovery
workflow under future authority.

### 17.3 Explicit deferrals and intake boundary

Biometrics, Face ID, WebAuthn, passkeys, and Authenticator Credentials are
explicitly deferred. They are neither designed nor implemented in this cycle.

An authentication email grants no Gmail API, OAuth, Gmail mailbox access,
reading, labels, or synchronization. Gmail Intake remains a later independent
cycle governed by Amendment 014 and its gates. WhatsApp Intake follows Gmail
and may reuse only already-ratified patterns for intake, authority, and human
review; it receives no authority from this Email-First Human Identity Variant.

### 17.4 Variant non-authority

This MVP scope decision is Proposed Design Only. It creates no email binding,
verification, recovery code, issuer, Person, Principal, Membership, role,
contract, catalog entry, code, migration, OAuth flow, Gmail capability, or
WhatsApp capability. It does not authorize provisioning, implementation, or
external access.
