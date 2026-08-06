# YARVIS
# F-011 Identity and Authority Envelopes Implementation Design

## Status

**REVIEWED — APPROVED AS IMPLEMENTATION DESIGN — NOT AUTHORIZED FOR IMPLEMENTATION**

**Date:** 2026-08-06
**Reviewed and approved by:** Guillermo de Hoyos
**Approval scope:** technical implementation design only; no runtime authority.
**Scope:** implementation design for the ratified F-011 architecture only. This
document does not open F-011, activate IG-006, or authorize runtime work.

**Authority:** [F-011 Architecture Amendment 001](F-011_IDENTITY_AUTHORITY_ENVELOPES_ARCHITECTURE_AMENDMENT_001.md),
[ADR-014](../decisions/ADR-014_PRINCIPAL_MEMBERSHIP_ACTIVE_ORGANIZATION_AUTHORITY.md),
and [F-011 Governance Contract Amendment 001](F-011_GOVERNANCE_CONTRACT_AMENDMENT_001.md).
It is subordinate to the Technical Blueprint, Contract Registry governance, and
Roadmap Amendments 002/003.

## 1. Boundary, Current Evidence, and Closed Change Inventory

The implementation replaces the current local/test header-claimed authority
boundary with a persistence-resolved envelope. It does not add an identity
provider, passwords, sessions, invitations, delegation, documents, DI-003/C09,
workers, queues, or any successor Foundation package.

Current evidence is explicit:

- `api/authentication.py` builds `AuthenticatedPrincipal` from
  `X-Yarvis-Actor`, `X-Yarvis-Organization`, `X-Yarvis-Authority`,
  `X-Yarvis-Roles`, and `X-Yarvis-Permissions` after a deterministic token.
- `models/radar.py` and migration `20260806_31` scope Radar by a client-supplied
  string `workspace_id`; `api/routes/radar.py` obtains it directly from
  `X-Yarvis-Workspace`.
- `Organization` and `Person` already use UUID primary keys and timestamps.
  `Organization.status` is an existing string state. No `Principal` or
  `PrincipalMembership` exists.
- Application contracts currently carry a header-derived `authority` scope;
  they are an implementation gap, not evidence of server-evaluated authority.

| Class | File/component | Current state | Proposed F-011 change | Dependency/risk | Acceptance criterion |
| --- | --- | --- | --- | --- | --- |
| New | `models/principal.py` | absent | `Principal` and `PrincipalMembership` ORM mappings | Alembic; lifecycle constraints | persistence and constraints prove invariants |
| New | `application/authority.py` | absent | immutable `IdentityAuthorityEnvelope`, role matrix, resolver interfaces | ratified roles | no request DTO can construct authority |
| New | `services/authority_resolution.py` | absent | persistence lookup, selector resolution, permission evaluation | repositories/session | every denial path is deterministic |
| New | `api/dependencies/authority.py` | absent | request dependency producing the envelope | FastAPI composition | handlers receive trusted envelope only |
| New | focused F-011 tests | absent | unit, API, migration, Radar isolation and contract tests | approval only | matrix in section 12 passes |
| Modified | `api/authentication.py` | trusts actor/org/role/permission headers | deterministic provider authenticates only a local/test external subject | compatibility transition | headers never grant authority |
| Modified | `application/authentication.py`, `application/ports.py` | mutable semantic fields in `AuthenticatedPrincipal` | replace at handler boundary with envelope and resolver port | affected Intake adapter | explicit compatibility adapter is temporary |
| Modified | `bootstrap.py` | composes deterministic provider only | compose resolver, repositories and dependencies at root | DI only at bootstrap | no service locator |
| Modified | `models/radar.py`, Radar route/schema/service boundary | workspace-owned records and caller `actor` payload | canonical `organization_id`, envelope actor, permission/ownership checks | mandatory Radar migration | accepted Radar journey is preserved |
| Modified | `models/__init__.py`, canonical contract/application contract bindings | no F-011 mappings | export models and bind two ratified Governance profiles | registry review | only QRY-001/EVT-001 profiles implemented |
| New | linear Alembic revisions after `20260806_31` | no F-011 schema | Principal/Membership then Radar backfill/constraints | data preflight | upgrade/downgrade/upgrade proven |
| Preserved | Document Registry, DI-003/C09, Identity CMD/QRY/EVT, Governance QRY-002 | separate/deferred/rejected | no change | scope breach | no files or contracts added |
| Closure only | CURRENT_STATE, CURRENT_SPRINT, closure document | F-011 unstarted | update only after factual closure evidence | gate governance | no premature status claim |

