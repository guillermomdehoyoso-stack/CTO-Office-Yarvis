# ADR-020 — Ratify Temporary Role Authority Architecture

Status: **PROPOSED — DRAFT — NO CONTRACT REGISTRATION, IMPLEMENTATION, RELEASE OR ASSIGNMENT AUTHORITY**

Draft date: 2026-09-09

Ratification readiness: **PENDING INDEPENDENT REVIEW**. T-01, T-02 and T-03 are individually RESOLVED AT DESIGN LEVEL. This correction records no independent acceptance or ratification.

Scope: Superior architecture for ADR-019 Package B — Expiry-aware Temporary Role Authority.

## 1. Context and proposed architectural Decision

### 1.1 Context and immutable source identity

ADR-019 ratifies Contract and Role Allocation and requires separate architecture for Package B. Package A remains **IMPLEMENTED — CONFORMANT — EVIDENCE GATE PASSED**. Package B has accepted design input but no ratified superior ADR, implementation authority or implementation conformance. The current engineering gate permits documentary correction and independent review only. After validation the next allowed action is renewed independent review; no ratification recommendation is inferred from documentary validation.

The accepted source is [Temporary Role Authority Proposal](../engineering/NETPAY_MVP2D1_TEMPORARY_ROLE_AUTHORITY_PROPOSAL.md). This ADR retains that design and records terminal-review corrections T-01/T-02/T-03. The bounded Architecture Authority clarification for T-03 is recorded in section 9.4, separately from the unrecorded future ratification act. The proposal and its acceptance act remain unchanged.

| Identity or preflight fact | Verified value |
| --- | --- |
| Local and remote HEAD before this draft | `d74d0c7c9365b68a2f29ee60519191fc606e6e9e`, branch `feat/operational-intake-spine` |
| Parent | `cca7c441393787e313fabbe7366dd1b78cb9a776` |
| Accepted proposal as recorded at HEAD, canonical SHA-256 | `F1B0433563FE96DCBE27EC3AAC6C92EB29D6F20D43FB61E95E12EA47C681CBFA` |
| Proposal status | ACCEPTED PROPOSAL — ADR REQUIRED — NO CONTRACT REGISTRATION, IMPLEMENTATION OR ASSIGNMENT AUTHORITY |
| Proposal acceptance authority and date | Guillermo de Hoyos, Architecture Authority of Yarvis; **2026-09-08**, local decision date, not adjusted to UTC or commit time |
| Design version identified by the proposal acceptance act | Commit `cca7c441393787e313fabbe7366dd1b78cb9a776`; canonical SHA-256 `E7C0344883A9C57C6F9EB218CF9FAA11BB34F0174E9C18716E8014526E910E4E` |
| Source terminal review disposition | ACCEPT, expressly accepted by Architecture Authority with no mandatory findings pending; design only |
| Source acceptance exceptions / downstream authority | None / None |
| ADR-019 canonical SHA-256 | `5A44BE2296DF2EA11733D32E9900CC9B01687692089C367B2152C76CBFBB387E`, unchanged |
| Preflight worktree and index | Only `?? AUDIT_REPORT.md`; index empty; proposal physical bytes equal HEAD blob |
| ADR number and filename | ADR-020 is the next free number after ADR-019; inventory and reference search found no ADR-020, equivalent superior Package B ADR or filename collision before creation |
| Migration head, not changed by this draft | `20260823_47`, parent `20260823_46`; `apps/api/migrations/versions/20260823_47_first_organization_receipts.py` |

Canonical hashes use strict UTF-8 without BOM, normalizing CRLF and lone CR to LF. The two proposal hashes identify different documentary versions: reviewed design and subsequent recording of its acceptance. Neither is the hash of this new ADR. The source's earlier discovery baseline was `e75e86d5d9a66c677c2eaece5e24bcdc39d581ca`; §2 preserves that inventory and its call-site locations, not a claim that implementation work has occurred. Candidate paths and allocations were rechecked for this draft; they require revalidation again before future authorization.

### 1.2 Decision — proposed, architectural authority only

The decision proposed for later ratification is to adopt the complete architecture in §§3–17: a Governance-owned canonical TemporaryRoleAssignment and independent receipt; one physical Membership role; PostgreSQL-maintained P/O/M/A authority revisions; fresh protected temporal resolution; separate revocation and reconciliation/restoration; and a caller-owned Identity session invalidation participant. The controlled role transition is `netpay_operations_operator` → `netpay_intake_pilot_operator`. Static permission lookup never grants Intake.

B1, B2 and B3 are **separate implementation work packages under this one superior architecture**, not automatically authorized phases. Each requires its own subsequent authority act, exact Authorized File Boundary, Evidence Gate, rollback, independent review, commit and conformance. Integral conformance and any later release/promotion or operational assignment require separate authority as well. Future architectural ratification alone cannot authorize any of them. No separate implementation ADR is presumed accepted or required by merely naming these work packages; the later authority act must specify the governing artifacts under AR-001.

This document is Proposed. Normative "must" and "shall" statements describe the architecture submitted for review; they confer no present implementation or operational authority. Creating this ADR neither ratifies it nor registers/reserves contracts, implements controls or closes a roadmap gate.

### 1.3 Governing relationships

| Governing source | Exact relationship and retained limit |
| --- | --- |
| [AR-001](../architecture/AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md) | Governs proposal, independent review, explicit architectural ratification, separately bounded implementation and conformance; none is inferred from drafting |
| [ADR-019](ADR-019_RATIFY_NETPAY_MVP2D1_CONTRACT_AND_ROLE_ALLOCATION.md) | Parent allocation architecture; Package A conformance remains intact. On later explicit ratification, §8 prospectively specifies the parent day-based wording as 336/720 absolute hours for Package B. Historical authority and all other parent limits remain unchanged |
| [ADR-017](ADR-017_RATIFY_DISPATCH_HANDLER_FACTORY_COMPOSITION.md) | Dispatcher owns the single Command UoW; actual handler factory receives the active Session/facade; exactly one explicit handler facade commit follows the final gate. Platform conformance is not business authority |
| [Amendment 018](../engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_018.md), §8.3 | Contract and role-mechanism conformance precedes express evidence acceptance and explicit §8.3 closure; productive assignment requires a subsequent separate operational act. Effective assignment is not a closure prerequisite. Closure authorizes no assignment and opens neither §8.5 nor later gates |
| [Accepted Contract and Role Allocation proposal](../engineering/NETPAY_MVP2D1_CONTRACT_AND_ROLE_ALLOCATION_PROPOSAL.md) | Upstream accepted design input as identified by ADR-019 and the accepted Package B proposal; no new implementation authority |
| [AUTH-POLICY-001](../engineering/AUTH_POLICY_001_PRODUCTIVE_IDENTITY_AND_SESSION_SECURITY.md), §§4–5 | Material authority loss/change invalidates affected sessions and requires new authentication; base entitlement is distinct from session continuity |
| [AUTH-CONTRACT-001](../engineering/AUTH_CONTRACT_001_PRODUCTIVE_IDENTITY_AND_SESSION_CONTRACTS.md) | Existing Identity/session contracts and Governance query responsibilities remain; future profile amendments must be explicit |
| [ADR-014](ADR-014_PRINCIPAL_MEMBERSHIP_ACTIVE_ORGANIZATION_AUTHORITY.md) | Canonical Principal/Membership/active Organization chain and ownership remain authoritative |
| Ordered repository bootstrap documents | PROJECT_CONTEXT, CURRENT_STATE and CURRENT_SPRINT were inspected; later ratified records govern where historical summaries lag |

The bounded AUTH-POLICY-001 clarification issued by Architecture Authority on 2026-09-08 local is recorded in section 9.4 for T-03 only. It does not ratify this ADR or amend authority outside Package B.

Source proposal acceptance on 2026-09-08 is historical authority for its design input, not an acceptance date or signature for this ADR. Its terminal ACCEPT does not constitute this ADR's independent review. The published ADR received ACCEPT WITH AMENDMENTS; independent review of these corrections is PENDING and the future authority act remains unrecorded.

### 1.4 Closed evaluation-mode terminology transfer

The five names used in this ADR are exactly `descriptive_query`, `session_create`, `session_authenticate`, `command_authorization` and `deterministic_local`, as required by the current drafting instruction. The accepted proposal called the second, third and fifth modes `session_creation`, `session_authentication` and `deterministic_local_test`, respectively. This is an explicit documentary name mapping only: all five protocols, lock lifetimes, freshness, persistence and permission limits in §9.1.1 are preserved. It authorizes no runtime rename, compatibility alias or additional sixth mode. Unknown modes fail closed.

## 2. Physical discovery and integration surface

Paths in this section are relative to the repository root. `S/` means `apps/api/src/yarvis_api/`; `T/` means `apps/api/tests/`. These aliases identify existing physical paths, not packages to be created.

### 2.1 Canonical models, clocks and persistence

| Existing path and symbol | Observed behavior and implication |
| --- | --- |
| `S/models/principal.py`: `Principal` | UUID identity, unique `external_subject`, active/disabled status, optional `person_id` with SET NULL FK; no authority revision |
| Same: `PrincipalMembership` | `principal_memberships`; UUID ID; RESTRICT Principal/Organization FKs; unique Principal/Organization pair; one non-null `role` String(64); active/revoked status and consistent `revoked_at`; no authority revision or temporal assignment |
| Same: `PrincipalMembershipCommand` | Existing membership receipt, Organization/idempotency-key uniqueness and fingerprint; activation/revocation replay resolves current Membership rather than an immutable original success result |
| `S/models/organization.py`: `Organization` | Organization status controls authority; names and organization type are not the proposed authority-revision material fields |
| `S/models/base.py`: `TimestampedUUIDMixin` | UUID and created/updated timestamps using database `func.now()` defaults/update behavior; not a fresh temporal-authority clock |
| `S/models/productive_auth.py`: `ProductiveSession` | Canonical identity FKs, token/CSRF hashes, idle/absolute deadlines, last-seen and terminal state/revocation fields; no permission authority or revision snapshots |
| `S/database.py`: `get_db`, `legacy_session` | Legacy Session lifecycle; not the Dispatcher command transaction policy |
| `S/persistence/unit_of_work.py` | Single-owner commit/rollback; failed commit must retain its primary exception during cleanup |
| `S/models/__init__.py`, `apps/api/migrations/env.py` | Model import surface supplies migration metadata; a model file alone is not composed |

Membership originated in `apps/api/migrations/versions/20260806_32_principal_membership_foundation.py`, revision `20260806_32`, parent `20260806_31`. Productive sessions originated in `apps/api/migrations/versions/20260820_42_productive_identity_sessions.py`, revision `20260820_42`, parent `20260819_41`. Current head is revision `20260823_47`. The new schema must use explicit timezone-aware PostgreSQL timestamps; implicit ORM datetime typing is not proof of a matching database type. Existing application `utc_now()` and session expiration support wall-clock authentication behavior, but cannot substitute for the protected PostgreSQL clock required here.

### 2.2 Complete productive `permissions_for_role(...)` call-site list

`S/application/authority.py` owns `ROLE_PERMISSIONS`, `permissions_for_role` and the frozen `IdentityAuthorityEnvelope`. The temporary role is absent at the baseline. `netpay_operations_operator` has exactly the four Master/Inbox permissions. Unknown roles raise authorization denial. Envelope permission checks currently inspect a permission snapshot.

| Existing caller | Baseline location | Required conceptual integration |
| --- | --- | --- |
| `AuthorityResolutionService.resolve` | `S/services/authority_resolution.py:41` | Use the shared canonical temporal resolver |
| `ProductiveSessionService.create` | `S/services/productive_auth.py:138` | Resolve fresh canonical authority under login serialization, record invalidation snapshots |
| `ProductiveSessionService.authenticate` | `S/services/productive_auth.py:197` | Re-resolve authority and validate session snapshots/deadlines; do not trust stored permissions |
| `grant_bootstrap_membership` | `S/services/governance_authority.py:151` | Replace role-recognition-as-validation with the separate bootstrap assignment allowlist |

These are the four productive calls, including the bootstrap validator even though it does not construct the final permission envelope. Tests and the function definition are not additional productive calls. Adding a temporal service without migrating all three authority constructors and the fourth assignment validator leaves an unsafe intermediate design.

### 2.3 Imports, consumers and composition

`S/api/dependencies/authority.py:authority_envelope` selects `ProductiveSessionService.authenticate` for productive identity or `AuthorityResolutionService.resolve` for the other supported authority path. Permission-consuming dependencies reach Governance, Radar, NetPay Master, NetPay Inbox and NetPay Data routes. `S/api/routes/auth.py` calls session creation at callback and authentication for current session/capabilities; logout explicitly owns its commit.

Direct resolver wrappers also exist in route modules `document_registry` (`_resolved_document_principal`), `intake` (`_resolved_intake_principal`), `mission_inbox` (`_resolved_mission_inbox_principal`), `mission_work` (`_resolved_mission_work_principal`), `operational_economics` (`_principal`), `operational_task` (`_p`), `operational_workspace`, `process` (`_principal`) and `process_runtime` (`_principal`). They consume the central resolver, so they require regression coverage even where no direct file edit is proposed. `S/application/netpay_inbox_authority.py:netpay_inbox_envelope` intersects Inbox scopes; it must remain non-escalating.

`S/bootstrap.py:create_app`/`register_routes` compose the application; `main` delegates to that bootstrap. Default dispatcher composition includes the dispatch-mechanics probe, not operational Package B handlers. `S/dispatch/dispatcher.py` supplies the active Session to handler factories. `S/dispatch/models.py:CommandEnvelope` has contract ID and payload; it is not itself trusted actor authentication or proof of operational assignment authority. No generic authenticated command provider is assumed to exist.

