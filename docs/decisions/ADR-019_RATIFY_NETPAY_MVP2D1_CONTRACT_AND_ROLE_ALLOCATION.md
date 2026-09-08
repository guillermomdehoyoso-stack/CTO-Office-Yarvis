# YARVIS
# ADR-019 — Ratify Netpay MVP-2D1 Contract and Role Allocation

## Status

**ACCEPTED — ARCHITECTURAL AUTHORITY ONLY — NO IMPLEMENTATION OR ASSIGNMENT AUTHORITY**

## Date

**Proposed:** 2026-09-08

## Context

Implementation Roadmap Amendment 018 separates the productive MVP-2D1 path
into sequential gates. Its §3.2 Organization Verification Gate and §8.2
Canonical Identity Gate have been accepted as satisfied. Section 8.3 Contract
and Role Allocation remains unsatisfied and closed to productive progression.

The normative source for this ADR is the accepted proposal:

- document: `docs/engineering/NETPAY_MVP2D1_CONTRACT_AND_ROLE_ALLOCATION_PROPOSAL.md`;
- accepted proposal commit:
  `eb3204e86187acfab14a5bdef71004accb1c39a2`;
- accepted-document canonical SHA-256:
  `68AE749D870DAEC265A27753CDA28F106F465FB554D248D37CFEF532B5217780`;
- hash basis: UTF-8 without BOM, with CRLF and lone CR normalized to LF; and
- independent review verdict: `ACCEPT`.

The proposal was accepted only as the reviewed basis for this separate ADR.
Its acceptance did not assign contracts, roles or permissions and created no
implementation or downstream authority.

At the reviewed HEAD:

- none of the eight proposed contract identifiers exists in the canonical
  catalog or runtime;
- no proposed Gmail Handler, Query implementation or Event producer is
  registered;
- `PrincipalMembership` represents one role;
- productive authority resolves that role directly through
  `ROLE_PERMISSIONS`;
- no expiry-aware canonical temporary-assignment source exists; and
- no inert executable role catalog exists outside the active authority map.

Adding a static seven-permission temporary role to the current map would grant
the three Intake permissions without canonical expiry, review or revocation
checks. Contract definition, safe temporal authority machinery and an effective
assignment must therefore remain separate governed stages.

While this ADR remains Proposed, every statement in its Decision section is a
proposed future decision only. This document does not change the canonical
catalog, active authority map, Memberships or runtime.

## Decision

If, and only if, an explicit future Architecture Authority act changes this ADR
to Accepted, it would ratify the contract and role semantics below. Acceptance
would authorize no implementation or effective assignment unless that same act
expressly names a bounded package and its exact file boundary.

### 1. Canonical contract allocation

Exactly these eight identifiers would be assigned:

| Contract ID | Type | Semantic name |
| --- | --- | --- |
| `IC-NETPAY-CMD-016` | Command | `ConfigureNetpayGmailConnector` |
| `IC-NETPAY-CMD-017` | Command | `SynchronizeNetpayGmailConnector` |
| `IC-NETPAY-CMD-018` | Command | `ReviewNetpayIntakeCandidate` |
| `IC-NETPAY-QRY-007` | Query | `ListNetpayIntakeCandidates` |
| `IC-NETPAY-QRY-008` | Query | `RetrieveNetpayIntakeCandidate` |
| `IC-NETPAY-EVT-007` | Event | `NetpayIntakeCandidateReceived` |
| `IC-NETPAY-EVT-008` | Event | `NetpayIntakeCandidateReviewed` |
| `IC-NETPAY-EVT-010` | Event | `NetpayGmailConnectorSyncFailed` |

Every one of the eight would use exactly this metadata:

| Field | Value |
| --- | --- |
| `version` | `1.0.0` |
| `owner_module_id` | `netpay_merchant_operations` |
| `owning_context` | `Netpay Merchant Operations` |
| `owning_capability` | `Netpay Gmail intake` |
| `lifecycle` | `RATIFIED` |
| `operational_status` | `PLANNED` |
| `criticality` | `CORE` |
| `primary_consumer_or_use_case` | `Netpay MVP-2D1 Manual Review Variant` |
| `architectural_steward` | `None` |
| `traceability_references` | `("IMPLEMENTATION_ROADMAP_AMENDMENT_018.md", "NETPAY_MVP2D1_CONTRACT_AND_ROLE_ALLOCATION_PROPOSAL.md", "ADR-019_RATIFY_NETPAY_MVP2D1_CONTRACT_AND_ROLE_ALLOCATION.md")` |