## 2. Persistent Model and Database Rules

Identity owns `principals`; Governance owns `principal_memberships`. Both follow
the repository's `TimestampedUUIDMixin`, PostgreSQL UUID, timezone-aware
timestamp, explicit named-constraint, and indexed-organization conventions.

### Principal

`principals`: `id UUID PK`; `external_subject VARCHAR(255) NOT NULL UNIQUE`;
`status VARCHAR(16) NOT NULL`; nullable `person_id UUID FK people.id`;
`created_at`, `updated_at`. Use a named check `status IN ('active','disabled')`,
an index on `(external_subject)`, and an index on `person_id` if query evidence
shows it necessary. `external_subject` is the deterministic provider's sole
authenticated assertion and is immutable after creation. It is not a token,
credential, secret, email, or display name. `person_id` is optional and
`ON DELETE SET NULL`; deleting a Person cannot delete or relink Principal
history. Principal deletion is not part of F-011.

### PrincipalMembership

`principal_memberships`: `id UUID PK`; `principal_id UUID NOT NULL FK
principals.id`; `organization_id UUID NOT NULL FK organizations.id`; `role
VARCHAR(64) NOT NULL`; `status VARCHAR(16) NOT NULL`; `created_at`; nullable
`revoked_at`. Add named checks for `status IN ('active','revoked')` and the
paired temporal invariant: active has null `revoked_at`; revoked has a non-null
`revoked_at`. Add unique `(principal_id, organization_id)`, an index on
`(principal_id,status)`, and an index on `(organization_id,status)`. FKs use
`RESTRICT`: Authority history cannot be silently cascade-deleted. The only
transition is `active -> revoked`; revocation is terminal. Reactivation requires
a separately authorized semantic change, not an update that rewrites history.

The resolver rejects an inactive Organization (`organizations.status !=
'active'`) even if an active Membership exists. The role is persisted as a
closed string rather than a new role table; unknown roles deny by default and
are logged only with safe IDs. All Principal/Membership creation, revocation,
event append, and idempotency record (when allocated) share one transaction.

## 3. Closed Role Matrix

The server-owned constant belongs in `application/authority.py`, next to the
value object, rather than in a request schema, database table, or frontend.
It is versioned by source and must be exhaustive.

| Role | Validated permissions | F-011 consumers |
| --- | --- | --- |
| `radar_viewer` | `radar.read`, `radar.activity.read` | dashboard, merchant/request/checklist/activity reads |
| `radar_operator` | viewer permissions plus `radar.merchant.create`, `radar.request.create`, `radar.request.update`, `radar.checklist.update`, `radar.request.close`, `radar.request.reopen`, `radar.note.create` | all migrated Radar writes |
| `foundation_membership_operator` | `governance.membership.create`, `governance.membership.revoke` | bounded F-011 Membership bootstrap/revocation entry point |

Role, permission, `authority`, and organization values supplied in headers or
payloads are ignored for authorization; endpoints that currently require them
must stop accepting them. An unknown persisted role results in deny-by-default
(`403` for a known same-organization target; no envelope permission) and a safe
security log with Principal/Membership IDs and correlation ID. No document or
DI-003/C09 permission is introduced.