### 2.4 Writers, session behavior and evidence precedents

| Existing writer/path | Finding and required containment |
| --- | --- |
| `S/services/governance_authority.py:activate_membership` | No closed role-assignment validation at baseline; validate before receipt replay and writes |
| Same: `grant_bootstrap_membership` | Static role lookup is currently a validator; known must no longer imply assignable |
| Same: `revoke_membership` | Membership/session mutation lacks the proposed common Principal serialization; align affected authority/session writers |
| `S/api/routes/governance.py:MembershipActivation` | Baseline string-length validation permits arbitrary role strings; generic write schema and service require independent allowlist guards |
| `S/services/founder_bootstrap.py:FounderBootstrapAuthorizationService` | `_ROLES` already contains only `netpay_operations_operator`; preserve and validate enrollment/replay, including downstream bootstrap call |
| `S/local_netpay_authority.py:provision_local_netpay_operator` | Local/test-only base-role provisioning with its own transaction and no overwrite; retain closed base-only behavior |
| `S/services/identity_provisioning.py:link_principal_to_person` | Material Principal update without the new revision mechanism; database trigger covers this writer, lock/CAS compatibility needs evidence |
| Organization routes, first-Organization provisioning and `S/seed.py:main` | Organization creation paths exist; no discovered productive Principal/Organization status-update service; database revisions must cover future writers too. Seed creates Organization, not temporary assignments |
| `S/services/productive_auth.py:create` | Locks Principal, checks unique active Membership and active Organization, creates session/evidence; caller commits |
| Same: `authenticate` | Expiry or canonical-invalidity paths currently commit internally before raising; cannot be called inside a Package B Command |
| Same: `revoke`, `logout`, cleanup | `revoke` prepares state/Event/audit without commit; logout route commits; cleanup is not a temporal-role scheduler |
| `S/api/routes/auth.py` callback | Multiple deliberate legacy transaction boundaries around attempt consumption/provider interaction; B does not redefine the entire callback as one Command |

Existing receipts, Events and authentication-security audit establish patterns, not authority. `IC-IDENTITY-EVT-005` already expresses productive-session revocation. Existing Membership revocation and session-service revocation do not use identical audit paths; the participant must converge on one evidence transition without duplicates. Radar/Master receipt savepoints and ArchiveDocument's separate UoW are not precedents that override ADR-017. No second UoW, savepoint, independent transaction, nested dispatch, background task or alternate outbox is permitted for a B Command. State, receipt, result, Events and audit remain in the same Dispatcher-owned transaction; none may be diverted to an alternate persistence path.

The discovered Governance activation, bootstrap grant and revocation functions use a caller-supplied legacy Session, not Dispatcher-owned Commands. Activation/grant read canonical rows without the proposed common lock chain; Governance HTTP handlers commit their results. Founder enrollment locks its receipt/handoff and its CLI owns commit; local provisioning owns `db.begin()`. `IdentityProvisioningService.link_principal_to_person` changes `person_id` without the proposed CAS/common lock chain and leaves commit to its caller; no productive route for that method was found. `S/api/routes/organizations.py:create_organization` commits its creation; `S/services/first_organization.py` uses an advisory exclusion for first creation with caller-owned commit; seed owns its creation transaction. These differences motivate database revision coverage across writers and explicit lock-order integration rather than assuming every writer already follows ADR-017. No role-version safety claim relies solely on Python instrumentation.

Existing tests relevant to the change are enumerated as existing paths in §13. Additional consumer regression must cover the dependency and wrapper graph above, not just textual role matches. No tests or migrations were executed to draft this Proposed ADR.

## 3. Alternatives considered and selected recommendation

| Alternative | Risk or failure | Disposition |
| --- | --- | --- |
| Temporary role string or static map grants Intake | Cannot prove assignment, review, expiry or revocation | Rejected; static lookup always excludes Intake |
| Temporal columns only on Membership | Conflates physical role and historical assignment lifecycle; complicates independent receipts/review/restoration | Not selected; preserve single role and separate canonical entity |
| Session/cookie permission snapshot | Stale authority survives review deadline or revocation | Rejected; snapshots only invalidate, fresh canonical resolution grants |
| Audit-derived assignment | Logs become an authority database and absence of closure appears active | Rejected; audit is evidence only |
| Scheduler or physical role restoration gates expiry | Delayed or failed job prolongs Intake | Rejected; temporal denial is evaluated synchronously |
| Application-maintained Membership-only version | Misses other writers, Principal/Organization changes and time | Replaced with four PostgreSQL revisions plus separate time evaluation |
| Single revoke-and-restore Command | Failed CAS restoration rolls back revocation | Replaced with separate Revoke and Reconcile Commands |
| Canonical assignment plus fresh resolver, revisions, independent revocation and bounded Identity participant | Larger integration boundary and real PostgreSQL concurrency evidence required | Recommended corrected design |

The selected design preserves the accepted single-role model and distinguishes canonical temporal authority, static base permission recognition, operational assignment admission, session continuity and historical evidence. All alternatives admitted for future consideration must preserve §4; no rejected alternative is an implementation option under this Proposed ADR.

## 4. Mandatory authority invariants and assignment guards

Let **B** be exactly `netpay.master.read`, `netpay.master.manage`, `netpay.inbox.read`, `netpay.inbox.manage`. Let **I** be exactly `netpay.intake.read`, `netpay.intake.connect`, `netpay.intake.review`, as allocated by ADR-019. No additional permission is inferred by this notation.

`permissions_for_role(role)` in isolation never grants any `netpay.intake.*` permission. The static map for `netpay_intake_pilot_operator` contains B only. Intake can appear only through a unique coherent canonical assignment, with valid covered identity chain/revisions, active time interval, timely human review when required, and no revocation or terminal closure. A role string is not temporal authority. Expiry/revocation denies I on the next protected evaluation without depending on physical restoration. B remains available to the valid canonical identity; a revoked session cannot continue using it.

Three distinct policies must exist:

1. `ROLE_PERMISSIONS`: recognized static role to static permissions. Recognition is not assignment authorization.
2. `GENERIC_MEMBERSHIP_ACTIVATION_ROLES`: an explicit frozen allowlist of baseline generic roles, reviewed against the current map. Do not derive it from dictionary keys or dynamic subtraction of the temporary role.
3. The dedicated Assign Command: the only application path allowed to perform the base-to-temporary transition, inside its UoW, locks, CAS, receipt and separately authorized admission.

`activate_membership` must validate its allowlist before both replay and mutation. `grant_bootstrap_membership` must use a separate bootstrap allowlist containing the base operator, not `permissions_for_role` as admission. Founder Bootstrap retains its existing base-only `_ROLES`, with enrollment/replay guard coverage. Local provisioning retains its local/test restriction, exact base role and no-overwrite guard. Generic write schemas/endpoints reject the temporary role; read schemas may represent it. Seed cannot create assignments or call the dedicated operation. Bootstrap/default composition cannot silently add an executable grant path. Unknown roles fail closed. Direct administrative SQL is outside Python guard guarantees and must be contained by verified database privileges.

For Revoke, canonical revocation, affected-session invalidation, receipt, Domain Events and definitive local AuthenticationSecurityAudit share the sole owning transaction. Confirmed rollback is not durable denial; an uncertain result is not completion. No external audit delivery is required. Section 9.4 applies without reducing AUTH-POLICY-001 sections 10-12.

No intermediate default composition may grant I. The four productive call sites and all indirect consumers must migrate coherently. No real assignment, seed or assignment backfill is part of B.

## 5. Proposed data model and database constraints

### 5.1 Ownership and identity

Governance owns `TemporaryRoleAssignment` and `TemporaryRoleCommandReceipt`. Identity owns Principal and productive-session state. Membership retains exactly one physical `role`; there is no parallel effective-role column or editable permission set. Organization remains the canonical scope.

`TemporaryRoleAssignment` links UUID `id`, `membership_id`, `principal_id`, `organization_id`. A composite FK `(membership_id, principal_id, organization_id)` references the matching Membership triple; the referenced table needs the corresponding unique candidate key. Independent FKs alone do not prove this correspondence. Identity/role/initial binding fields are immutable. History is preserved; cascading deletion of assignment evidence is prohibited.

### 5.2 Assignment field inventory

| Fields | Meaning and constraints |
| --- | --- |
| `id`, `membership_id`, `principal_id`, `organization_id` | UUID identity and composite canonical relationship; immutable |
| `prior_role`, `temporary_role` | Immutable exact `netpay_operations_operator` and `netpay_intake_pilot_operator`; no caller-defined alternate roles |
| `starts_at`, `review_due_at`, `expires_at` | Immutable finite UTC timestamptz values; start generated under lock, due at start plus exactly 336 hours, expiry strictly after start and at most start plus exactly 720 hours |
| `status` | Closed persistent state set from §7; transitions cannot reopen a terminal assignment |
| `authority_revision` | Independent PostgreSQL-maintained positive revision, not an application-controlled version |
| `bound_principal_revision`, `bound_organization_revision`, `bound_membership_revision` | Immutable canonical revision bindings; grant captures Membership revision after the physical role transition; never rebase to repair or renew authority |
| `assigned_by_principal_id`, `assignment_authority_reference` | Trusted actor and immutable structured assignment reference |
| `reviewed_at`, `reviewed_by_principal_id`, `review_authority_reference` | Nullable together until one timely human review; complete together when recorded and then immutable; not a renewal |
| `revoked_at`, `revoked_by_principal_id`, `revocation_reason_code`, `revocation_authority_reference` | Consistent revocation block; immutable once recorded; actor/reference required for explicit revocation |
| `closed_effective_at`, `closed_recorded_at`, `closure_reason_code` | Terminal fact's effective instant, later observation instant and closed reason; do not backdate observation |
| `restored_at`, `restored_by_principal_id`, `restoration_authority_reference`, `restored_membership_revision` | Separate successful physical restoration evidence; nullable until terminal, coherent CAS restoration; immutable once recorded |
| `created_at`, `updated_at` | Explicit timezone-aware structural timestamps, not authorization samples |
| Command, correlation and causation references | Safe trace references linked to the transition and receipt; not permission-bearing fields |

Column representations for bounded opaque text and trace references must be made explicit in a later authorized schema review. This Proposed ADR does not invent numeric bounds or authority channels absent from the corrected design.

Required checks include positive revisions, closed statuses/reasons, role constants, timestamp finiteness and ordering, all-or-none transition blocks, state/block coherence, terminal-only restoration, and non-reopening transitions. Review must be within the original interval and strictly before its due time; database row checks complement, not replace, the final protected command-time check. An expiry earlier than day 14 is allowed; it does not create an obligation or opportunity to review after expiry.

The exclusion is a partial **UNIQUE (`membership_id`) WHERE `restored_at IS NULL`**, including revoked, expired and review-missed rows. A terminal row without restoration grants no I and blocks another grant. Never restrict uniqueness only to active statuses. Historical restored rows remain history and are not competing outstanding assignments.

### 5.2.1 Normative invariant-to-mechanism matrix

| Invariant | Required mechanism | Scope and limitation |
| --- | --- | --- |
| Required identity, scope, role, interval, status, revision and receipt-key fields | Explicit NOT NULL | A nullable expression is not accepted as validated without an explicit NOT NULL requirement; optional transition blocks instead use explicit IS NULL/IS NOT NULL predicates |
| Positive revisions, finite timestamps, closed row states/reasons, role constants, interval bounds | Deterministic same-row CHECK, plus NOT NULL for required operands | No CHECK consults another row or derives validity from current time; 336/720-hour arithmetic is independent of connection TimeZone |
| Review/revocation/closure/restoration blocks all-or-none and coherent with row status | Deterministic same-row CHECK with explicit null predicates | State/block consistency is distinct from whether the transition was authorized |
| Assignment belongs to the exact Membership/Principal/Organization triple | Composite FK | Membership supplies a referencable UNIQUE key on (id, principal_id, organization_id); required FK columns are NOT NULL |
| Canonical IDs and receipt Organization/contract/idempotency-key uniqueness | Primary/UNIQUE keys and required FKs | Receipt keys cannot be nullable; fingerprint comparison remains part of the Command |
| At most one unrestored Assignment per Membership, including terminal rows | Unique partial index on membership_id WHERE restored_at IS NULL | Not an ordinary UNIQUE table constraint with a WHERE clause; no status-only exclusion |
| Immutable IDs, roles, validity interval, bound revisions and recorded transition blocks | OLD/NEW trigger | Reject forbidden changes, rather than merely incrementing revision |
| Revision 1 on INSERT; material increment, no-op preservation, null-safe comparison, manual override containment and overflow rejection | BEFORE INSERT/UPDATE OLD/NEW trigger | Writer cannot select revision; invalid OLD or overflow fails; database privileges remain an explicit limitation |
| Closed allowed transitions and no terminal reopening | OLD/NEW transition validation in trigger, plus Command validation | A same-row CHECK alone cannot compare previous and new state |
| Actual active P/O/M chain, matching current role and bound revisions; actor/target scope | Protected reads inside the Command or protected resolver mode | A CHECK cannot establish the current contents of another row; fresh snapshots are reread after waits |
| Restoration of exact prior base role and recording restored Membership revision | Protected reads and CAS inside the Command | Unexpected role/status/revision is not overwritten; role and restoration evidence share the same transaction |
| Current grant/review/expiry/review-missed eligibility | Runtime temporal evaluation using fresh clock_timestamp() | No clock-dependent CHECK represents automatic expiry or review-missed denial |
| Historical assignment/receipt preservation | Restrictive FKs, immutable recorded blocks and authorized writer/privilege restrictions | No cascading history deletion; DELETE/DDL/restore privileges require separate verification and are not covered by revision triggers alone |
| One terminal session transition and its corresponding evidence | Protected reread or equivalent conditional UPDATE, applicable uniqueness constraints and the owner's transaction | Only the writer that actually transitions active to terminal records the corresponding Event/audit; no broader exactly-once claim |