`PLANNED` means unavailable to runtime. No contract becomes registered,
dispatchable, implemented or operational merely because its identifier and
semantics are ratified.

### 2. Excluded identifiers

The following remain outside MVP-2D1, unreserved and unassigned:

- `IC-NETPAY-CMD-019 AcceptNetpayIntakeCandidate`; and
- `IC-NETPAY-EVT-009 NetpayIntakeCandidateAccepted`.

Their numerical positions create no implied reservation. No contract in this
ADR may directly create a `CommercialIntakeItem` or `NetpayServiceCase`, invoke
`IC-NETPAY-CMD-009`, or perform business acceptance.

### 3. Common contract invariants

All Commands and Queries use canonical authority-envelope Organization and
Principal identity. Provider data, mailbox data, request headers and payload
fields cannot select an Organization or grant authority.

Authorization is revalidated before lookup, receipt lookup or replay. Foreign
and missing resources share the same concealed not-found behavior. Commands use
Organization-scoped idempotency identity and functional fingerprints. Identical
committed replay returns the original result; changed-payload key reuse fails
with `IDEMPOTENCY_CONFLICT`.

No payload, result, Event, receipt, log or error may contain complete body,
HTML, MIME, attachment bytes, credentials, tokens, secrets, raw provider
payloads or raw provider exceptions. No contract allocation authorizes provider
connectivity.

For every Command, authorized state, receipt, successful result and Events must
commit atomically within its single governed transaction. CMD-017 failure paths
remain governed by §4.2: rollback creates no durable result, receipt or Event,
and commit failure preserves the primary exception.

### 4. Command semantics

#### 4.1 CMD-016 — ConfigureNetpayGmailConnector

CMD-016 defines only logical configuration and lifecycle. It performs no OAuth,
consent, provider discovery, Gmail communication or credential storage.

Required permission: `netpay.intake.connect`.

Payload:

| Field | Type | Rule |
| --- | --- | --- |
| `mailbox_configuration_id` | UUID | Required for lifecycle changes; absent only for initial `configure`. |
| `operation` | Closed enum | Exactly `configure`, `pause`, `resume` or `disconnect`. |
| `mailbox_binding_key` | Opaque non-secret string | Required only for `configure`. |
| `label_binding_key` | Opaque non-secret string | Required only for `configure`. |
| `expected_version` | Positive integer | Required for changes to an existing configuration. |
| `reason_code` | Closed enum | Required only as allowed by the operation matrix. |

Closed reasons are `operator_pause`, `authorization_pending`,
`binding_invalid`, `security_review` and `operator_disconnect`.

| Operation | Required conditional fields | Prior state | Resulting state | Allowed reason |
| --- | --- | --- | --- | --- |
| `configure` | binding key and label key; no ID, version or reason | No matching configuration | `configured`, new ID | None |
| `pause` | ID, version and reason | `configured` | `paused` | `operator_pause`, `authorization_pending`, `binding_invalid`, `security_review` |
| `resume` | ID and version; no reason | `paused` | `configured` | None |
| `disconnect` | ID, version and reason | `configured` or `paused` | `disconnected` | `operator_disconnect`, `binding_invalid`, `security_review` |

Every unlisted field is prohibited for that operation. `disconnected` is
terminal for its configuration ID. A later configure creates a new ID.

Successful result fields are `mailbox_configuration_id`, `organization_id`,
`lifecycle_status`, `version`, `replayed` and
`provider_access_enabled=false`. The result contains no provider or secret
material.

Errors are `AUTHORIZATION_DENIED`, `VALIDATION_ERROR`, `RESOURCE_NOT_FOUND`,
`VERSION_CONFLICT`, `IDEMPOTENCY_CONFLICT`,
`INVALID_LIFECYCLE_TRANSITION`, `BINDING_CONFLICT` and
`CONTRACT_NOT_OPERATIONAL`.

#### 4.2 CMD-017 — SynchronizeNetpayGmailConnector

