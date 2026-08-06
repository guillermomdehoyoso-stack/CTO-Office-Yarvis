# YARVIS
# F-011 Identity and Authority Envelopes Architecture Amendment 001

## Status

**RATIFIED — ARCHITECTURAL DESIGN ONLY — NOT IMPLEMENTATION AUTHORIZATION**

**Steward:** Architecture Authority
**Ratified by:** Guillermo, Architecture Authority, 2026-08-06
**Scope:** F-011 Identity and Authority Envelopes only.  This ratified amendment
supplements the Foundation plan without changing the ratified completion path
or opening an engineering gate.

**Sources:** [AR-001](../architecture/AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md),
[Technical Blueprint](TECHNICAL_BLUEPRINT.md), [Roadmap Amendment 002](IMPLEMENTATION_ROADMAP_AMENDMENT_002.md),
[Roadmap Amendment 003](IMPLEMENTATION_ROADMAP_AMENDMENT_003.md),
[Interaction Contract Catalog](../architecture/INTERACTION_CONTRACT_CATALOG.md),
[ADR-013](../decisions/ADR-013_NETPAY_DOCUMENT_INTAKE_ORGANIZATIONAL_AUTHORITY.md),
and [IG-005](IG-005_NETPAY_DOCUMENT_INTAKE_IMPLEMENTATION_AUTHORIZATION.md).

## 1. Purpose and Boundary

F-011 supplies the minimum trustworthy organization context required by the
Foundation: an inbound authenticated identity is resolved to a persisted
Principal, a persisted active membership is validated, an active Organization
is resolved, server-controlled permissions are evaluated, and target handlers
verify resource ownership.  It is not a general identity-management product.

The mandatory Foundation completion graph remains exactly:

```text
F-012 -> F-013 -> F-011 -> F-016 -> F-017 -> F-010 -> F-014 -> F-015
```

F-011 does not initiate F-016, F-017, F-010, F-014, F-015, DI-003, C09,
Document Registry extension, upload, download, storage, Gmail, WhatsApp, OCR,
AI, cloud storage, workers, queues, brokers, SSO, OAuth, password recovery,
invitations, or generic user administration.

## 2. Ratified Ownership and Persistent Concepts

| Concept | Owner | Ratified responsibility | Explicit non-ownership |
| --- | --- | --- | --- |
| Principal | Identity | Stable immutable identifier, lifecycle state, optional business-profile reference. | Passwords, tokens, secrets, Membership, permissions. |
| Person | Identity business profile | Optional business profile and contact representation. | Credential or authentication identity. |
| PrincipalMembership | Governance | Principal-to-Organization membership, role, lifecycle and revocation. | Principal identity or Organization lifecycle. |
| Permission matrix | Governance | Closed server-versioned mapping from role to permissions. | Client-declared role, authority, or policy editing. |
| Identity/Authority Envelope | F-011 application boundary | Trusted evaluated context passed to a target handler. | A client-controlled claim bag or a second source of authority. |

`Principal` is ratified as persistent and separate from `Person`: immutable
`id`, `status` (`active` or `disabled`), `created_at`, `updated_at`, and an
optional `person_id`.  A disabled Principal cannot authenticate or receive
authority.  It stores no password, token, credential, secret, or PII beyond an
optional foreign reference to Person.  Service principals are deferred, while
the identifier model must not preclude them.

`PrincipalMembership` is ratified as persistent with `principal_id`,
`organization_id`, `role`, `status`, `created_at`, and nullable `revoked_at`.
Allowed status is `active` or terminal `revoked`.  `(principal_id,
organization_id)` is unique; only active membership may confer authority; an
inactive Organization cannot be active context; and a revocation is effective
on every subsequent request.

## 3. Active Organization and Trust Boundary

The client may request an `organization_id` only as a selector.  The server
resolves it against persistent active memberships:

1. no active membership: deny;
2. exactly one active membership and no selector: derive that organization;
3. multiple active memberships and no selector: reject as ambiguous;
4. selector present: accept only an existing active Organization with active
   membership for the resolved Principal; otherwise conceal as `not found`.

`X-Yarvis-Workspace` may temporarily carry the selector during Radar migration,
but is never a source of identity, membership, role, permission, or authority.
Headers carrying actor, organization, role, or authority are likewise claims at
most.  The existing deterministic provider remains local/test-only and may
attest a development external identity, but Principal, Membership,
Organization, role, and permissions must be re-resolved from persistence.

The resulting trusted envelope contains only `principal_id`, `organization_id`,
`validated_permissions`, `authentication_source`, and correlation/tracing
metadata.  It contains no token, password, raw header authority, or unnecessary
PII.  Evaluation is strictly:

```text
authentication -> principal resolution -> membership validation
-> active organization resolution -> server-side permission evaluation
-> target resource ownership validation
```

Every target handler requires its permission and verifies ownership against the
envelope Organization, rather than relying only on a route filter or repository
lookup.  Cross-organization resources are concealed as `not found`; logs and
events retain only safe identifiers and trace metadata.

## 4. Ratified Minimum Roles and Permission Matrix

The matrix is a closed, server-versioned F-011 policy, not client data:

| Role | Validated permissions | Purpose |
| --- | --- | --- |
| `radar_viewer` | `radar.read`, `radar.activity.read` | Read the migrated Radar only. |
| `radar_operator` | `radar.read`, `radar.activity.read`, `radar.merchant.create`, `radar.request.create`, `radar.request.update`, `radar.checklist.update`, `radar.request.close`, `radar.request.reopen`, `radar.note.create` | Preserve current accepted Radar operations. |
| `foundation_membership_operator` | `governance.membership.create`, `governance.membership.revoke` | Bounded bootstrap/revocation operation required by F-011; not a generic administration product. |

No document permission, DI-003/C09 permission, policy editor, delegation UI, or
external identity-provider permission is authorized.  The server maps role to
permissions; the client cannot submit either value.

## 5. Contract Decision Matrix

The catalog's historic Runtime Baseline V1 records the six existing contracts
as Proposed/Planned. Their current names and owners are insufficient to infer
F-011 allocation; the ratified profiles below are the only exception.

| Contract | Decision | Reason, consumer, and F-011 acceptance boundary |
| --- | --- | --- |
| `IC-IDENTITY-CMD-001 ResolveSubjectCandidate` | **DEFERRED** | Resolves Party/PartyGroup candidates for intake, not security Principal lifecycle. It must not become credential or membership management. |
| `IC-IDENTITY-QRY-001 RetrieveCanonicalIdentity` | **DEFERRED** | Returns canonical business identity references; it does not resolve an authenticated Principal. |
| `IC-IDENTITY-EVT-001 IdentityResolutionRecorded` | **DEFERRED** | Records subject-resolution provenance, not Principal status or membership change. |
| `IC-GOVERNANCE-QRY-001 EvaluateAuthority` | **RATIFIED F-011 PROFILE** | The compatible F-011 profile is ratified by [Governance Contract Amendment 001](F-011_GOVERNANCE_CONTRACT_AMENDMENT_001.md): trusted Principal, server-resolved Organization, validated permission, target ownership, concealed cross-organization absence, and no client-declared authority. |
| `IC-GOVERNANCE-QRY-002 RetrieveApplicableDelegation` | **REJECTED FOR F-011** | Delegation is not required for the minimum Principal/Membership slice; introducing it would widen Governance scope. |
| `IC-GOVERNANCE-EVT-001 AuthorityChanged` | **RATIFIED F-011 PROFILE** | The compatible F-011 profile is ratified by [Governance Contract Amendment 001](F-011_GOVERNANCE_CONTRACT_AMENDMENT_001.md): attributed Membership activation/revocation, canonical Organization, safe trace, replay/conflict semantics, and immediate later-request effect. |

Before implementation, Contract Registry review must additionally decide whether
new identities are needed for Principal resolution and membership mutation.  If
needed, the candidate semantic family is a Principal resolution query and a
Governance Membership command; identifiers, payloads, lifecycle, version,
consumer, idempotency, and events are **not allocated by this proposal**.

## 6. Radar Consumer and Migration Proposal

Radar migration is a mandatory F-011 closure criterion, not an optional later
consumer.  Radar merchants, requests, checklist items, next action, close and
reopen transitions, and append-only activity must operate under canonical
`organization_id` and the trusted envelope while preserving the accepted user
journey.

The implementation design must define a deterministic local/test backfill from
each Radar `workspace_id` to an existing Organization.  It must create or map
the required Principals and active Memberships deterministically.  Ambiguous or
unmapped records are not silently assigned: they are rejected from migration,
reported for explicit disposition, and cannot receive active authority.

The migration must preserve historical Radar behavior without claiming that
legacy workspace strings were authority.  It requires a reviewed forward
migration, downgrade, and re-upgrade path; cross-organization command and query
tests; idempotent replay tests; and persistence tests.  It must not add
documents, upload/storage, or reinterpret `checklist.received`.

## 7. Implementation and Closure Gate

This ratified architecture authorizes no runtime work.  A future F-011
implementation gate may be approved only after the ratified contract profiles
are allocated, `CURRENT_STATE` and `CURRENT_SPRINT` explicitly open F-011, and
a reviewed implementation design defines migration and failure handling.

F-011 may close only when all of the following are demonstrated:

1. Principal is persistent, resolvable, and disabled principals are denied.
2. Membership is persistent, unique, active/revocable, and revocation takes
   effect on subsequent requests.
3. Server resolves active Organization and server-derived permissions.
4. Unauthorized commands are rejected; commands and queries are organization
   isolated; cross-organization references are `not found`.
5. No authority is derived from arbitrary headers.
6. Radar is migrated while preserving accepted workflow and audit behavior.
7. Allocated contracts, migrations upgrade/downgrade/re-upgrade, focused,
   cross-organization, idempotency and affected regression tests, compile/Docker
   validation, and `git diff --check` pass.
8. A post-implementation closure records real evidence.

DI-003/C09 remains Not Authorized until this closure, an expressly Approved
IG-005, and a separate implementation mandate.

## 8. Ratification Record and Non-Authorization

Guillermo, as Architecture Authority, ratified the ownership split, Principal
and Membership state machines, selector rule, closed roles/permission matrix,
deterministic-provider boundary, Radar mandatory migration, Governance contract
profiles, and closure gate on 2026-08-06.  This ratification does not authorize
code, tests, migrations, configuration, deployment, staging, commit, or
production use.