## 4. Resolution Pipeline and Failure Contract

```text
deterministic authentication -> external_subject -> Principal lookup -> active
Principal -> active Membership lookup -> selector resolution -> active Organization
-> closed role matrix -> immutable envelope -> handler permission -> repository
organization ownership
```

| Step / owner | Trusted input | Result and failure |
| --- | --- | --- |
| API authentication adapter | deterministic token only in local/test | emits `external_subject`, authentication source and correlation ID; invalid token is `401`/authorization-denied |
| Identity resolver | adapter subject | no Principal or disabled Principal: deny before resource lookup; log safe reason |
| Governance resolver | persisted memberships | no active membership: `403`; revoked Membership is excluded |
| selector resolver | optional `X-Yarvis-Workspace` selector | one membership/no selector derives it; many/no selector is `409` ambiguous context; nonexistent or foreign selector is `404` |
| Organization validation | persisted Organization | inactive Organization: `403` without an envelope |
| policy evaluator | persisted role, server map | unknown role or missing permission: `403` |
| target handler/repository | envelope plus target ID | foreign target and foreign related reference: `404`; lists filter by canonical organization |

The selector remains untrusted input. During transition it maps through the
preflight-approved `workspace_id -> organization_id` correspondence, never
through a client-provided UUID. It may be omitted only when there is exactly one
active Membership. Correlation is taken from the existing correlation header or
generated at the request boundary; it is trace metadata, not authority. Logs
contain safe IDs, outcome, reason classification, contract ID/version and
correlation; never token, raw header authority, permissions list, email, or
unnecessary person data.

## 5. Headers, DTO Replacement, and Envelope

`X-Yarvis-Workspace` is a temporary selector only. `X-Yarvis-Actor`,
`X-Yarvis-Organization`, `X-Yarvis-Authority`, `X-Yarvis-Roles`,
`X-Yarvis-Permissions`, and system-actor claims are removed from the
deterministic provider's authority path. The provider accepts a local/test token
and authenticated subject only; it then re-resolves all authority data from
persistence. Existing `AuthenticatedPrincipal` is retained only behind a
short-lived Intake compatibility adapter until each consumer migrates; its
header-derived fields must not reach a F-011-migrated handler.

`IdentityAuthorityEnvelope` is a frozen, slots dataclass in
`application/authority.py`:

```text
principal_id: UUID
organization_id: UUID
validated_permissions: frozenset[str]
authentication_source: str
correlation_id: str
```

It is built only by `AuthorityResolutionService`, transported via a FastAPI
dependency, and passed explicitly to application handlers. It excludes raw
token, headers, role, Membership mutable state, Person fields, credentials,
and client authority claims. The type is not a request DTO and has no public
constructor exposed to transport code.

## 6. Handler, Repository, and Radar Transition

Every migrated command/query declares one required permission. The handler
checks it before mutation; repository predicates additionally include
`organization_id` as defence in depth. Single resources and related IDs are
loaded through same-organization predicates, returning `404` for foreign or
nonexistent records. Lists always filter by envelope organization. A malformed
same-organization request is `422`; an idempotency key reused with a different
fingerprint is `409`; authentication failure is `401`; known authority failure
is `403`. No query emits an event.

Radar is mandatory and must change together:

| Consumer | Current scope | F-011 target | Required permission / proof |
| --- | --- | --- | --- |
| merchants/dashboard/detail | `workspace_id` | `organization_id` on merchant | `radar.read`; foreign list empty and foreign detail `404` |
| requests/create/read | workspace string and payload actor | canonical organization; envelope principal is activity actor | create/read permissions; related merchant same organization |
| checklist/next action/notes | request workspace and payload actor | request/merchant canonical organization | update/note permissions; foreign IDs `404` |
| close/reopen | request workspace and payload actor | envelope + same organization transaction | close/reopen permissions; accepted close behavior unchanged |
| activity | workspace and text actor | canonical organization + `principal_id` safe actor reference | `radar.activity.read`; append-only trigger retained |