CMD-017 represents a future manual synchronization request. It remains
unregistered, non-dispatchable and fail-closed while `PLANNED`.

Required permission: `netpay.intake.connect`.

Payload fields are:

- required `mailbox_configuration_id: UUID`;
- required `trigger_kind`, whose sole value is `manual`;
- conditional `manifest_id: UUID`, usable only under a later real-pilot gate;
  and
- required non-negative `expected_checkpoint_version`.

Failure precedence is exact:

| Order | Condition | Result |
| --- | --- | --- |
| 1 | Contract unavailable | `CONTRACT_NOT_OPERATIONAL` |
| 2 | Authority invalid | `AUTHORIZATION_DENIED` |
| 3 | Payload invalid | `VALIDATION_ERROR` |
| 4 | Configuration missing or foreign | concealed `RESOURCE_NOT_FOUND` |
| 5 | Replay or conflicting reuse | committed replay or `IDEMPOTENCY_CONFLICT` |
| 6 | Checkpoint conflict | `VERSION_CONFLICT` |
| 7 | Connector disabled | `CONNECTOR_DISABLED` |
| 8 | Binding or label invalid | `BINDING_INVALID` or `LABEL_BINDING_INVALID` |
| 9 | Retention blocks ingestion | `RETENTION_BLOCKED` |
| 10 | Credential state invalid | `CREDENTIAL_STATE_INVALID` |
| 11 | Concurrent sync owns exclusion | `SYNC_ALREADY_IN_PROGRESS` |
| 12 | Post-admission failure before commit | complete rollback and `SYNC_FAILED_CLOSED` |

CMD-017 uses exactly the one Unit of Work created and owned by Dispatcher. Its
Handler never opens a second Unit of Work, nested independent transaction,
savepoint, background task, alternate outbox or equivalent mechanism.

Every post-admission failure before commit rolls back the entire Dispatcher
Unit of Work and terminates through `SYNC_FAILED_CLOSED`. It creates no durable
result, receipt or Event. If commit itself fails, the primary exception is
preserved and no later write or Event is promised. Absence of EVT-010 is never
evidence of success.

The only durable result is successful and contains:

- safe `sync_request_id` and `mailbox_configuration_id`;
- `status=completed`;
- non-negative `candidate_count` for the complete committed batch;
- `checkpoint_advanced` reflecting only the committed complete-batch
  checkpoint;
- `failure_code=null`; and
- `replayed`.

Replay exists only for a committed success. Durable post-failure recording
would require a separate contract and later Accepted ADR.

#### 4.3 CMD-018 — ReviewNetpayIntakeCandidate

CMD-018 records one explicit human review. It cannot create a Case, Master or
productive Commercial Intake entity.

Required permission: `netpay.intake.review`.

Payload fields are `candidate_id`, `decision`, conditional
`corrected_category`, controlled `reason_code` and positive
`expected_version`. Categories are exactly `commercial_contact_or_rfq`,
`tpv_physical`, `ecommerce`, `support_or_incident` and `unclassified`.

The decision matrix is closed:

| Decision | `corrected_category` | Allowed reason | Effective category | Review status |
| --- | --- | --- | --- | --- |
| `accept_classification` | Prohibited | `classification_confirmed` | Original proposed category | `classification_accepted` |
| `correct_classification` | Required and different | `classification_corrected` | Corrected category | `classification_corrected` |
| `reject_candidate` | Prohibited | `not_relevant`, `duplicate_candidate` | `null` | `rejected` |
| `request_correction` | Prohibited | `insufficient_information`, `requires_human_follow_up` | `null` | `correction_requested` |

Every other combination fails with `DECISION_PAYLOAD_INVALID` before mutation.
AI, classification or sync cannot make or impersonate a human decision.

Successful results contain candidate ID, review status, effective category,
canonical reviewer Principal ID, version,
`commercial_intake_projection_exists` and replay status. Business acceptance
is explicitly excluded.

Errors are `AUTHORIZATION_DENIED`, `VALIDATION_ERROR`,
`RESOURCE_NOT_FOUND`, `VERSION_CONFLICT`, `IDEMPOTENCY_CONFLICT`,
`CANDIDATE_ALREADY_REVIEWED`, `CATEGORY_NOT_ALLOWED`,
`DECISION_NOT_ALLOWED`, `DECISION_PAYLOAD_INVALID` and
`CONTRACT_NOT_OPERATIONAL`.