No CHECK consults other rows. Coherence with Membership's current role/revision requires protected reading; restoration requires CAS. All cross-row, transition and runtime obligations remain distinct from static DDL checks. DDL conformance must demonstrate each row of this matrix, including rejected NULL combinations and the composite FK's referencable key.

### 5.3 Command receipt

`TemporaryRoleCommandReceipt` is separate from the legacy Membership receipt. It has an immutable command identity and Organization/contract/idempotency-key uniqueness, canonical versioned input fingerprint, target and trusted actor references, expected/observed/result revision references, successful original result, event references, correlation/causation and recording time. The fingerprint includes functional inputs, expected revisions and the canonical authority-reference digest. It does not depend on incidental serialization order.

Only a successful atomic command writes a success receipt and its original result. Same key and same fingerprint replays that immutable result after current admission checks; a different fingerprint conflicts. A replay never reapplies role assignment, extends time, repeats review, restores again or duplicates evidence. Legacy replay semantics are not reinterpreted. Receipt lookup cannot bypass current actor/target authority. Uncertain commit acknowledgment is not an invitation to open a second UoW.

The handler expresses exactly one commit through the received `CommandUnitOfWork` facade immediately after the final authorization gate. It never calls `Session.commit()` directly or creates another UoW. Resolver, services, repositories and the Identity participant perform no commit or rollback. Dispatcher and UnitOfWork retain transaction ownership, terminal-state validation and cleanup under ADR-017. Receipt, successful result, state (including canonical revocation and affected-session invalidation), Domain Events and definitive local AuthenticationSecurityAudit are committed by this one facade invocation; the primary exception remains preserved on failure.

### 5.4 ProductiveSession invalidation snapshots

Proposed snapshots identify Principal/Organization/Membership revisions, nullable assignment ID/revision, authority profile (`base_only` or `temporary`) and the next temporal deadline. They contain no permission set as authority. Missing snapshots on pre-change sessions require new authentication; no historical authority backfill is inferred.

For an unreviewed temporary session the deadline is the earlier of review due and expiry; for a timely reviewed assignment it is expiry. Review invalidates affected sessions; it does not silently extend an existing session. A fresh base-only session after terminalization may use B. Old terminal history alone must not cause that fresh session to be revoked repeatedly; a later material restoration transition may invalidate it once.

## 6. PostgreSQL-maintained authority revisions

The authorization vector covers Principal, Organization, Membership and Assignment. Time is evaluated separately. Identity Binding is outside this vector; the design does not claim to cover all authentication or all identity-binding changes.

| Entity | Exact material fields | Non-material fields |
| --- | --- | --- |
| Principal | `external_subject`, `status`, `person_id` | `created_at`, `updated_at`; immutable ID is rejected on change |
| Organization | `status` | Names, `organization_type`, `created_at`, `updated_at`; immutable ID is rejected on change |
| Membership | `principal_id`, `organization_id`, `role`, `status`, `revoked_at` | `created_at`, `updated_at`; immutable ID is rejected on change |
| TemporaryRoleAssignment | Identity/link fields; `prior_role`, `temporary_role`; `starts_at`, `review_due_at`, `expires_at`; `status`; all three bound revisions; assignment actor/reference; review block; revocation block; closure block; restoration block listed in §5.2 | `created_at`, `updated_at`, technical command/correlation/causation references; `authority_revision` is trigger-owned, not a material input |

Immutable material fields are integrity inputs, not permission to update them. Recorded authority-reference blocks remain immutable even though changing them would be material.

For avoidance of doubt, Assignment's expanded material list is `id`, `membership_id`, `principal_id`, `organization_id`, `prior_role`, `temporary_role`, `starts_at`, `review_due_at`, `expires_at`, `status`, `bound_principal_revision`, `bound_organization_revision`, `bound_membership_revision`, `assigned_by_principal_id`, `assignment_authority_reference`, `reviewed_at`, `reviewed_by_principal_id`, `review_authority_reference`, `revoked_at`, `revoked_by_principal_id`, `revocation_reason_code`, `revocation_authority_reference`, `closed_effective_at`, `closed_recorded_at`, `closure_reason_code`, `restored_at`, `restored_by_principal_id`, `restoration_authority_reference`, `restored_membership_revision`. Immutable-ID and immutable-block checks reject changes rather than legitimizing them by incrementing a revision.

Four proposed `BEFORE INSERT OR UPDATE FOR EACH ROW` triggers:

| Entity | Trigger |
| --- | --- |
| Principal | `trg_principals_authority_revision` |
| Organization | `trg_organizations_authority_revision` |
| Membership | `trg_principal_memberships_authority_revision` |
| TemporaryRoleAssignment | `trg_temporary_role_assignments_authority_revision` |

On INSERT each trigger imposes revision **1**; a writer cannot choose its value. On UPDATE it validates OLD revision, rejects invalid/nonpositive values, overflow and immutable changes, compares real OLD/NEW material values using null-safe comparisons, and sets NEW revision to OLD plus one if any material value changed, otherwise to OLD. It overwrites attempts to choose an arbitrary NEW revision. Listing a column in SET is not evidence that its value changed. A no-op update does not advance authority. Multiple material updates in one Command may advance more than once; consumers use the actual post-flush database revision.

Triggers perform no session invalidation, permission lookup, audit or command dispatch. Existing rows receive structural epoch revision 1; this is not reconstruction of historical authority and not assignment backfill. FK-induced updates must receive the same material comparison coverage.

This mechanism does not protect against DBA/DDL privileges, disabled triggers, database restore or privileged external writers. The application-role privilege model and trigger enablement require evidence before implementation conformance. An assignment's own revision is compared against the operation/session expectation; comparing it to a copy of itself proves nothing.

## 7. States, transitions and complete permission precedence

Persistent states are `active_unreviewed`, `active_reviewed`, `revoked`, `expired`, `review_missed`. Derived observations such as scheduled, invalid, ambiguous and stale are not extra permissive stored states. Assign never creates a future scheduled grant.

| Command or observation | Allowed transition | Physical role and evidence |
| --- | --- | --- |
| Assign | No outstanding assignment to `active_unreviewed` | CAS base to temporary; bind post-change Membership revision; revoke affected sessions; receipt/Event/audit |
| Review | `active_unreviewed` to `active_reviewed` before due and expiry | Record one timely human review; no role or interval extension; invalidate sessions |
| Revoke | Revocable nonterminal assignment to `revoked` | Commit revocation and invalidation; do not restore role in this Command |
| Time evaluation | Unreviewed past due or any assignment past expiry loses I immediately | No durable transition is assumed from a read; no Event is required to deny |
| Reconcile | Materialize `review_missed` or `expired`, or retain committed `revoked`; restore terminal assignment by CAS | Record effective/observed closure and separate restoration; invalidate affected active sessions once |
| Replay | Original successful result only | No transition repeated; current admission still applies |

Terminal states never return to active. Same-key revoke replay succeeds with its original result; a different-key request cannot rewrite terminal history. Reconcile never changes a revoked fact into an active or alternative historical fact. No extension, renewal or reactivation operation exists.

Let **C** mean fresh, healthy SQL reads prove the active Principal, unique selected active Membership, active Organization, matching canonical IDs/scope and a valid canonical clock. The following precedence is normative: first applicable row wins.

| Priority | Canonical/physical/assignment condition | Entitlement result |
| --- | --- | --- |
| 1 | C cannot be established; repository, PostgreSQL, authoritative reads or clock unavailable; aborted SQL transaction | No permissions; controlled denial/unavailability; no fallback queries in aborted transaction |
| 2 | C valid, physical role unknown | No permissions |
| 3 | C valid, another recognized non-temporary role | Its static permissions, never I |
| 4 | C valid, physical role is exact base operator | Exactly B, regardless of assignment history; assignment cannot upgrade base role |
| 5 | C valid, physical role temporary, outstanding assignment absent | Exactly B |
| 6 | C valid, temporary role, duplicate outstanding assignments, semantically invalid or safely decoded illegible assignment | Exactly B, closed invalid/ambiguous reason; never select the latest row |
| 7 | C valid, temporary role, terminal assignment or nonterminal row with revocation/closure inconsistency | Exactly B |
| 8 | C valid, temporary role, bound revisions stale or operation assignment expectation mismatched | Exactly B for entitlement; a mutating operation also fails its concurrency check |
| 9 | C valid, temporary role, active row marked restored or inconsistent identity/role/time/review blocks | Exactly B |
| 10 | C valid, coherent temporary assignment but t before start or t at/after expiry | Exactly B |
| 11 | C valid, review claimed but invalid, incomplete or late | Exactly B |
| 12 | C valid, unique coherent `active_unreviewed`, start at/before t and t strictly before both due and expiry | Exactly B plus exactly I |
| 13 | C valid, unique `active_unreviewed`, t at/after review due without timely committed review | Exactly B |
| 14 | C valid, unique coherent `active_reviewed`, timely review, start at/before t and t strictly before expiry | Exactly B plus exactly I |
| 15 | Any other temporal inconsistency with C still proven | Exactly B |

The matrix determines canonical entitlement, not permission to continue a revoked productive session. A session requiring invalidation is denied and requires new authentication even where the identity could subsequently obtain B. A driver/database failure is not the safely decoded illegible-data case in row 6. Section 9.4 distinguishes local persistence failure from a subsequent non-canonical audit outage; neither audit delivery nor a new health vector supplies authority.

## 8. Temporal policy and commit semantics

Upon subsequent explicit architectural ratification, this ADR prospectively specifies ADR-019 §7.2's day-based temporal wording for Package B: review due is exactly 336 absolute elapsed hours from starts_at; maximum expiry is 720 absolute elapsed hours from starts_at. No calendar-day arithmetic, local zone, connection TimeZone or DST determines those durations. This precision creates no retroactive change, historical authority, extension or assignment. It is not effective ratification while this ADR remains Proposed. The UTC, non-DST, DST-start and DST-end evidence in §14 remains mandatory.