Migration adds `organization_id` to `radar_merchants`, `radar_requests`, and
`radar_activities`; `RadarChecklistItem` inherits ownership through its request.
Composite foreign keys or transactional same-organization verification prevent a
request from referencing a merchant in another organization. Temporary
`workspace_id` remains only for selector/backfill compatibility, is not used as
an authorization predicate after cutover, and is removed only in a later
reviewed cleanup revision. Existing actor strings remain historical display
evidence; F-011 writes use safe Principal IDs (with a separately defined
display projection if needed), never a payload actor.

## 7. Ratified Governance Profiles

`IC-GOVERNANCE-QRY-001 EvaluateAuthority` v1.1.0 is implemented as the
application entry point used by the request dependency/handler: input is a
trusted envelope, required permission, target descriptor and correlation; its
output is allow/deny or concealed not-found. It has no side effect. Consumers
are migrated target-command/query handlers. Tests prove disabled/revoked/
inactive/ambiguous/foreign denial, ignored headers, ownership, and no mutation.

`IC-GOVERNANCE-EVT-001 AuthorityChanged` v1.1.0 is appended transactionally by
the bounded Membership activation/revocation command after the mutation. It
contains Membership ID, canonical organization ID, accountable Principal ID,
transition, occurred/recorded times, correlation, optional causation and
version `1.1.0`; no token, credential, raw headers, document content or excess
PII. The command must define organization-plus-idempotency-key fingerprinting:
an equivalent replay returns the original outcome with no duplicate event;
conflicting reuse is `409`. The next authorization request queries persistence,
so revocation takes effect immediately. Identity CMD/QRY/EVT remain deferred;
QRY-002 remains absent.

Before coding, Contract Registry review must either allocate the bounded
Principal-resolution and Membership-mutation identities or approve their exact
use of existing mechanics. This design does not allocate IDs.

## 8. Migration, Backfill, and Rollback Design

No migration is created by this document. The authorized implementation must
use linear revisions after `20260806_31`:

1. Create `principals` and `principal_memberships` with FKs, checks, unique
   constraints and lookup indexes. Downgrade removes them only if no dependent
   cutover revision remains.
2. Add nullable `organization_id` and required supporting composite constraints
  /indexes to Radar tables, preserving `workspace_id` and historical activity.
3. Run a read-only preflight report before backfill. Each Radar workspace is
   classified `unambiguous`, `absent`, `multiple`, or `inconsistent` against
   existing Organizations and an explicit approved mapping. The report names
   only safe IDs/counts; absent/multiple/inconsistent rows stop cutover.
4. In one reviewed data revision, populate only unambiguous mappings, create
   local/test Principals and active Memberships only from an explicit approved
   subject-to-Organization seed map, and record counts/checksums for review.
   It never creates an Organization implicitly or treats a workspace as
   Membership evidence.
5. Validate no null/mismatched organizations, then make Radar organization
   ownership non-null and enforce same-organization related references. Update
   routes to envelope predicates; retain workspace only as selector bridge.
6. Downgrade removes new enforcement only after restoring nullable transition
   columns without deleting Radar records; re-upgrade repeats deterministically.

Ambiguous historical data is a stop condition requiring human disposition. The
backfill preserves all activity and does not retroactively claim historical
actors had authority. Migration evidence includes preflight output, row counts,
constraint checks, upgrade/downgrade/upgrade, and no partial transaction state.

## 9. Test Plan