### 5. Query semantics

#### 5.1 QRY-007 — ListNetpayIntakeCandidates

Required permission: `netpay.intake.read`.

The request has optional closed `status`, optional closed `category`, optional
same-Organization `mailbox_configuration_id`, optional protected pagination
`cursor`, and required `limit` in `1..100`.

The result contains exactly `items`, `next_cursor`, `total_count` and nullable
`connector_health`. Candidate summaries contain only candidate ID,
configuration ID, proposed and effective category, review status, nullable
sanitized excerpt, nullable received time, projection-exists flag and version.

`sanitized_excerpt` and `received_at` remain `null` until §8.5 approves their
productive definitions. Connector health contains only configuration ID,
lifecycle status, successful `last_sync_status=completed` or `null`, candidate
count, controlled nullable error code and checkpoint-available boolean.

#### 5.2 QRY-008 — RetrieveNetpayIntakeCandidate

Required permission: `netpay.intake.read`. The request contains only a
same-Organization `candidate_id`.

The result contains the exact safe detail shape from the accepted proposal:
candidate ID, configuration ID, controlled provenance kind, nullable opaque
internal provenance reference, proposed and effective category, review status,
nullable review reason, nullable sanitized excerpt,
`attachment_metadata=null`, nullable canonical reviewer ID, nullable review
time, projection-exists flag, nullable same-Organization projection reference
and version.

`attachment_metadata` is a nullable reserved field that must remain exactly
`null`. `SafeAttachmentMetadata` is not defined. Any non-null value requires a
later Accepted ADR after §8.5 that expressly modifies QRY-008.

“Defined before §8.5” describes contract shape only, never runtime
availability. Both Queries remain unavailable until separately implemented and
made operational. No productive candidate field may be read or populated
before all applicable productive gates pass.

Both Queries fail with controlled authorization, validation, concealed
not-found and non-operational errors as specified in the proposal.

### 6. Event semantics

Events are immutable, tenant-scoped and safe for durable audit. Canonical event
timestamp, trace, correlation and causation conventions apply. Candidate
excerpts and prohibited provider content are excluded.

#### 6.1 EVT-007 — NetpayIntakeCandidateReceived

The exact payload is `organization_id`, `candidate_id`,
`mailbox_configuration_id`, `proposed_category`,
`review_status=pending`, nullable `manifest_id`, `occurred_at`,
`correlation_id` and `causation_id`.

#### 6.2 EVT-008 — NetpayIntakeCandidateReviewed

The exact payload is `organization_id`, `candidate_id`,
`mailbox_configuration_id`, decision, previous category, nullable effective
category according to the CMD-018 matrix, review status, controlled reason,
canonical `reviewed_by_principal_id`, `occurred_at`, `correlation_id` and
`causation_id`.

#### 6.3 EVT-010 — NetpayGmailConnectorSyncFailed

EVT-010 remains `RATIFIED` and `PLANNED`, non-operational and without a runtime
producer. CMD-017 does not guarantee its emission after rollback or commit
failure.

Its exact future-safe payload is `organization_id`,
`mailbox_configuration_id`, `sync_request_id`, controlled `failure_code`,
`checkpoint_advanced=false`, `candidate_count_committed=0`, `occurred_at`,
`correlation_id` and `causation_id`.

Closed failure codes are `contract_not_operational`, `connector_disabled`,
`binding_invalid`, `label_binding_invalid`, `credential_state_invalid`,
`retention_blocked`, `provider_unavailable`, `provider_rate_limited`,
`batch_validation_failed`, `batch_commit_failed` and `unexpected_failure`.
They carry no raw error or provider material.

Any producer requires a later Accepted ADR, exact File Boundary, Evidence Gate
and demonstrated ADR-017 compatibility. EVT-010 does not authorize another Unit
of Work or post-rollback persistence.

### 7. Temporary authorization model

#### 7.1 Permissions and role

The proposed new permissions are semantically distinct:

- `netpay.intake.read`;
- `netpay.intake.connect`; and
- `netpay.intake.review`.

No permission implies another. The temporary role name is
`netpay_intake_pilot_operator`.