Use fresh PostgreSQL `clock_timestamp()` samples. `now()`, `CURRENT_TIMESTAMP` and `transaction_timestamp()` return transaction-start time, which can be stale after waiting for locks; `statement_timestamp()` is also not the chosen evaluation clock. All relevant values must be finite timezone-aware UTC timestamps. See [PostgreSQL current date/time functions](https://www.postgresql.org/docs/16/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT).

`starts_at = t0` is generated after protected grant locks, not accepted as a caller's future or backdated value. Fourteen days means exactly 336 hours; thirty days means exactly 720 hours. `review_due_at = t0 + 336 hours`; `t0 < expires_at <= t0 + 720 hours`. Calculate deadlines with hour intervals or equivalent arithmetic on instants, independently of the connection's TimeZone. Do not rely solely on SET TIME ZONE 'UTC', or on calendar-day interval addition in the connection's zone. The authorized duration can be shorter. The interval is `starts_at <= t < expires_at`. Review is valid only when the last protected evaluation has `t < review_due_at` and `t < expires_at`. At the exact due boundary, absent a timely committed review, Intake is denied. At the exact expiry boundary, Intake is denied. There is no grace period or retry-induced deadline movement. Fresh current-time samples still use clock_timestamp().

Commands take fresh samples after locks, before effects, and after flush. The sequence is: authoritative reread and validation; prepare transition/receipt/result/Event/audit in the same Session; flush; fresh snapshots and time; transition-specific final gate; exactly one handler call to the received CommandUnitOfWork commit facade. The **last protected evaluation immediately before that facade call is the authorization/linearization point**. No further business mutation occurs after that gate. No direct Session.commit(), service/repository/participant commit, second UoW or nested Dispatch is permitted. Review's staged `reviewed_at` cannot substitute for a timely final evaluation. Revoke's final gate validates the revocation transition, not a requirement that the now-revoked row still be active.

A successful commit finishing after a deadline retains the ordering established by its timely protected linearization point. This does not demonstrate the exact physical instant of durability or promise wall-clock atomicity at the boundary. Future Intake Commands must use the same fresh evaluation inside their own UoW before effects and at their final gate; a previously issued envelope is insufficient.

For closure observation, `closed_effective_at` records the applicable deadline and `closed_recorded_at` records later observation. If review-missed and expiry are both observed, the first violated deadline is the primary closure reason; an exact tie uses expiry. Already recorded terminal history is not rewritten.

Invalid/nonfinite/unavailable clock samples deny all authority. An observed backward movement within one operation denies; the design does not claim to detect every system-clock rollback across operations. Stored terminal state never reopens because time moved backward. No local-clock fallback is allowed.

With confirmed rollback, the operation leaves no durable revocation, session invalidation, successful receipt, Event or required audit record: canonical state remains as before the operation. Preserve the primary exception; cleanup cannot replace it and success must never be reported. Lost commit acknowledgment produces **UNCERTAIN_RESULT**, not proven rollback or success. Resolve it through readback, idempotency and receipt in a later independently admitted operation, never a second UoW in the original Command. Evaluations unable to prove canonical authority fail closed; that is not proof of committed revocation. An aborted attempt creates no durable cross-replica denial signal. Section 9.4 governs the distinction from subsequent audit outage.

Expiry/review-missed denial does not depend on a scheduler. Later reconciliation records the fact and restores via CAS. Absence of an Event is never evidence that authority remains active. No scheduler or worker is authorized.

## 9. Resolver and Identity session participant

### 9.1 Shared resolver contract

The conceptual interface accepts the caller's active Session, trusted Identity context, optional Organization selector, optional expected Membership ID and evaluation mode. Dependencies are a canonical repository, PostgreSQL authority clock, static policy and pure temporal evaluator. Trusted identity is server-owned authenticated or deterministic context; caller-supplied headers, cookies, frontend state, arbitrary payload actor IDs and `CommandEnvelope` alone are not that context.

Return `AuthorityResolution`: safe authority envelope, canonical IDs, actual revision vector, assignment reference/revision when applicable, evaluation time, next deadline and closed reason. Permission values are derived results, not durable authority. Query evidence is safe read output, not a new write requirement. Required durable command evidence participates in the caller's transaction.

`AuthorityResolutionService.resolve`, `ProductiveSessionService.create` and `authenticate` conceptually delegate to this shared core. Bootstrap assignment uses the separate guard, not the resolver as assignability proof. Read fresh scalar snapshots after waits and after flush; do not trust discovery ORM objects. Avoid refresh/populate-existing behavior that can discard a caller's pending changes. Recheck the caller's own flushed state without overwriting pending values.

The core has no commit, rollback, audit-derived authority or session factory. Existing HTTP wrappers retain explicit transaction ownership. B uses a separate commit-free abstraction rather than calling legacy `authenticate()` from command handlers. This does not authorize a broad rewrite of all legacy/OIDC transactions.

### 9.1.1 Closed evaluation-mode protocols

The closed proposed modes are `descriptive_query`, `session_create`, `session_authenticate`, `command_authorization` and `deterministic_local`. Unknown modes fail closed. A fresh query alone does not imply a protected authorization chain under READ COMMITTED.

| evaluation_mode | Locks and fresh reads | Validity duration | Can grant Intake? | Persistence and reuse |
| --- | --- | --- | --- | --- |
| descriptive_query | Read P/O/M/A in one coherent statement snapshot under READ COMMITTED, with an explicit observation time; no row locks or authorization lock lifetime are claimed | Describes only its observed snapshot | No executable permission grant; may describe temporal eligibility as data | Safe descriptive output may be retained as evidence, never as authority; later operations resolve again in their own transaction |
| session_create | Share the global lock protocol with authority writers: Principal exclusive; Organization protection against status changes; protected Membership/Assignment reads; sessions in UUID order. Reread P/O/M/A after every wait and before the final creation gate | Protection retained until the caller-owned session-creation commit | Only from a unique valid canonical assignment at protected evaluation; no permission set is stored as authority | Persist only invalidation IDs/revisions/profile/deadline. Session creation does not authorize a later effect; subsequent requests re-resolve |
| session_authenticate | Validate session, canonical IDs, P/O/M/A and invalidation snapshots through authoritative fresh reads under the shared ordered protection. Coordinate with all terminal writers; reread after waits and before producing authority | Envelope valid only in the producing request/transaction, while its protection and temporal predicate hold; never beyond its deadline or transaction end | Yes, only while canonical assignment and session remain valid under the complete matrix | Persist only permitted session/invalidation changes through the legacy owner; resolver never commits. Do not cache or reuse the envelope in a later request or Command |
| command_authorization | Operate in Dispatcher UoW; lock and reread P/O/M/A in global order, including trusted actor/target dependencies. Revalidate after waits and after flush, with a fresh final temporal sample; retain locks through commit | Only this Command and its final protected authorization point | Yes, only through the full canonical temporal predicate; old envelopes cannot replace it | Persist state/result/receipt/evidence in this UoW through exactly one handler facade commit. Stored result is not permission authority for another operation |
| deterministic_local | Retain existing deterministic Identity validation; request headers alone are not authority. Synthetic grants use the same protected reads, clock and lock protocol as the operation being tested; identify the covered operation explicitly | Only the isolated test/local request transaction; no production validity | Only with an explicit synthetic canonical assignment in the isolated test; no role/header-only grant and no implicit local Intake | Synthetic invalidation/evidence only in the isolated fixture transaction; no production persistence, permission backfill or altered productive semantics |

Each mode that can grant Intake protects P/O/M/A through its authorization evaluation. A caller that will perform effects in another transaction must select command_authorization there rather than reuse a session/query envelope. The authentication wrapper retains protection until its owning transaction ends; time must still be reevaluated before protected effects. Required durable invalidation is performed by the appropriate owner/participant, never by committing inside the resolver. Descriptive output cannot be passed as a trusted executable envelope. No mode changes the existing productive authentication or Identity Binding requirements. All five modes apply section 9.4: no external audit-delivery prerequisite or additional health vector; unavailable canonical proof denies evaluation without inventing durable revocation. General AUTH-POLICY-001 sections 10-12 obligations remain intact.

### 9.2 Closed failures and responsibilities

These are proposed closed local reasons carried through compatible existing error envelopes, not newly registered global contracts.

| Reason | Required behavior |
| --- | --- |
| `CANONICAL_AUTHORITY_UNAVAILABLE` | No proven canonical chain; total denial/unavailability |
| `TEMPORAL_SOURCE_UNAVAILABLE` | Required repository/clock unavailable; total denial, never static fallback |
| `TEMPORARY_ASSIGNMENT_INVALID` | B only when C is authoritatively proven in healthy SQL; mutating invalid transitions fail |
| `TEMPORARY_ASSIGNMENT_AMBIGUOUS` | B only when C is proven; never choose a duplicate winner |
| `AUTHORITY_CONCURRENCY_CONFLICT` | Expected revisions, CAS or serialization conflict; no command success/effects committed |
| `AUTHORITY_PERSISTENCE_FAILED` | Abort the Command; preserve primary failure and no partial success |
| `AUTHORITY_COMMIT_FAILED` | Confirmed commit failure; preserve original exception and do not promise later durable audit |
| Existing `UNCERTAIN_RESULT` | Commit outcome not established because acknowledgment was lost; no fabricated success or rollback |

Existing invalid-input, authorization-denied, idempotency-conflict and unavailable envelopes remain applicable; exact schema/profile mappings require explicit later contract review. Do not catch a generic SQL exception and convert it to B. After an invalidating SQL failure, perform no more reads in the aborted Session; the owning UoW handles rollback. A controlled application-level decoder may classify malformed temporal data only after successful authoritative SQL reads establish C.

### 9.3 Identity participant and session policy

`SessionAuthorityInvalidationParticipant.revoke_affected` receives the Command's active Session/UoW and trusted transition context. It locks and rereads affected sessions in UUID order, transitions only active sessions to revoked, records `IC-IDENTITY-EVT-005` and authentication-security audit once per transition, and returns prepared references. It performs no commit, rollback, new Session, savepoint or nested Dispatch, and returns no claim of durable success before the outer commit.

Grant, review that permits authority beyond the review boundary, revoke, review-missed, reconciled expiry and material canonical authority changes invalidate affected productive sessions. Closed classifications are `temporary_role_granted`, `temporary_role_reviewed`, `temporary_role_revoked`, `temporary_role_review_missed`, `temporary_role_expired`, `canonical_authority_changed`. Existing Event reason `authority_changed` can carry the prospectively specified safe classification; the existing Event ID is retained.

Logical deadline/snapshot invalidation denies session use immediately when evaluated. Durable revocation evidence is recorded by an observing owner or reconciliation; it is not guaranteed at the unobserved deadline. AUTH-POLICY-001 §§4–5 remain compatible: retaining canonical B is distinct from session continuity, and new authentication is required. A prospective policy/contract supplement must explicitly enumerate these causes, snapshot profiles and logical-versus-recorded timing; it must not relax the policy. Identity/Governance participation is bounded to this Session, not a general cross-context transaction framework.

### 9.3.1 Terminal-session writer inventory and alignment

Every writer attempting active-to-terminal must lock and reread the session, or use an equivalent conditional transition that identifies whether it actually changed the row. Only that successful transition writer records the corresponding Event and audit in the same owning transaction. Legacy wrappers preserve their commit owner, respect the global lock order, emit no transition evidence for a no-op and never use a stale object as proof. This guarantee is limited to the demonstrated conditional transition, constraints and transaction; it is not an unrestricted exactly-once delivery promise.

| Writer and existing/proposed path | Affected scope and required alignment | Transaction owner |
| --- | --- | --- |
| Proposed SessionAuthorityInvalidationParticipant in S/services/session_authority_invalidation.py | Assignment/Membership changes select all matching membership_id sessions, with canonical Principal/Organization consistency validation; lock/recheck active rows before transition/evidence | Received Command UoW; no participant commit/rollback |
| ProductiveSessionService.logout and revoke in S/services/productive_auth.py; S/api/routes/auth.py wrapper | Selected session; serialize terminal transition, do not re-emit evidence after another winner | Existing HTTP wrapper |
| ProductiveSessionService.authenticate expiry branch in S/services/productive_auth.py | Selected session; fresh deadline and terminal-state reread; preserve expiry classification and its explicitly defined evidence | Existing legacy owner, outside Commands; shared resolver remains commit-free |
| ProductiveSessionService.create session-limit eviction in S/services/productive_auth.py | Principal-scoped candidate sessions, ordered/locked consistently; only actual active-to-terminal victims emit evidence | Session-creation caller |
| revoke_membership in S/services/governance_authority.py; Governance route wrapper | All sessions for the target Membership; common Principal serialization and protected session reread | Existing Governance wrapper, or explicitly authorized Command owner |
| Principal authority loss/change; observing productive_auth path and material writers such as S/services/identity_provisioning.py | All sessions referencing that Principal, not only a selected Membership. No separate productive Principal-status mutation service was found; any later writer must be inventoried and bound before implementation | Actual writer/observing owner; no fabricated service or extra transaction |
| Organization authority loss/change; observing productive_auth path | All sessions referencing that Organization. No productive Organization-status update service was found; discover affected Principal IDs before locks and abort if the required set cannot be protected in order | Actual writer/observing owner; no automatic worker or unapproved Organization route |
| ProductiveAuthCleanupService.run in S/services/productive_auth.py | Retention deletion of already-terminal sessions, not active-to-terminal authority mutation; protect and recheck terminal eligibility, coordinate deletion with logout/revocation and preserve required durable evidence outside deleted session rows | Existing cleanup caller; no new scheduler or commit owner |
| Any additional physical writer found during pre-implementation discovery | Enumerate direct ORM/Core/bulk writes and deletes before the exact phase boundary is accepted; align or stop and amend that boundary | Explicitly identified owner only |

Principal/Organization-wide invalidation must not hold an Organization lock and then discover/acquire earlier-order Principal locks. Discover the complete candidate set first, acquire sorted locks, reread and abort on an incompatible expansion. Material revision/snapshot invalidation denies authority even if recording by a later observer is pending; observing one session is not evidence that every affected session was durably revoked.

### 9.4 T-03 normative clarification and disposition

This section records the clarification issued by Guillermo de Hoyos, Architecture Authority of Yarvis, exclusively for AUTH-POLICY-001 sections 9-10 as applied to ADR-020 Package B. It is a policy clarification, not acceptance or ratification of this ADR. T-03 is **RESOLVED AT DESIGN LEVEL**; implementation evidence and renewed independent review remain pending.

| Clarification field | Recorded value |
| --- | --- |
| Architecture Authority | Guillermo de Hoyos |
| Decision date | 2026-09-08, Architecture Authority local date; not adjusted to UTC or commit time |
| Scope | AUTH-POLICY-001 sections 9-10, exclusively ADR-020 Package B |
| Exceptions | None |
| Downstream authority | None |

#### 9.4.1 Definitive local audit and one transaction

The sanitized PostgreSQL AuthenticationSecurityAudit row, committed in the same Session and sole ADR-017 UnitOfWork as canonical revocation, affected-session invalidation, receipt and Domain Events, is the definitive required audit record for this scope. No export, projection, consumer delivery or external materialization is required for a committed revocation to be locally audited and complete. DomainEvent is corresponding evidence, not a replacement for this explicitly designated AuthenticationSecurityAudit record and never a source of authority.

All these writes commit atomically through the received CommandUnitOfWork facade. Durable revocation without the required local audit record, a successful required audit record without its revocation, and successful receipt/Events after confirmed rollback are prohibited partial states. An exception or uncertain outcome cannot establish completed revocation. Resolver, repositories and the Identity participant neither commit nor create another Session/UoW. No savepoint, autonomous transaction, nested dispatch or improvised post-failure persistence completes the original Command.

Existing S/models/domain_event.py:record_event uses db.add(event) on the received Session. S/services/productive_auth.py:ProductiveSessionService.revoke stages session state, DomainEvent and AuthenticationSecurityAudit in that same Session without its own commit. These are existing atomic-persistence patterns, not an outbox or delivery protocol. The Package B handler/receipt integration and field-complete sanitized audit remain future evidence obligations. AUTH-POLICY-001 section 9 fields, privacy and retention requirements still apply; safe_details must not become an unvalidated substitute for a defined audit profile.

#### 9.4.2 Outage, local failure and uncertain result

For this clarification, audit outage means exclusively unavailability of a subsequent non-canonical export, consumer, projection or destination after the required local audit record has committed. Such an outage does not delay or reverse committed revocation, restore authority or sessions, or make external evidence authoritative. No subsequent delivery is mandatory. No outbox, durable queue, worker, broker or global audit-health authority is required or authorized.

Failure to persist the required local record in the sole transaction is failure of the entire Revoke operation, not completed revocation and not the subsequent audit outage just defined. With confirmed rollback, revocation, affected-session invalidation, receipt, Events and successful audit do not persist; previous canonical state is preserved, the primary exception is reported and success is never reported. Preserving that previous state is neither revocation nor durable denial. Correct the cause and use a subsequent independently admitted operation.

Lost commit acknowledgment is UNCERTAIN_RESULT. Readback, idempotency and receipt resolve it in a later governed operation, never a second UoW within the original Command. While canonical authority cannot be established, evaluations depending on it fail closed. This does not assert that revocation committed, nor turn a client-side uncertain result into global revocation state.

#### 9.4.3 Immediacy, concurrency and five-mode application

"Prioritize denial immediately" means that a valid revocation which successfully commits linearizes denial at the last protected evaluation defined in section 8. Subsequently ordered evaluations must observe revocation and deny Intake. Previously ordered evaluations are not retroactively unauthorized; affected sessions are invalidated in the revocation's same transaction. Locks and fresh rereads retain the section 10 order through commit. An aborted attempt supplies no durable revocation signal to other replicas.

| evaluation_mode | Application of the clarification |
| --- | --- |
| descriptive_query | Describe the observed canonical state only; unavailable authority cannot be described as proved revocation or executable permission. No new audit write is required merely to query |
| session_create | Protected canonical reread and creation gate determine authority; a preceding committed Revoke excludes Intake. Required creation evidence remains in the caller-owned transaction |
| session_authenticate | Enforce fresh canonical state and invalidation snapshots; committed revocation denies affected sessions and requires new authentication. Failed Revoke alone does not prove durable invalidation |
| command_authorization | Prepare revocation, sessions, receipt, Events and definitive local audit in the sole Dispatcher UoW; final protected gate then one facade commit. Rollback and uncertain outcomes follow section 9.4.2 |
| deterministic_local | Exercise the same semantics with isolated synthetic canonical fixtures; never substitute a role/header or Session double for PostgreSQL atomicity/concurrency proof |

#### 9.4.4 Cases A-G and evidence obligations

These cases define future evidence, not tests already passed. Each Command uses one owning UoW; later independently admitted resolution is not a second UoW of the failed Handler.

| Case | Durable state and authority | Observable result and sessions | Reconciliation and claimable evidence |
| --- | --- | --- | --- |
| A. Required local audit persistence failure | Confirmed rollback preserves prior assignment and session state; no partial durable revocation | Primary error, never success; staged session invalidation also rolls back | Correct cause and admit a later operation; no successful receipt/Event/audit or cross-replica denial may be claimed |
| B. Subsequent export/consumer/destination outage | Revocation, sessions, receipt, Events and definitive local audit already committed; Intake stays revoked | Locally complete Revoke is independent of external availability; affected sessions stay revoked | No external delivery/reconciliation is required to complete Revoke; any separately governed export cannot restore access |
| C. PostgreSQL or commit failure | Confirmed rollback preserves previous state; an ambiguous commit may have committed all writes or none | Error or UNCERTAIN_RESULT as established; unavailable canonical proof denies dependent evaluation without asserting revocation | Later governed readback/retry; no success evidence unless commit is established |
| D. Lost commit acknowledgment | All-or-none durable outcome is unknown to the caller, including session invalidation | UNCERTAIN_RESULT, neither success nor rollback assertion | Later readback/idempotency/receipt; no internal second UoW or fabricated completion |
| E. Deterministic local audit payload/constraint error | Required local insertion failure aborts all Revoke writes; prior authority may remain otherwise valid | Primary error; no success and no durable session invalidation from the failed attempt | Correct deterministic cause before a later operation; identical blind retry does not resolve it |
| F. Revoke not admitted | No Revoke mutation or successful evidence; previous canonical authority is unchanged by the rejected attempt | Rejection; Dispatcher admission rejection creates zero UoWs; sessions not revoked by the attempt | No completion claim or global denial trigger; any later request must satisfy admission independently |
| G. Revoke concurrent with session authentication | Successful transactions follow protected lock/reread order; Revoke invalidates affected sessions in its commit | Authentication ordered later observes revocation and denies Intake; earlier evaluation is not retroactively unauthorized | Prove both orders and rollback with independent PostgreSQL transactions; aborted Revoke creates no durable peer signal |

#### 9.4.5 Preserved policy and authority limits

AUTH-POLICY-001 sections 10-12 retain all general incident, retention and unhealthy-control obligations. This clarification does not classify every local error as global audit failure. Any future policy demanding global or cross-replica denial from an aborted attempt needs separately defined trigger, scope, authority source, recovery and architectural authorization.

The clarification neither requires nor authorizes outbox, durable queue, worker, broker or global audit-health authority. It does not ratify ADR-020; authorize B1/B2/B3, contract registration, implementation, release, roles, permissions or assignments; close Amendment 018 section 8.3; or open section 8.5 or later gates. It grants no downstream authority. The Future Architecture Authority Act in section 21 remains entirely [not recorded].

## 10. Locks, idempotency and deterministic races

The corrected design uses the following global order, to be enforced on participating writers and login paths:

1. Non-authoritative discovery of the complete required IDs.
2. Principals, sorted by UUID.
3. Organizations, sorted by UUID.
4. Memberships, sorted by UUID.
5. TemporaryRoleAssignments, sorted by UUID.
6. Idempotency exclusion by Organization/contract/key.
7. ProductiveSessions, sorted by UUID.
8. Command-specific resources.

Discover actor and target lock requirements together. If authoritative reread reveals additional required locks that would violate the order, abort; do not expand the lock set out of order. Principal exclusive locks serialize login with affected authority Commands. Protect Organization status against updates: `FOR SHARE` provides protection that `FOR KEY SHARE` alone does not provide for non-key status changes. Select sufficient Membership/Assignment lock modes without later unsafe upgrades, hold locks through commit, and reread authoritatively after waits using fresh Read Committed statement snapshots. See [PostgreSQL explicit locking](https://www.postgresql.org/docs/16/explicit-locking.html) and [transaction isolation](https://www.postgresql.org/docs/16/transaction-iso.html).

Idempotency exclusion is inside the same UoW. Same-key retries must reread current admission before exposing the receipt. A unique constraint remains a backstop; SQL collision/deadlock abort is not recovered using a savepoint or second transaction inside the Command.

| Race | Deterministic serialized result |
| --- | --- |
| 1. Login vs grant | Login first: grant sees and revokes the new affected session. Grant first: login sees committed new authority and creates only a matching new session |
| 2. Login vs revoke | Login first: revoke includes that session. Revoke first: login resolves remaining canonical B, or denies if Membership/canonical chain is revoked |
| 3. Login vs reconcile | Login first: reconciliation invalidates affected active session. Reconcile first: login resolves the committed terminal/restored state |
| 4. Review vs revoke | Review first may commit timely review, then revoke wins subsequently. Revoke first makes review invalid; no reopening |
| 5. Revoke vs reconcile | Serialize on the same chain/assignment. Committed revocation is never undone; reconcile may restore terminal state without rewriting history |
| 6. Two grants | Membership locking and outstanding-row uniqueness permit one assignment. Same key/fingerprint replays; otherwise conflict; no duplicate grants |
| 7. Two reconciliations | One performs CAS restoration. The other rereads and replays its matching receipt or observes closed/already-restored state without duplicate transition/evidence |
| 8. Intake operation vs expiry/revoke | Fresh final time gate decides deadline order; lock order decides revoke order. An operation linearized before the boundary may commit later; one evaluated after expiry or committed revoke cannot obtain I |
| 9. Replay vs authority change | Current admission and fresh canonical state precede receipt disclosure. Revoked actor/invalid scope cannot recover executable authority from an old success receipt |

Restoration requires expected revision CAS, a valid active Membership still holding the exact temporary role, the exact immutable prior base role and a coherent terminal assignment. Unexpected role/status/revision does not permit overwrite or rebase. Seeing the base role without a canonical restoration marker does not prove successful restoration. A failed reconcile rolls back its own transition/evidence, not a prior committed Revoke; logical deadline denial remains effective.

### 10.1 Additional terminal-writer races

| Race | Required outcome and evidence |
| --- | --- |
| Participant vs logout | One active-to-terminal winner; loser rereads terminal state and emits no duplicate transition Event/audit |
| Participant vs authentication expiry | One terminal transition with the winner's valid classification; no stale overwrite or second transition evidence |
| Session-limit eviction vs revoke | Both respect Principal/session ordering; already-terminal victims are not evicted/revoked again |
| Cleanup vs logout | Cleanup deletes only freshly verified eligible terminal rows; logout either wins its transition or sees terminal/missing state without inventing a new event; no session reactivation |
| Principal change vs session creation/authentication | Fresh Principal revision and lock ordering prevent new or continuing authority from stale identity state; affected scope is Principal-wide |
| Organization change vs session creation/authentication | Protected Organization status/revision and reread prevent stale authority; discover affected Principals before ordered locks and fail closed on incompatible expansion |

Additional T-03 cases A-G in section 9.4 require confirmed local rollback, uncertain commit and successful Revoke/authentication ordering. A subsequent non-canonical audit outage does not affect committed authority; an aborted attempt is not a durable peer signal.

These extend, rather than replace, the original nine races. A transaction abort has no success evidence; retries are separate admitted operations, never an internal second UoW or savepoint.

## 11. Structured authority reference and contract candidates

### 11.1 Authority reference schema and limits

| Field | Closed structural validation |
| --- | --- |
| `reference_kind` | Exactly `architecture_authority_operational_act` |
| `act_id`, `document_id` | Opaque bounded identifiers; numeric bounds require explicit schema finalization, not inferred here |
| `document_sha256` | Exactly 64 hexadecimal characters, normalized canonically |
| `decision` | Exactly `authorized` |
| `purpose` | One of `assign`, `review`, `revoke`, `reconcile`, matching the Command |
| `target_membership_id`, `target_organization_id` | UUIDs matching the canonical target and scope |
| `decided_at` | Finite timezone-aware UTC timestamp |
| `recorded_by_principal_id` | Derived from trusted admitted actor, never a payload claim of authority |

The reference is immutable transition traceability and part of the fingerprint. Structural validation does not prove authenticity, approval or permission. A path, SHA, Event or text saying “approved” is not authority. Runtime assignment authority is canonical only because a later separately and expressly authorized operation may create that row through the dedicated command. No productive transport currently exists that can present this reference as an authorized B operation. This Proposed ADR invents no verifier/provider, reusable CLI, generic administrative endpoint, frontend flow or self-assignment path.

### 11.2 Candidate allocation and common contract rules

The following IDs were searched in repository contracts and implementation before drafting and were unallocated. Existing Governance CMD-001 through CMD-006, QRY-001 through QRY-004 and EVT-001 through EVT-005 must be considered even where runtime projection omits them. Candidates below are **not registered or reserved**. Each has candidate operational status **PLANNED**. Allocation must be rechecked at a separately authorized B1 gate.

Once B1 is separately authorized, canonical Package B definitions remain PLANNED throughout B1/B2/B3. The isolated Command test copies in §12.1 preserve the real contract ID and every metadata field, including lifecycle, except operational_status, which is IMPLEMENTED only in those test-local copies. This does not promote or mutate the canonical definition. The same-ID copy appears exactly once in its separate registry; the canonical PLANNED definition is not also loaded into that registry.

For Commands, precedence is: persistence/clock availability; trusted operational admission; canonical actor/target/scope and structural validation; locked receipt/fingerprint handling; expected revisions and transition/time checks; staged state/result/receipt/Event/audit; final protected gate; one Dispatcher UoW commit. Replay needs current admission but does not reapply historical expected revisions to reconstruct the old effect. Validation failures, denied authority, fingerprint conflict, invalid transition, concurrency conflict, source unavailability, persistence/commit failure and uncertain outcome use the closed failure family in §9.2. No permission or actor-approval provider is silently allocated by a contract name.

| Candidate Command, operational status PLANNED | Purpose and inputs | Successful original result | Additional errors and precedence | Idempotency and Events |
| --- | --- | --- | --- | --- |
| `IC-GOVERNANCE-CMD-007` `AssignTemporaryRole` | Dedicated base-to-temporary assignment; trusted actor, target Membership/Organization, expected P/O/M revisions, authorized duration, assign reference, key and trace context; no caller start timestamp or permission set | Assignment ID/state, immutable interval, resulting revisions and evidence references | Common precedence; deny non-base target, outstanding unrestored row, invalid duration/reference or CAS mismatch; no generic-role admission | Common immutable receipt; emits EVT-006 and affected Identity EVT-005/audit once |
| `IC-GOVERNANCE-CMD-008` `ReviewTemporaryRoleAssignment` | One timely human review; assignment/target, expected vector including A, review reference, key/trace | Recorded review, resulting revision/deadline and evidence references | Common precedence; reject terminal/already-reviewed incompatible request, late final evaluation or stale vector; cannot extend expiry | Common receipt; emits EVT-007 and affected Identity EVT-005/audit once |
| `IC-GOVERNANCE-CMD-009` `RevokeTemporaryRoleAssignment` | Revoke independently of restoration; assignment/target, expected vector, closed reason, revoke reference, key/trace | Committed revoked state/revision and evidence references; no restoration claim | Common precedence; incompatible terminal transition/conflict fails; restore failure cannot be a dependency | Common receipt; emits EVT-008 and affected Identity EVT-005/audit once |
| `IC-GOVERNANCE-CMD-010` `ReconcileTemporaryRoleAssignment` | Observe deadline closure and/or restore terminal assignment; target/assignment, expected vector/CAS, reconcile reference, key/trace | Effective/recorded closure and successful restoration markers/revisions as applicable | Common precedence; no active-before-deadline restoration; reject unexpected role/status/vector; no inferred restoration | Common receipt; EVT-009 only for new closure, EVT-010 only for actual restoration, affected Identity EVT-005/audit once |

| Candidate Query, operational status PLANNED | Purpose and inputs | Result | Errors and precedence | Idempotency and Events |
| --- | --- | --- | --- | --- |
| `IC-GOVERNANCE-QRY-005` `RetrieveTemporaryRoleAssignment` | Authorized scoped inspection by trusted actor, target/assignment selector and correlation context | Safe canonical assignment/history projection, current derived state/vector/time/deadline and closed reason; no executable authority from history | Availability, admission, scope, then fresh read/semantic classification; closed unavailable, denied, invalid or ambiguous result; do not leak cross-scope history | Read-only repeatable request semantics, no command receipt, no lifecycle mutation and no emitted Event |

Event inputs are the successful transition's canonical IDs, safe before/after state/revisions, actor/reference where relevant, effective/recorded times and command/receipt/correlation/causation references. They contain no secrets, cookies or editable permission grant. Their result is an immutable recorded fact inside the producer's UoW, not an independent authorization decision.

| Candidate Event, operational status PLANNED | Purpose and specific input/result | Errors and precedence | Idempotency and subsequent Events |
| --- | --- | --- | --- |
| `IC-GOVERNANCE-EVT-006` `TemporaryRoleAssigned` | Fact of dedicated assignment with immutable roles/interval and bound/result revisions | Producer validates assignment before Event; invalid evidence shape or persistence failure aborts entire Command | One fact per successful assignment receipt; replay emits none; no automatic child Event |
| `IC-GOVERNANCE-EVT-007` `TemporaryRoleAssignmentReviewed` | Fact of timely human review with review actor/reference/time and resulting A revision | Producer's final timely gate remains required after staged Event; failure aborts all | One fact per review transition; no replay emission or authority extension subscriber |
| `IC-GOVERNANCE-EVT-008` `TemporaryRoleAssignmentRevoked` | Fact of independent revocation, reason, actor/reference and effective/recorded timing | Revoke validation precedes staging; durable result requires same successful commit | One fact per revocation transition; no restoration or new authority derived from it |
| `IC-GOVERNANCE-EVT-009` `TemporaryRoleAssignmentClosed` | Observed expiry/review-missed closure, effective deadline and recorded observation | Reconcile proves temporal terminal condition; cannot overwrite prior terminal history | One fact per newly materialized closure; absence never implies active authority |
| `IC-GOVERNANCE-EVT-010` `TemporaryRoleRestored` | Fact of exact prior-role CAS restoration and resulting Membership revision | Successful restoration validation precedes staging; failure aborts reconcile | One fact per restoration transition; no reopening, replay emission or automatic grant |

All Event producers share closed persistence/commit/uncertain outcomes through their Command; Events are not separately invoked Commands with their own UoW or idempotency key. Evidence construction/schema errors fail the producing transition. No new Event subscriber or handler is implicitly composed.

Existing `IC-GOVERNANCE-QRY-001` EvaluateAuthority retains the final authority-decision responsibility. `IC-GOVERNANCE-QRY-003` ResolveEffectiveMembership retains canonical Membership-context responsibility. Their IDs remain unchanged; temporal inputs/results and invalidation profiles require explicit prospective amendments, not silent semantic expansion. Existing Governance EVT-001 is not reinterpreted as temporal assignment. Package A's eight contracts remain intact.

## 12. One superior architecture, separate B1/B2/B3 work packages

Every phase requires a **separate authorization, exact File Boundary, Evidence Gate, rollback, independent review, its own commit and its own conformance**. This Proposed ADR performs none of those acts. Phase completion alone cannot open default Intake access or authorize operational assignment.

| Phase | Candidate scope | Required exit and limits |
| --- | --- | --- |
| B1 | Explicit contract/profile allocation exclusively as PLANNED metadata | Real Dispatcher rejects these contracts before UoW creation; no executable handler or transport; independent contract evidence and conformance |
| B2 | Empty assignment/receipt schema, triggers/revisions, repository, PostgreSQL clock and central fail-closed resolver modes | Does not change canonical operational status; all contracts remain PLANNED; no real assignment/backfill; all static recognition/assignment guards coherent; default composition cannot grant I |
| B3 | Internal Commands/receipts, Identity participant, terminal-writer alignment, session invalidation and reconcile | Alternative A isolated test composition under §12.1 uses the real ID and handler/factory with a test-local IMPLEMENTED copy; exactly one handler facade commit after final gate; canonical contracts remain PLANNED; no default-composition enablement, productive transport or real assignment |
| Integral B conformance | Review combined B1/B2/B3 behavior and regression | Independent final evidence, own authorization/boundary/rollback/review/commit/conformance; no operational act inferred |
| Later productive operation | Separately defined and expressly authorized operational assignment/admission | Outside B implementation authority; no actor, access channel, deployment, data scope or pilot permission inferred |

B2 and B3 apply the bounded clarification in section 9.4 using existing local audit persistence patterns. No additional health prerequisite, asynchronous delivery infrastructure or implementation package is introduced.

The later gate sequence is contract and role-mechanism conformance, express evidence acceptance, explicit §8.3 closure, then a subsequent separate productive-assignment act. Effective assignment is not closure evidence; closure opens neither assignment authority nor §8.5+.

Positive authority scenarios may be exercised later with isolated synthetic test fixtures under their authorized gates. A document, configuration flag, environment variable or incomplete registration must never activate Intake in default composition.

### 12.1 B3 isolated test admission projection — alternative A

The actual ContractOperationalStatus members are PLANNED, IMPLEMENTED, VERIFIED, PRODUCTION, SUSPENDED and REMOVED. ACTIVE does not exist in this enum and is not proposed. Dispatcher admits IMPLEMENTED, VERIFIED and PRODUCTION for non-retired contracts; this structural predicate is not proof of architectural ratification or actor authority. No change to that predicate is required by alternative A.

**B3 isolated test admission projection**

Canonical Package B contracts remain `ContractOperationalStatus.PLANNED` throughout B1, B2 and B3. The real Dispatcher must reject their canonical definitions with `CommandNotDispatchableError` before creating a UnitOfWork.

For explicitly authorized isolated B3 tests, construct a new immutable `ContractDefinition` from each B1 canonical definition, preserving every field except `operational_status`, which is set to `ContractOperationalStatus.IMPLEMENTED` solely in that test-local copy. Register that copy exactly once in a separately constructed ContractRegistry, then seal it. Construct a separate sealed HandlerRegistry against that same registry and execute the actual Package B handler factory through the real Dispatcher and its UnitOfWork.

The test-local projection must not modify `CANONICAL_CONTRACTS`, a canonical registry instance, default bootstrap/application composition or productive configuration. It is a synthetic admission fixture, not canonical implementation status, conformance, release or assignment authority. No new operational status, Dispatcher-filter change, monkey-patch, environment switch, HTTP flag or payload-controlled promotion is permitted.

Tests must prove canonical PLANNED rejection with zero UoWs, isolated IMPLEMENTED execution, equality of all other definition fields, and absence of changes to canonical/default composition. Direct service invocation alone is insufficient Command/Dispatcher evidence. PostgreSQL-specific lifecycle, concurrency and atomicity evidence remains mandatory under the separately authorized B3 gate.

Canonical operational promotion or default handler composition requires a separate later authority/release act.

The isolated registry contains the real-ID test copy only, never both it and the canonical PLANNED definition. Uniqueness and sealing apply independently to each registry instance: no replacement, duplicate registration or shadowing inside a canonical registry is involved. The ModuleRegistry used for isolated construction supplies the actual contract owner; the isolated HandlerRegistry validates the actual owner/context against the same test-local ContractRegistry. Both registries are constructed separately from canonical/default instances and sealed before dispatch.

Equality checks cover ID, version, contract_type, owner_module_id, owning_context, owning_capability, name, semantic_purpose, lifecycle, criticality, primary_consumer_or_use_case, architectural_steward and traceability_references. Only operational_status may differ. The test must preserve the real handler/factory selection and cannot replace it with a dummy business handler while claiming B3 conformance. A different synthetic ID can provide complementary infrastructure evidence but does not replace the real-ID test. A Session double may prove mechanics; it does not replace real PostgreSQL evidence.

The required sequence is B1 canonical registration exclusively as PLANNED; B2 with no operational-status change; B3 with the explicitly isolated real-ID projection above; and a separate later release/authority act for canonical promotion or default composition. The fixture never enters bootstrap/default app, and no environment variable, HTTP flag or payload can select or promote it there. Synthetic B3 admission is resolved at design level; phase implementation authorization and its evidence remain separate requirements.

B1/B2/B3 remain one superior architecture with separately bounded implementation work packages, each requiring §12's authorization, exact boundary, independent review, Evidence Gate, rollback, commit and conformance. No phase inherits productive admission from the existence of a synthetic fixture.

## 13. Candidate file boundary — not yet authorized

The following is a **candidate** inventory pending a later authority act. It is not an Authorized File Boundary. Current drafting authorization covers only this new Proposed ADR file. Each phase must select and ratify its exact subset, including any documentary files, before work; the inventory does not authorize edits now.

### 13.1 Existing candidate source files (16)

| Existing path | Candidate purpose |
| --- | --- |
| `apps/api/src/yarvis_api/application/authority.py` | Base-only temporary static recognition |
| `apps/api/src/yarvis_api/services/authority_resolution.py` | Central resolver delegation |
| `apps/api/src/yarvis_api/services/governance_authority.py` | Generic/bootstrap guards and participating writer serialization |
| `apps/api/src/yarvis_api/services/productive_auth.py` | Fresh login/authentication authority and session invalidation integration |
| `apps/api/src/yarvis_api/api/dependencies/authority.py` | Trusted context and resolver consumption |
| `apps/api/src/yarvis_api/api/routes/auth.py` | Explicit legacy session wrapper ownership and regression integration |
| `apps/api/src/yarvis_api/api/routes/governance.py` | Generic write-schema guard and owner integration |
| `apps/api/src/yarvis_api/services/founder_bootstrap.py` | Preserve base-only enrollment/replay guard |
| `apps/api/src/yarvis_api/local_netpay_authority.py` | Preserve local/test base-only guard |
| `apps/api/src/yarvis_api/services/identity_provisioning.py` | Covered material writer and lock-order compatibility |
| `apps/api/src/yarvis_api/models/principal.py` | P/M revisions and composite candidate key |
| `apps/api/src/yarvis_api/models/organization.py` | Organization revision |
| `apps/api/src/yarvis_api/models/productive_auth.py` | Invalidation snapshots, not permission authority |
| `apps/api/src/yarvis_api/models/__init__.py` | New model metadata composition |
| `apps/api/src/yarvis_api/bootstrap.py` | Bounded internal composition with no productive transport |
| `apps/api/src/yarvis_api/canonical_contracts.py` | Explicit later candidate contract/profile projection |

### 13.2 Existing candidate test files (10)

| Existing path | Candidate regression |
| --- | --- |
| `apps/api/tests/test_authority_resolution.py` | Canonical chain, roles and fail-closed authority |
| `apps/api/tests/test_productive_auth.py` | Login/authentication/revocation and session continuity |
| `apps/api/tests/test_productive_auth_migration.py` | Session schema compatibility |
| `apps/api/tests/test_governance_authority_contracts.py` | Membership writes, guards and contract behavior |
| `apps/api/tests/test_local_netpay_authority.py` | Local provisioning cannot grant temporary role |
| `apps/api/tests/test_founder_bootstrap.py` | Founder enrollment allowlist and replay |
| `apps/api/tests/test_founder_bootstrap_cli.py` | Existing CLI cannot bypass role guard |
| `apps/api/tests/test_bootstrap.py` | Default composition remains closed |
| `apps/api/tests/test_canonical_contracts.py` | Candidate metadata and Package A preservation |
| `apps/api/tests/test_contract_registry.py` | ID uniqueness and explicit operational status |

### 13.3 New proposed candidate files (exactly 18)

None of these files exists at the verified baseline. Names are proposed paths, not implemented symbols or allocated authority.

| Number | New proposed path | Candidate purpose |
| --- | --- | --- |
| 1 | `apps/api/src/yarvis_api/application/role_assignment_policy.py` | Separate recognized and assignable policies |
| 2 | `apps/api/src/yarvis_api/application/temporary_role_authority.py` | Pure authority matrix and resolution result |
| 3 | `apps/api/src/yarvis_api/application/temporary_role_contracts.py` | Explicit internal contract input/result profiles |
| 4 | `apps/api/src/yarvis_api/models/temporary_role_assignment.py` | Assignment and receipt persistence |
| 5 | `apps/api/src/yarvis_api/persistence/temporary_role_repository.py` | Fresh canonical snapshots and protected persistence |
| 6 | `apps/api/src/yarvis_api/persistence/authority_clock.py` | PostgreSQL current evaluation time |
| 7 | `apps/api/src/yarvis_api/services/temporary_role_assignment.py` | Dedicated lifecycle operations |
| 8 | `apps/api/src/yarvis_api/services/session_authority_invalidation.py` | Session-bound Identity participant |
| 9 | `apps/api/src/yarvis_api/dispatch/temporary_role_handlers.py` | Active-Session internal handler factories |
| 10 | `apps/api/tests/test_authority_writer_versions.py` | Four real trigger/writer revision rules |
| 11 | `apps/api/tests/test_authority_clock.py` | PostgreSQL clock and temporal limits |
| 12 | `apps/api/tests/test_temporary_role_authority.py` | Complete precedence matrix |
| 13 | `apps/api/tests/test_temporary_role_commands.py` | Atomic Commands, receipts and evidence |
| 14 | `apps/api/tests/test_temporary_role_session_concurrency.py` | Nine PostgreSQL races |
| 15 | `apps/api/tests/test_temporary_role_composition.py` | Single UoW and no incomplete enablement |
| 16 | `apps/api/tests/test_temporary_role_migration.py` | Empty additive schema and rollback constraints |
| 17 | `apps/api/tests/test_temporary_role_bypass.py` | Generic, bootstrap, local, seed and HTTP exclusion |
| 18 | `apps/api/migrations/versions/20260908_48_temporary_role_authority.py` | Candidate migration, expected parent `20260823_47`; recheck head/name before authorization |

### 13.4 Prospective documents, distinct from implementation paths

This Proposed ADR is the only artifact modified by the current terminal correction; the accepted proposal and all other existing documents remain unchanged. Later independent review, a ratifying decision/authority act, exact phase boundaries and conformance evidence require separate authorization. AUTH-POLICY-001's temporal invalidation supplement, AUTH-CONTRACT-001's session/Event profiles and Governance QRY-001/QRY-003 explicit temporal profiles are prospective documentary changes. Their filenames, registration and acceptance are not invented here. The 18-path implementation inventory does not count those prospective documents.

In the transferred design, the writer alignment is contained in existing candidate services/productive_auth.py, services/governance_authority.py, services/identity_provisioning.py and auth/Governance route wrappers, plus the already proposed services/session_authority_invalidation.py. Cleanup, logout, authentication expiry and session-limit logic all reside in the existing productive_auth.py. Their expanded regression scope fits the already proposed session-concurrency and command tests. The candidate inventory remains 26 existing and 18 proposed new files. T-03 adds no implementation path; required local audit integration and evidence must fit the later exact boundary or require an explicit amendment. Principal/Organization status services not found in the baseline are not invented; discovery of another writer requires an explicit boundary amendment before its implementation. The read-only registry/Dispatcher inspection in §12.1 does not add those framework files to the candidate edit boundary.

### 13.5 Explicit exclusions

ADR-019, Amendment 018 and AUTH-POLICY-001 remain unchanged by this drafting task. Existing migrations, application code, tests and configuration are unchanged now. `AUDIT_REPORT.md` is excluded from reading and editing. No independent transaction, background task or alternate outbox is authorized. No broad `clock.py`, UoW or Dispatcher framework rewrite, configuration/provider changes, frontend, reusable CLI, HTTP/admin transport, seed modification, worker or scheduler is included in the candidate implementation scope. Existing indirect route consumers are regression targets, not an implicit blanket edit allowance. Production resources, secrets and external account/data access remain excluded.

## 14. Candidate Evidence Gates

These gates define future evidence; none has been executed or passed for B. Use real isolated PostgreSQL where database semantics matter, not SQLite or mocked locks as conformance evidence. Each phase requires the governance artifacts and independent review listed in §12.

| Gate | Required evidence |
| --- | --- |
| B1 | Recheck all candidate IDs against normative documents and runtime projection; explicit names, scopes, inputs/results/error precedence/idempotency/Event relationships; exclusively PLANNED; real Dispatcher rejection before UoW creation; QRY-001/QRY-003 and Identity profiles explicit; Package A's eight contracts unchanged; no handler or transport registration |
| B2 | Additive empty schema/head-parent verification; DDL/invariant matrix §5.2.1 including explicit NOT NULL, deterministic same-row CHECK, referencable composite FK key and unique partial index; immutable fields/history and empty assignments; four real PostgreSQL triggers, revision 1, null-safe changes/no-ops, arbitrary-writer attempts, FK-driven changes, invalid OLD/overflow rejection; privileges/trigger enablement; all five resolver modes and permission guards; 336/720-hour timezone-independent tests; all four calls/indirect consumers coherent; canonical status remains PLANNED and no default I |
| B3 | Alternative A under §12.1: canonical PLANNED rejection before UoW creation and isolated real-ID IMPLEMENTED-copy execution through actual handler/factory, Dispatcher and UoW; equality of every other field including lifecycle; separate sealed registries with one copy per ID and no canonical/default/configuration changes; exactly one handler facade commit, zero direct Session commits or service/repository/participant commits, second UoW or nested Dispatch; atomic state/result/receipt/Event/audit; replay/conflict; separate revoke/restore; all terminal writers aligned; original nine plus six additional races; real PostgreSQL final-gate, commit-failure/uncertain-result evidence; no productive transport, bypass or real assignment |
| Integral B conformance | Independent review of all phase evidence against ADR-019/ADR-017/AUTH-POLICY; combined composition and failure behavior; full focused regression, type/lint/format checks appropriate to authorized changes; zero real assignments, Package A intact; contract and role-mechanism conformance precedes express evidence acceptance and explicit §8.3 closure; productive assignment requires a subsequent separate operational act; closure grants no assignment authority and opens no later gate |

T-03 evidence is mandatory within the separately authorized B2/B3 gates. B2 verifies the definitive local AuthenticationSecurityAudit profile, required sanitized fields and all five modes without a health vector or delivery dependency. B3 proves cases A-G through real Dispatcher/factory/CommandUnitOfWork and isolated PostgreSQL: shared Session/transaction, atomic revocation/session/receipt/Event/audit commit, local audit failure with complete rollback and primary-exception preservation, no false success, lost-ack readback/idempotency in a later operation, and both Revoke/authentication orders. Prove successful Revoke requires no external delivery and aborted Revoke is not represented as durable peer denial. No outbox, queue, worker or global health mechanism is part of either gate. Session doubles alone are insufficient.

Detailed required adversarial cases:

- Every matrix row, including unknown role, base role with assignment history, temporary string alone, duplicates, composite-ID mismatch, stale bindings, restored-active inconsistency and safely decoded malformed data.
- Review and expiry at each boundary minus one microsecond, exactly at the boundary and plus one microsecond; day-14/day-30 limits; no future/backdated start; shorter duration; no extension/reactivation; lock wait crossing a deadline; timely final evaluation followed by later successful commit.
- Unavailable canonical repository/clock, nonfinite time and observed backward samples; SQL-aborted Session with proof of no additional queries/fallback; preserve primary exception.
- Confirmed flush/commit failure with no partial successful state or evidence; failed cleanup cannot mask the primary exception. Lost commit acknowledgment yields UNCERTAIN_RESULT without an internal second UoW or fabricated rollback claim.
- All nine races from §10 on real PostgreSQL, including same/different idempotency keys, stale ORM identity-map state, reread after lock waits and lock-set expansion rejection.
- Snapshot mismatch and deadline invalidation; old sessions without snapshots require new authentication; review/grant/revoke/reconcile invalidate affected active sessions once; new base-only session is not repeatedly killed by unchanged terminal history.
- Separate generic allowlists: base remains allowed, unknown remains denied, temporal role rejected before receipt replay and writes in every generic path; dedicated operation is the only application base-to-temporary writer.
- One Dispatcher UoW and active Session per Command; exactly one handler invocation of the received CommandUnitOfWork commit facade immediately after the final gate; zero direct Session.commit() calls, zero service/repository/participant commits or rollbacks, zero second UoW, second Session, independent transaction, nested Dispatch, savepoint, background task, alternate outbox or legacy committing authenticate call. Dispatcher/UoW owns validation and cleanup. Evidence and receipt share the same commit, and cleanup preserves the primary exception.
- Exact four-call-site regression plus FastAPI dependency, direct resolver wrappers, auth capabilities and Inbox permission intersection. Check imports and actual bootstrap composition, not only `rg` matches.
- Empty real assignment table/no seeds/backfill; no Guillermo assignment; no productive transport or authority-reference provider; all Package A allocation/conformance invariants intact.

- DDL-specific gate: map every §5.2.1 invariant to its implementation; demonstrate FK prerequisite key, non-null required columns, optional-block null rejection, ordinary UNIQUE versus unique partial index, OLD/NEW transition validation and protected cross-row CAS. Reject clock-dependent or cross-row CHECK designs.
- Mode-specific gate: descriptive_query has no executable capability; session_create holds protection through creation commit; session_authenticate coordinates terminal writers and has no cross-request envelope reuse; command_authorization rereads after waits/flush and gates before facade commit; deterministic_local uses validated deterministic identity and explicit synthetic assignments only. Test mixed/stale snapshots and concurrent P/O/M/A changes in every applicable mode.
- Terminal-writer gate: prove complete physical writer inventory before implementation; participant/logout, participant/expiry, session-limit/revoke, cleanup/logout, Principal-change/creation/authentication and Organization-change/creation/authentication races. Only the successful conditional terminal transition records its corresponding Event/audit; losing/no-op writers emit none.
- Absolute-duration gate: 14 days equals 336 hours and 30 days equals 720 hours. Execute the same instant calculation with connection TimeZone set to UTC, a zone without DST, a zone crossing DST start and a zone crossing DST end. The resulting UTC instants must match in all four scenarios; setting UTC alone is insufficient evidence. Retain boundary tests at minus one microsecond, exact deadline and plus one microsecond.
- Admission gate: canonical PLANNED rejection raises CommandNotDispatchableError with zero UoWs. An isolated real-ID copy changes only operational_status to IMPLEMENTED; all other fields, including lifecycle, compare equal to the B1 definition. A separately constructed and sealed ContractRegistry contains one copy per ID, without simultaneously loading the canonical definition; a separate sealed HandlerRegistry uses the actual handler factory against that registry. Execute through the real Dispatcher/UoW and prove no mutation of CANONICAL_CONTRACTS or canonical/default composition. A different synthetic ID or direct-service-only test is complementary, not a substitute; Session doubles do not replace PostgreSQL tests. No flag, environment value or HTTP payload promotes or selects the fixture in production. Canonical promotion/default composition remain subject to a separate later release act.

Candidate checks include Ruff/format, Pyright and focused existing/new test suites selected by the exact authorized phase boundary. They are future implementation checks, not commands executed during this documentary task. Production privilege verification itself needs a separately approved evidence method; this Proposed ADR does not authorize production access.

## 15. Adversarial disposition matrix

All thirteen dispositions concern design only. Exactly seven original BLOCKER and six original MAJOR findings are retained. No row asserts implemented controls or passed conformance.

| Finding | Original severity | Corrective mechanism and contained counterexample | Disposition | Required implementation evidence |
| --- | --- | --- | --- | --- |
| B-01 | BLOCKER | Four PostgreSQL-maintained revisions cover real material updates; an uninstrumented writer cannot silently preserve a revision while triggers operate | RESOLVED AT DESIGN LEVEL | Real trigger/writer/no-op/forged-revision/privilege and FK-action tests |
| B-02 | BLOCKER | Unique outstanding assignment while restored_at is NULL includes terminals; revoked but unrestored row cannot permit a second grant | RESOLVED AT DESIGN LEVEL | Concurrent grants and terminal-unrestored uniqueness/restoration tests |
| B-03 | BLOCKER | Independent Revoke commits before any separate restoration; failed CAS cannot roll back an already committed revocation | RESOLVED AT DESIGN LEVEL | Revoke success followed by reconcile failure leaves I denied and sessions revoked |
| B-04 | BLOCKER | Shared Principal serialization and fresh session locks; login cannot escape grant/revoke/reconcile invalidation | RESOLVED AT DESIGN LEVEL | Three login races on real PostgreSQL |
| B-05 | BLOCKER | Exactly one handler commit through the received CommandUnitOfWork facade after the final gate; zero direct Session/service/repository/participant commits; Dispatcher/UoW owns validation and cleanup under ADR-017 | RESOLVED AT DESIGN LEVEL | Real Dispatcher execution with one facade invocation, no second UoW/nested Dispatch and preserved primary exception; positive test composition subject to §12.1 |
| B-06 | BLOCKER | Complete closed evaluation_mode protocols in §9.1.1 define locks, rereads, lifetime, Intake eligibility and persistence/reuse limits; prior envelopes and stale ORM snapshots cannot replace protected resolution | RESOLVED AT DESIGN LEVEL | All five mode protocols, stale/mixed snapshots, waits, post-flush gate and no descriptive/cross-request capability reuse |
| B-07 | BLOCKER | Explicit protected linearization point separates authorization order from physical commit completion | RESOLVED AT DESIGN LEVEL | Boundary crossing, delayed successful commit, confirmed failure and lost-ack cases |
| B-08 | MAJOR | P/O/M/A vector plus separate time evaluation; Membership-only version cannot hide covered upstream changes; Identity Binding excluded explicitly | RESOLVED AT DESIGN LEVEL | Material P/O/M/A changes and independent clock expiry/scope tests |
| B-09 | MAJOR | Structured reference is traceability only; no invented verifier or operational transport converts a hash/path into approval | RESOLVED AT DESIGN LEVEL | Default-denied admission, forged-reference and composition tests |
| B-10 | MAJOR | Canonical B survives while affected sessions are revoked and require new authentication; no continuity promise | RESOLVED AT DESIGN LEVEL | Policy/profile review and revoked-session/new-base-session tests |
| B-11 | MAJOR | Independent generic/bootstrap allowlists; adding a recognized static temporary role cannot make it generically assignable | RESOLVED AT DESIGN LEVEL | All generic/bootstrap/founder/local/seed/HTTP anti-bypass cases |
| B-12 | MAJOR | B fallback requires proven C in healthy SQL; unavailable/aborted persistence cannot silently become static authority | RESOLVED AT DESIGN LEVEL | Real aborted Session and no-further-query proof; decoder versus driver failure cases |
| B-13 | MAJOR | Synchronous logical temporal denial with later effective/recorded closure; no scheduler or missing Event can prolong I | RESOLVED AT DESIGN LEVEL | Unobserved deadline denial, delayed reconcile, failed restoration and no-reopening tests |

### 15.1 Individual independent-review amendment dispositions from the accepted design

The source's initial review of commit `b12f64cd0c4e6c21854b2a86125e56a105ffcb62` returned ACCEPT WITH AMENDMENTS (0 CRITICAL, 1 HIGH, 4 MEDIUM, 1 LOW), with B-05/B-06 initially partially resolved. The amended mechanisms below were subsequently accepted as design input by Architecture Authority on 2026-09-08, expressly accepting the terminal ACCEPT verdict with no mandatory findings pending. The source records that act; no separate nonexistent review artifact or reviewer identity is asserted here.

| Review finding | Original severity | Transferred corrective mechanism | Disposition | Required future evidence |
| --- | --- | --- | --- | --- |
| R-01 | HIGH | §§5.3, 8, 12 and 14 explicitly require one handler CommandUnitOfWork facade commit and prohibit direct Session/service/repository/participant commits; B-05 revised | RESOLVED AT DESIGN LEVEL | Real Dispatcher/UoW instrumentation, failure and cleanup evidence |
| R-02 | MEDIUM | RESOLVED AT DESIGN LEVEL through alternative A in §12.1: canonical PLANNED definitions remain unchanged; real-ID immutable test-local copies change only operational_status to IMPLEMENTED in separate sealed registries using the actual handler/factory and Dispatcher | RESOLVED AT DESIGN LEVEL | Demonstrate zero-UoW canonical rejection, isolated execution, equality of every other field, no canonical/default mutation and real PostgreSQL B3 evidence; canonical promotion/release is separate |
| R-03 | MEDIUM | §5.2.1 maps row, FK/key/index, OLD/NEW, protected CAS and runtime-time invariants to implementable mechanisms | RESOLVED AT DESIGN LEVEL | DDL and NULL/cross-row/transition tests in §14 |
| R-04 | MEDIUM | §9.1.1 defines all five closed resolver modes, protection, freshness, validity, Intake eligibility and reuse limits; B-06 revised | RESOLVED AT DESIGN LEVEL | Protected mode-specific concurrency and stale-envelope evidence |
| R-05 | MEDIUM | §9.3.1 inventories terminal writers and scopes; §10.1 adds six races; §13 explains containment within existing candidate paths | RESOLVED AT DESIGN LEVEL | Complete writer rediscovery and conditional-transition/evidence tests; amend boundary if another writer is found |
| R-06 | LOW | §8 fixes exactly 336/720 hours independent of connection TimeZone; §14 requires UTC, non-DST, DST-start and DST-end comparisons | RESOLVED AT DESIGN LEVEL | Identical resulting UTC instants and microsecond boundaries on real PostgreSQL |

All six R findings and all thirteen B findings are individually **RESOLVED AT DESIGN LEVEL** in the accepted source. None is implemented or conformant. Alternative A resolves R-02 without a pending B3 synthetic-admission decision; actual authorization, tests and conformance remain pending. These inherited design dispositions are not an independent ACCEPT of this ADR. Its own independent review is PENDING under §20.

### 15.2 Terminal ADR findings and current dispositions

The independent review of published ADR commit `ca37846d21ea0207aebc965002335077d96f93b2`, canonical SHA-256 `1E7A4AAA39F017B7766DEB5BE6C6ABBB1F5A15C61D27E104B6E412D108428CA1`, returned **ACCEPT WITH AMENDMENTS**: 0 CRITICAL, 2 HIGH, 1 MEDIUM, 0 LOW. These corrections record no replacement verdict.

| Finding | Severity | Current disposition | Correction / remaining obligation |
| --- | --- | --- | --- |
| T-01 | HIGH | RESOLVED AT DESIGN LEVEL | §§1.3, 12, 14 and 19 place conformance, express evidence acceptance and explicit §8.3 closure before a subsequent separate productive-assignment act; no assignment prerequisite or downstream opening |
| T-02 | MEDIUM | RESOLVED AT DESIGN LEVEL | §§1.3 and 8 specify prospective 336/720 absolute hours without local/calendar/DST arithmetic, historical change, extension or assignment; §14 retains the four timezone/DST cases |
| T-03 | HIGH | RESOLVED AT DESIGN LEVEL | Section 9.4 records Guillermo de Hoyos' bounded clarification dated 2026-09-08 local: definitive local audit in one UoW; subsequent outage distinct from local failure; rollback/uncertain outcome and protected ordering; cases A-G remain future evidence |

B-01 through B-13 and R-01 through R-06 retain their individual source-design dispositions and evidence obligations. T-01, T-02 and T-03 are individually RESOLVED AT DESIGN LEVEL, not implemented or conformant. B-03 and B-05 require atomic local audit and distinguish failed Revoke from completed denial; B-07 retains protected ordering; B-12 retains unavailable-authority denial without inferring global revocation. Renewed independent review of all three corrections is PENDING; no replacement ACCEPT is recorded.

## 16. Documentary and progressive rollback with history preservation

For this documentary draft, rollback is limited to this ADR under separate explicit authorization: if still untracked, remove only this exact newly created draft; if tracked later, use a documentary revert preserving history, without rewriting commits or altering the accepted proposal or ADR-019. Do not use `git clean`, broad resets or delete any unrelated untracked file. No rollback is executed or authorized by this text. Withdrawal of the draft creates no implementation, contract or operational effect and does not retract the source proposal's separately recorded acceptance.

Confirmed operation rollback preserves previous canonical state, including sessions, and commits no successful receipt/Event/audit. This differs from rollback of an application release: release or restore must never reactivate a committed revocation or erase its required local evidence. Subsequent external audit unavailability neither requires undoing Revoke nor restoring sessions. Resolve uncertain outcomes through separately governed readback/idempotency, never an extra UoW of the original Handler.

Rollback is phase-specific and must be included in each later authorization. It must fail closed without interpreting schema removal or missing evidence as restored authority.

| Stage | Candidate rollback behavior |
| --- | --- |
| B1 metadata only | Return unimplemented projection/profile changes under the later authorized boundary; preserve decision history and Package A contracts; no operational effect exists |
| B2 empty additive schema | Disable incomplete composition first; empty/isolated schema downgrade may be assessed after proving no runtime dependency, assignment or session snapshot requirement |
| B3 before any real operation | Remove internal activation/composition only after preserving base-only recognition and resolver/session dependencies; retain schema/history needed by readers |
| Any later state containing assignments | Revoke before restoring through separately authorized operations; invalidate sessions, restore by CAS, preserve receipts/Events/audit and terminal history; prefer additive retention over destructive downgrade |

Do not remove base-only recognition while the temporary role string exists. Do not remove revisions or snapshots while a resolver depends on them. Do not delete history as rollback. A destructive downgrade is permitted only in an isolated database or proven empty schema under its own authorization. A failed restoration never reactivates Intake. No rollback reactivates terminal assignments or revoked sessions; new authentication remains required.

## 17. Residual risks and decisions still requiring Architecture Authority

The bounded T-03 interpretation is resolved at design level by section 9.4. Residual risks include local audit profile/constraint defects causing full Revoke failure, lost commit acknowledgment and stale session writers. These require the B2/B3 evidence, not an inferred global health authority. General AUTH-POLICY-001 sections 10-12 duties remain; any future global denial policy requires separate architecture.

The design resolutions do not remove implementation risks: privileged roles can disable triggers or change data outside application guards; time and commit completion after the linearization point are not exact durability evidence; deadlocks/serialization aborts must remain closed; the 26-existing/18-new candidate boundary is broad; Identity/Governance participation must remain narrowly scoped; legacy wrappers retain commit ownership outside the new core and all terminal writers need alignment; and no productive authority transport/provider exists. Alternative A must be contained in test-local registries: confusing its IMPLEMENTED copy with canonical promotion, changing lifecycle or other metadata, importing the fixture into default bootstrap, or treating a Session double as PostgreSQL conformance would exceed its authority. Equality and isolation evidence are mandatory. Confusing facade commit intent with direct Session commit would violate ADR-017; the amended design requires exactly one handler facade call. Resolver mode protection, cross-row CAS and timezone-independent hour arithmetic must be demonstrated, not inferred from fresh queries or timestamp types. Identity Binding remains outside the revision vector. Lost acknowledgment remains an uncertain outcome, not an atomicity proof.

Architecture Authority must still record acceptance or rejection of this superior Proposed ADR after its own independent review, any explicit schema/profile finalization (including bounded opaque identifier representations), actual contract allocation and documentary supplements, exact per-phase file boundaries and evidence methods, independent reviewers, phase implementation authorizations and conformance. Those are pending acts, not partially inferred permissions. The later operational admission mechanism, actual actor, assignment act and any production/pilot access require separate decisions outside B; this Proposed ADR provides none.

The source proposal's accepted design and this Proposed ADR do not authorize implementation. Repository drift, a changed head/contract allocation or new implementation evidence requires revalidation before any subsequent phase.

## 18. Consequences

The architecture makes expiry and revocation effective at protected authorization evaluation without waiting for physical role restoration or any external audit materialization; required local audit commits atomically with Revoke. It preserves the four canonical base permissions while requiring new authentication after session authority loss/change. Separate canonical history and receipts permit auditable replay without using audit as authority; the single physical role prevents an additional editable effective-role source.

The cost is coordinated integration across authority resolution, assignment guards, sessions, legacy transaction owners, database revisions and writer locks. Real PostgreSQL evidence is indispensable. Reauthentication is deliberate, and a failed reconcile may leave a terminal unrestored assignment blocking a new grant while Intake remains denied. Empty structural revision initialization invalidates unsupported historical session snapshots; it cannot reconstruct past authority.

The bounded design does not solve Identity Binding versioning, privileged database tampering, every cross-operation clock rollback, exact physical commit durability timing or productive operational admission. Deferred bounded schema/profile representations require later explicit review, not invented defaults. Canonical operational promotion, default composition and actual assignment remain separate release/authority decisions. These consequences do not expand the candidate boundary.

## 19. Authority limits and required next acts

This Proposed ADR authorizes no B1, B2 or B3 work, contract registration or reservation, operational metadata change, migration, trigger, model, repository, service, handler, test or configuration change. It grants no role, permission, productive session, temporal assignment or authority to Guillermo de Hoyos or anyone else. It authorizes no canonical promotion, default handler composition, HTTP/CLI/frontend transport, operational authority provider, deployment, synchronization or pilot.

No production access, secrets, Google resources, OAuth, Gmail, mailbox access or mailbox data is authorized. `AUDIT_REPORT.md` must not be opened, edited, staged or removed. The proposal, ADR-019, Amendment 018, AUTH-POLICY-001 and all other existing files remain unchanged by this correction.

There is no downstream implementation, release, composition, operation or assignment authority. Amendment 018 §8.3 remains open. The mandatory sequence is contract and role-mechanism conformance → express acceptance of evidence → explicit §8.3 closure → subsequent separate operational act for productive assignment. Effective assignment is not required to close §8.3. Closure authorizes no assignment and opens neither §8.5 nor any subsequent gate. Even future ratification of this architecture cannot bypass these limits or the separate per-package acts in §12. Operational assignment cannot be inferred from completed code, canonical metadata, a test fixture, a reference hash or conformance alone.

The sequence after this draft is independent architectural review, any expressly authorized documentary corrections, and a separate Architecture Authority act deciding architectural ratification. Each implementation work package then requires its own exact authorization and evidence/conformance sequence. This draft performs none of those future acts. No staging, commit or push is authorized for this drafting delivery.

## 20. Independent Review Disposition - corrections PENDING

| Review field | Current value |
| --- | --- |
| Published-version review | ACCEPT WITH AMENDMENTS; T-01 HIGH, T-02 MEDIUM, T-03 HIGH |
| Review status of this correction | PENDING independent review; Proposed, not ratified |
| Reviewer | [not recorded] |
| Reviewed ADR commit and canonical SHA-256 | [not recorded] |
| Review date | [not recorded] |
| Verdict | [not recorded] |
| Mandatory findings and dispositions | T-01, T-02 and T-03 individually RESOLVED AT DESIGN LEVEL; no implementation conformance or new independent acceptance |
| Architecture acceptance / implementation conformance | Not granted by this draft |

Review must independently verify faithful transfer from the accepted proposal, all individual B/R dispositions, constraint/trigger feasibility, temporal/transaction claims, writer races, the five modes, anti-bypass, alternative A, all ten candidate IDs, the 26 existing and 18 new candidate paths, the bounded clarification and cases A-G in section 9.4, future gates and authority limits. Documentary validation is not this independent review. The accepted source's terminal ACCEPT must not be reused as this ADR's verdict.

## 21. Future Architecture Authority Act

Every value in this block is deliberately unrecorded. Neither the source proposal's signature/date nor this draft's creation date populates this future act. This blank template grants no authority.

| Field | Value |
| --- | --- |
| Act ID | [not recorded] |
| Architecture Authority | [not recorded] |
| Decision | [not recorded] |
| Decision date | [not recorded] |
| Accepted ADR draft commit | [not recorded] |
| Accepted ADR draft canonical SHA-256 | [not recorded] |
| Hash basis | [not recorded] |
| Independent reviewer and review reference | [not recorded] |
| Independent review verdict | [not recorded] |
| Mandatory findings pending | [not recorded] |
| Accepted architectural scope | [not recorded] |
| Authorized implementation work packages | [not recorded] |
| Authorized File Boundaries | [not recorded] |
| Evidence Gates | [not recorded] |
| Rollback authority | [not recorded] |
| Contract registration or promotion authority | [not recorded] |
| Release or default composition authority | [not recorded] |
| Operational assignment authority | [not recorded] |
| Exceptions | [not recorded] |
| Downstream authority | [not recorded] |

## 22. Documentary delivery boundary

The only file modified by this terminal correction is `docs/decisions/ADR-020_RATIFY_TEMPORARY_ROLE_AUTHORITY_ARCHITECTURE.md`. This exact documentary boundary is distinct from the candidate implementation inventory. No other existing file is edited, no code or database tests/migrations are run, and no staging, commit or push is performed.

Delivery checks cover strict UTF-8 without BOM and LF, Markdown table/fence/heading structure, intentional placeholders, each of the nineteen inherited design-only rows and three individual T dispositions, the three RESOLVED AT DESIGN LEVEL T dispositions and bounded clarification, candidate counts and existence, canonical SHA-256, whitespace checks for the tracked documentary diff, unchanged source hashes, empty index and final Git status. The resulting hash is reported externally to avoid a self-referential hash. Stop for independent review after those checks; validation does not ratify the draft.