| Layer | Planned suites and minimum evidence |
| --- | --- |
| Unit | envelope immutability; closed role map; unknown role deny; selector cases; safe log projection |
| Application/handler | permission required for command/query; no header authority; correct status taxonomy; QRY-001 no mutation |
| Repository | organization predicates on detail/list/related references; foreign returns no row |
| API | no Principal, disabled Principal, revoked Membership, inactive Organization, one/many membership, valid/foreign selector, missing permission |
| Governance contract | QRY-001 v1.1 behavior; EVT-001 payload, attribution, equivalent replay and conflicting idempotency reuse |
| Radar | every merchant/request/checklist/next-action/note/close/reopen/activity flow under envelope; existing ON/OFF and append-only behavior preserved |
| Cross-organization | foreign command, query, list and linked reference are concealed; no list leakage |
| Migration | preflight classifications; ambiguous backfill stops; upgrade/downgrade/upgrade; constraints and historical activity preservation |
| Regression/quality | affected API and web suites, full regression, Docker compile, `compileall`, and `git diff --check` |

New test files should be focused (`test_authority_resolution.py`,
`test_governance_authority_contracts.py`, `test_radar_authority.py`, and a
migration test) while existing `test_authentication_boundary.py`,
`test_application_contracts.py`, `test_operational_radar.py`, and
`test_radar_migration.py` are extended. No executable test is created now.

## 10. Authorized-Only Future Slice Sequence

| Slice | Permitted future change | Advance evidence / rollback risk |
| --- | --- | --- |
| A | models and first migration | constraints plus round trip; downgrade before cutover |
| B | resolver and immutable envelope | all resolution denials; retain compatibility adapter |
| C | closed role matrix and dependencies | deny-default and header-ignorance tests |
| D | QRY-001/EVT-001 profile bindings and bounded Membership command | contract/replay tests; transaction rollback |
| E | Radar reads and lists | cross-org concealment; preserve workspace bridge |
| F | Radar commands and activity actor transition | atomic writes/idempotency; rollback route cutover |
| G | Radar data backfill and final constraints | preflight clean, migration round trip; stop on ambiguity |
| H | deprecated authority-header removal | no legacy consumer remains; compatibility risk review |
| I | regression and factual closure | all required evidence; no closure on a failed gate |

Slices cannot be started by this document. Each requires the future IG-006
approval and implementation mandate; failures stop before the dependent slice.

## 11. Closure Evidence and Residual Decisions

F-011 closure requires persisted/resolvable Principal; active/revocable unique
Membership; server organization/permissions; ignored authority headers;
implemented QRY-001/EVT-001 profiles; fully migrated Radar; organization-safe
commands/queries and `404` concealment; migration round trip; focused and full
regression; Docker/compile; and post-code closure/status updates based on real
evidence.

Ratified and not reopenable here: ownership split, states, selector rule,
roles, Radar obligation, contract profile choices, and DI-003/C09 block.
Technical details determined by repository convention: UUID/timestamps,
SQLAlchemy/Alembic naming, FastAPI dependencies, PostgreSQL checks/FKs, and
append-only Radar activity trigger.

There are no new human architecture decisions required to review this design.
The implementation authorization must still decide the approved, explicit
local/test subject-to-Principal and workspace-to-Organization seed mappings
from actual data; this is a controlled migration disposition, not a new
authority model. Production identity-provider selection remains deferred before
production. Security risks are header-trust leakage and cross-org joins;
mitigations are server resolution, predicates, constraints, and concealment.
Migration risk is ambiguous legacy data; mitigation is mandatory preflight and
stop. Radar compatibility risk is changing scope while preserving the accepted
flow; mitigation is staged selector compatibility and focused regression.

## 12. Non-Authorization

This approved design does not modify runtime, tests, migrations, configuration,
fixtures, seeds, Radar, DI-003/C09, or the dependency graph:

```text
F-012 -> F-013 -> F-011 -> F-016 -> F-017 -> F-010 -> F-014 -> F-015
```

It is approved as an implementation design only. The required package before
runtime is still: explicit F-011 opening in CURRENT_STATE/CURRENT_SPRINT;
IG-006 changed by authority to an approved active gate; and a separate mandate
naming the branch, Slices A-I, validation responsibility, and stop conditions
above.