During one valid temporary assignment, its effective permission set is exactly:

```text
netpay.master.read
netpay.master.manage
netpay.inbox.read
netpay.inbox.manage
netpay.intake.read
netpay.intake.connect
netpay.intake.review
```

The first four preserve exactly the existing authority of
`netpay_operations_operator`; that existing role remains byte-for-byte
semantically unchanged. The three Intake permissions are temporary additions.

The static `ROLE_PERMISSIONS["netpay_intake_pilot_operator"]` entry, if later
authorized, contains exactly the four base permissions. The role string alone
must never grant `netpay.intake.*`. Only an expiry-aware resolver may add the
three Intake permissions after validating canonical temporary-assignment state.

This composite role represents logical separation through independent read,
connect and review checks and differentiated receipts, Events and audit. It is
not dual control or separation between two people.

#### 7.2 Canonical temporary-assignment state

The future mechanism must have a durable canonical source, distinct from audit,
that records at minimum:

- assignment ID;
- target Membership;
- exact prior role;
- temporary role;
- effective time;
- review deadline;
- expiry time;
- status;
- authority reference;
- review completion under valid authority; and
- optimistic-concurrency token.

Audit reflects actions and outcomes but cannot determine effective permissions
or the restoration target.

The resolver denies all Intake permissions when assignment state is absent,
future, inactive, expired, revoked, overdue for day-14 review, ambiguous,
inconsistent, stale, mismatched to the Membership or unsupported by valid
authority. Denial is immediate even if physical role restoration is pending.
The four base Master and Inbox permissions remain available during
reconciliation.

The assignment lasts at most 30 calendar days from effective time, requires
review no later than day 14, defaults to non-renewal and requires a new
Architecture Authority act for extension or deviation.

Assignment, review, revocation and restoration require idempotency, functional
fingerprints and optimistic concurrency. Unexpected roles fail closed. Physical
restoration uses the canonical prior role, requires it to be exactly
`netpay_operations_operator`, uses compare-and-swap and restores exactly that
role. Audit is evidence, not restoration authority.

No effective assignment may use a simple unguarded
`UPDATE PrincipalMembership.role`. No effective pilot-role assignment may
occur until a separate Accepted ADR authorizes the expiry-aware mechanism and
productive authority-resolution checks, those changes are conformant, and a
separate operational act authorizes the assignment.

#### 7.3 Required call-site migration

Before the role is usable, every productive direct and indirect call site of
`permissions_for_role(...)` must be inventoried again against implementation
HEAD and migrated atomically to temporal resolution.

Verified current call sites include:

- `apps/api/src/yarvis_api/services/authority_resolution.py`;
- `apps/api/src/yarvis_api/services/productive_auth.py`; and
- `apps/api/src/yarvis_api/services/governance_authority.py`.

The active role map itself is in
`apps/api/src/yarvis_api/application/authority.py`.

No residual productive path may obtain Intake authority from the role string
alone. Here, atomic means no externally observable or authority-granting unsafe
intermediate state; it does not claim one transaction across PostgreSQL and
deployment.

### 8. Separated implementation and authority stages

The required sequence is:

```text
accepted proposal
→ Accepted ADR
→ contract-definition package
→ contract conformance acceptance
→ separately reviewed and Accepted expiry-aware role ADR
→ expiry-aware role package
→ role-mechanism conformance acceptance
→ explicit §8.3 closure act
→ separately authorized productive assignment
```

The contract package cannot modify roles or authority. The expiry-aware package
cannot assign a role to any person. A productive assignment cannot be inferred
from either package.

Section 8.3 may close only after the eight definitions and the canonical
expiry-aware assignment and authority-resolution mechanism have been separately
authorized, implemented and demonstrated conformant through their respective
Evidence Gates, and Architecture Authority expressly accepts that evidence and
closes §8.3. This is demonstration of the required canonical assignment
machinery, not an effective assignment to Guillermo de Hoyos or another person.

An effective assignment remains subsequent and requires a distinct operational
act and transactional evidence.

## Proposed Authorized File Boundaries

These boundaries are proposals for future authority. They authorize nothing
while this ADR is Proposed. Any Accepted act must restate the exact authorized
boundary.

### Package A — Contract definitions

HEAD establishes this exact minimal candidate boundary:

- `apps/api/src/yarvis_api/canonical_contracts.py`;
- `apps/api/tests/test_canonical_contracts.py`;
- `apps/api/tests/test_contract_registry.py`.

Authorization of a file permits only changes necessary to demonstrate this
package; it does not require that every authorized file change.

No other source or test file is authorized by implication. If implementation
requires another file, it must stop and request an ADR amendment.

### Package B — Expiry-aware role mechanism

Existing files verified as candidate participants are:

- `apps/api/src/yarvis_api/application/authority.py`;
- `apps/api/src/yarvis_api/services/authority_resolution.py`;
- `apps/api/src/yarvis_api/services/productive_auth.py`;
- `apps/api/src/yarvis_api/services/governance_authority.py`;
- `apps/api/tests/test_authority_resolution.py`;
- `apps/api/tests/test_productive_auth.py`; and
- `apps/api/tests/test_governance_authority_contracts.py`.

The canonical assignment model, repository/service ownership, migration file,
schemas and any additional tests are **TO BE DETERMINED**. No physical artifact
currently provides the required canonical expiry-aware state. This ADR does not
invent paths for them and does not authorize Package B.

Package B requires a later reviewed design and Accepted ADR that resolves those
paths, determines whether additional verified call sites exist, and states one
complete exact Authorized File Boundary. If that later package cannot remain
within its boundary, it must stop and request an amendment.

### Productive assignment

No file boundary is proposed for effective assignment. It is an operational
mutation, not part of Package A or B, and remains unauthorized.

## Evidence Gates

### Package A — Contract-definition Evidence Gate

Conformance requires reproducible evidence that:

1. exactly the eight named IDs were added;
2. CMD-019 and EVT-009 remain absent and unreserved;
3. metadata exactly matches this ADR;
4. all eight are `RATIFIED`, `PLANNED` and `CORE`;
5. duplicate IDs and invalid metadata fail closed;
6. the canonical registries remain valid and sealed;
7. no Handler, Handler factory, Query implementation, Event producer, route or
   runtime composition entry exists for the eight;
8. CMD-017 remains rejected as non-operational before effects;
9. CMD-017 retains success-only result, single-UoW and failure semantics;
10. EVT-010 remains producerless and non-operational;
11. QRY-008 retains `attachment_metadata=null`;
12. `netpay_intake_pilot_operator` remains absent from `ROLE_PERMISSIONS`;
13. `netpay.intake.*` grants no runtime authority;
14. `netpay_operations_operator` remains unchanged;
15. no authority resolver, Membership, identity, persistence, migration,
    configuration, route or deployment file changed;
16. focused canonical-contract and registry tests pass;
17. relevant authority regressions pass;
18. Pyright, Ruff and Ruff format checks pass;
19. `git diff --check` passes;
20. the diff is exactly within the accepted Package A boundary; and
21. independent conformance review records no unaccepted exception.

Passing this gate does not close §8.3.

Because Package A implements canonical metadata only, items 9 through 11 are
documentary and structural conformance checks. They prove that the canonical
purpose and traceability preserve the ratified semantics and that no conflicting
runtime schema, producer or implementation was introduced. They do not claim
that CMD-017, EVT-010 or either Query has been implemented.

### Package B — Expiry-aware role Evidence Gate

The later Package B ADR must require evidence that:

1. one canonical expiry-aware assignment source exists;
2. required persistence and migrations were explicitly authorized;
3. every assignment records all required canonical fields;
4. the role's static entry contains only the four base permissions;
5. the role string alone never grants Intake;
6. the three Intake permissions arise only from valid temporal resolution;
7. role, Intake permissions, canonical assignment source and resolver enter
   runtime without an unsafe intermediate authority state;
8. every productive `permissions_for_role(...)` call site was inventoried and
   migrated;
9. absence, future state, inactivity, expiry, revocation, missed day-14 review,
   ambiguity and inconsistency all deny Intake immediately;
10. the four base permissions survive restoration reconciliation;
11. read, connect and review checks remain independent;
12. assignment, review, revocation and restoration are idempotent and use
    optimistic concurrency;
13. restoration uses canonical prior role and never audit as authority;
14. failed canonical-state, receipt or audit commit rolls back the associated
    mutation;
15. unexpected roles fail closed without overwrite;
16. no effective productive assignment occurs during implementation or tests;
17. no second Principal or definitive multi-role architecture is introduced;
18. focused temporal, resolver, concurrency, rollback and restoration tests
    pass;
19. productive authentication and authority regressions pass;
20. Pyright, Ruff, Ruff format and `git diff --check` pass;
21. the diff matches the later exact File Boundary; and
22. independent conformance review proves no partial runtime authority.

Passing this gate does not assign the role to Guillermo de Hoyos or anyone
else.

## Rollback

While Proposed, rejection requires only deletion or documentary reversion of
this draft; no runtime rollback is required.

Package A rollback may revert only the eight contract definitions and their
bounded tests while they remain unused. Once referenced by runtime or durable
records, retirement requires separate authority. Package A rollback cannot
touch roles, Memberships, authority resolution or productive data.

CMD-017 failure rollback is the rollback of the sole Dispatcher-owned Unit of
Work. It creates no durable result, receipt or Event and never opens a second
transaction. Commit failure preserves the primary exception.

Package B rollback must leave no unsafe authority-granting intermediate state.
The role must remain absent or base-only unless every productive authority path
enforces canonical temporal state. No Intake permission may remain reachable
solely from a role string, and no resolver may depend on absent assignment
state. Ordered compatible migration and deployment phases must fail closed;
this is not a cross-system transaction claim.

Expiry or revocation removes Intake authority immediately even if physical
restoration is pending. Restoration preserves the four base permissions, uses
the canonical prior role with compare-and-swap, is idempotent and cannot use
audit as authority. Rollback cannot perform a productive assignment or delete
identity and historical authority evidence.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Contract IDs are mistaken for runtime availability | Keep all eight `PLANNED`; prohibit registrations and implementations in Package A. |
| Static role creates non-expiring Intake authority | Static entry is base-only; only canonical temporal resolution adds Intake. |
| Partial Package B deployment grants authority | Require one bounded package with fail-closed ordered phases and no unsafe observable state. |
| Unmigrated call site bypasses expiry | Inventory and test every direct and indirect productive call site at implementation HEAD. |
| Missed day-14 review or expiry leaves Intake active | Resolver denies Intake immediately from canonical state, independently of physical restoration. |
| Restoration removes existing Netpay authority | Preserve the four base permissions and restore the exact canonical prior role. |
| Audit becomes an authority source | Canonical assignment state governs permissions and restoration; audit is evidence only. |
| Composite role is represented as dual control | Preserve independent permission checks and state explicitly that one person is not four-eyes control. |
| CMD-017 failure implies durable failure evidence | Success is the sole durable result; rollback and commit failure promise no Event or receipt. |
| EVT-010 implies an alternate transaction | Keep it producerless and require a later ADR proving ADR-017 compatibility. |
| Query shapes pre-empt privacy decisions | Keep sensitive productive fields null and §8.5 closed. |
| Contract or role work is mistaken for productive assignment | Require a separate operational act after both conformance gates and §8.3 closure. |

## Explicit Prohibitions and Non-Goals

This Proposed ADR does not authorize:

- implementation or tests;
- changing `canonical_contracts.py` or any contract registry;
- adding a Handler, Handler factory, Query implementation or Event producer;
- changing `ROLE_PERMISSIONS` or any authority call site;
- creating the temporary-assignment source, model, migration or resolver;
- assigning a role or permission to Guillermo de Hoyos or anyone else;
- modifying a Person, Principal, Identity Binding, Membership or Organization;
- creating a second Principal or changing the one-role-per-Membership model;
- productive persistence, configuration, secrets or credentials;
- Google resources, OAuth, consent, Gmail or mailbox access;
- synchronization, cursor movement, workers, schedulers or queues;
- Commercial Intake, Master or Case creation;
- CMD-019 or EVT-009;
- routes, deployment or a pilot; or
- any adjacent contract, role, permission, gate or capability by implication.

Section 8.3 remains unsatisfied. Section 8.5 and every later productive gate
remain closed. Amendment 018 §12.2 is not complete.

## Relationship to Governing Authority

AR-001 requires a reviewed proposal, Accepted ADR, bounded implementation
package and conformance evidence. This Proposed ADR supplies only the draft ADR
stage. It creates no authority until an explicit Architecture Authority act.

ADR-017 governs Handler-factory composition and the single Dispatcher-owned
Unit of Work. CMD-017 preserves that boundary. Nothing here changes
`CommandHandler`, Dispatch, UnitOfWork or ADR-017 cleanup and exception
semantics.

Amendment 018 governs the gate order. This ADR concerns only §8.3 and cannot
waive §8.5 through §8.12. Canonical Identity evidence supplies a prerequisite,
not contract, role, implementation or assignment authority.

ADR-018 is synthetic-only evidence. It assigns no productive contract or role
and supplies no evidence for productive provider access.

## Consequences

### Positive

- Establishes exact contract identities and closed semantic boundaries.
- Prevents planned contracts from becoming runtime capability by implication.
- Preserves ADR-017 transaction ownership for CMD-017.
- Preserves existing Netpay Master and Inbox authority during a temporary
  pilot representation.
- Makes expiry, day-14 review and revocation fail closed independently of role
  restoration.
- Separates contract registration, temporal authority machinery and effective
  human assignment.

### Costs

- Requires two implementation packages and two conformance acceptances before
  §8.3 can close.
- Requires a new canonical temporary-assignment design and likely persistence,
  whose physical boundary remains unresolved.
- Requires migration of every productive authority-construction call site.
- The single-person composite role does not provide dual control.
- No business capability results from contract definitions alone.

## Unresolved Decisions Required Before Package B

The following cannot be transferred from the accepted proposal into an exact
implementation boundary without a further architectural decision:

1. canonical temporary-assignment model and table representation;
2. migration filename and lineage;
3. repository and service ownership;
4. exact concurrency-token representation;
5. exact assignment, review, revocation and restoration contracts;
6. exact Package B Authorized File Boundary; and
7. whether a future definitive multi-role architecture replaces the temporary
   representation.

These questions do not block consideration of Package A, but Package B and
§8.3 closure remain blocked until they are separately resolved and ratified.

## Independent Review Disposition

- Review verdict received: **ACCEPT WITH AMENDMENTS**.
- Critical findings: **0**.
- High findings: **0**.
- Amendments incorporated: **4**.

The four incorporated amendments are:

1. an exact, unconditional Package A candidate File Boundary;
2. the common atomicity invariant for Commands;
3. an explicit documentary and structural evidence classification for Package
   A items 9 through 11; and
4. documentary rollback language valid whether the draft is tracked or
   untracked.

These amendments clarify ratification and conformance boundaries. None changes
the architecture accepted in the normative proposal.

## Future Architecture Authority Act

- Decision: **ACCEPTED — ARCHITECTURAL AUTHORITY ONLY**
- Architecture Authority: **Guillermo de Hoyos, Architecture Authority**
- Decision date: **2026-09-07**
- Accepted ADR Draft commit: **`522ffb56db442a8e8d5969a3e82634ce45fbfa9b`**
- Accepted ADR Draft SHA-256: **`D371114809C0233557F7CF8B39DDADA0431090E12A8C9001A35A74935E38570A`**
- Hash basis: **Canonical UTF-8 without BOM, with CRLF and lone CR normalized to LF before hashing**
- Independent review verdict: **ACCEPT**
- Mandatory findings pending: **None**
- Accepted scope: **The architectural decisions, contracts, invariants, package separation, limits and Evidence Gates defined in ADR-019**
- Authorized implementation packages: **None**
- Authorized File Boundaries: **None**
- Accepted exceptions: **None**
- Downstream authority: **None**

This ratification does not satisfy or close Amendment 018 §8.3. It does not
authorize implementing Package A, registering the eight contracts in runtime,
implementing Package B, or resolving by implication any Package B element
marked `TO BE DETERMINED`.

It does not authorize creating the temporary role, its Intake permissions or
the temporal resolver; modifying `ROLE_PERMISSIONS` or productive call sites;
or assigning any role or permission to Guillermo de Hoyos or any other person.

It does not authorize migrations, productive data, configuration, secrets,
Google resources, OAuth, Gmail, mailbox access, synchronization, deployment or
a pilot. It does not open §8.5 or any later gate.

Any implementation of Package A, design or implementation of Package B,
effective assignment or closure of §8.3 requires separate later authority.
