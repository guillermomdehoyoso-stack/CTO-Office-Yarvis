# YARVIS
# Netpay MVP-2D1 Contract and Role Allocation Proposal

## Status

**ACCEPTED PROPOSAL — ADR REQUIRED — NO CANONICAL ASSIGNMENT OR IMPLEMENTATION AUTHORITY**

## 1. Purpose and authority boundary

This proposal defines the candidate canonical contract and role allocation
needed to consider the Contract and Role Allocation Gate in §8.3 of
`IMPLEMENTATION_ROADMAP_AMENDMENT_018.md`.

It incorporates Architecture Authority decisions as proposals submitted for
independent review and later ratification. It does not apply those decisions.

While Proposed, this document:

- does not assign or reserve an Interaction Contract identifier;
- does not modify the canonical contract catalog;
- does not create or modify a runtime role or permission;
- does not modify any Principal, Membership or Organization;
- does not register a Handler or Query implementation;
- does not make any Command dispatchable;
- does not authorize implementation, tests, configuration, persistence,
  migration or runtime behavior;
- does not open Amendment 018 §8.3; and
- grants no authority for any later productive gate.

Amendment 018 §8.3 remains closed unless and until this proposal completes
independent review, the required packages are separately ratified and
implemented, their conformance is accepted, and Architecture Authority
expressly closes the gate.

## 2. Governing authority and evidence

This proposal is governed by:

- `IMPLEMENTATION_ROADMAP_AMENDMENT_018.md`;
- `AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md`;
- `IMPLEMENTATION_ROADMAP_AMENDMENT_014.md`;
- `NETPAY_MVP2D_GMAIL_INTAKE_DESIGN.md`;
- `NETPAY_MVP2D1_GMAIL_INTAKE_RATIFICATION_DRAFT.md`;
- the three independent reviews of that ratification draft;
- `NETPAY_MVP2D1_GOVERNANCE_RECONCILIATION_ASSESSMENT.md`;
- `NETPAY_MVP2D1_GOVERNANCE_RECONCILIATION_REVIEW.md`; and
- `NETPAY_MVP2D1_CANONICAL_IDENTITY_GATE_EVIDENCE.md`.

The accepted Canonical Identity evidence satisfies exclusively Amendment 018
§3.2 and §8.2. It confirms an unambiguous productive Principal, Membership and
Organization chain, but assigns no contract, role or permission and grants no
downstream authority.

Historical proposals and reviews provide reviewed semantic boundaries. They do
not themselves allocate canonical identifiers or authorize runtime.

## 3. Current repository baseline

| Field | Value |
| --- | --- |
| Branch | `feat/operational-intake-spine` |
| Local HEAD | `c5ea6faa5c3630986f629b03251dedcf22395b70` |
| Remote reference | `origin/feat/operational-intake-spine` |
| Remote commit | `c5ea6faa5c3630986f629b03251dedcf22395b70` |
| Canonical contract owner module | `netpay_merchant_operations` |
| Canonical owning context | `Netpay Merchant Operations` |
| Current Founder role | `netpay_operations_operator` |
| Current Gmail contract allocation | None |
| Current Gmail Handler registration | None |
| Current Gmail runtime | None |
| Current §8.3 state | Closed |

At this baseline, none of the eight proposed Gmail contracts exists in
`canonical_contracts.py`, the application contract surfaces, the Handler
Registry, the default runtime composition root or production routes.

The current authority resolver maps an active `PrincipalMembership.role`
directly through the active `ROLE_PERMISSIONS` map. It does not consult
temporal assignment state. The repository has no inert executable role catalog
separate from that active map.

The current contract registry recognizes lifecycle values including
`RATIFIED` and operational values including `PLANNED`. It does not define
`gate_closed` as an operational-status enum. In this proposal,
`gate_closed` describes the governing non-dispatchable condition; the proposed
canonical metadata would use lifecycle `RATIFIED` and operational status
`PLANNED`.

## 4. Proposed allocation set

Exactly the following eight contracts are proposed for future canonical
assignment:

| Proposed ID | Type | Semantic name |
| --- | --- | --- |
| `IC-NETPAY-CMD-016` | Command | `ConfigureNetpayGmailConnector` |
| `IC-NETPAY-CMD-017` | Command | `SynchronizeNetpayGmailConnector` |
| `IC-NETPAY-CMD-018` | Command | `ReviewNetpayIntakeCandidate` |
| `IC-NETPAY-QRY-007` | Query | `ListNetpayIntakeCandidates` |
| `IC-NETPAY-QRY-008` | Query | `RetrieveNetpayIntakeCandidate` |
| `IC-NETPAY-EVT-007` | Event | `NetpayIntakeCandidateReceived` |
| `IC-NETPAY-EVT-008` | Event | `NetpayIntakeCandidateReviewed` |
| `IC-NETPAY-EVT-010` | Event | `NetpayGmailConnectorSyncFailed` |

For all eight contracts, the proposed canonical metadata is:

| Field | Proposed value |
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
| `traceability_references` | `("IMPLEMENTATION_ROADMAP_AMENDMENT_018.md", "NETPAY_MVP2D1_CONTRACT_AND_ROLE_ALLOCATION_PROPOSAL.md")` |

These values are proposals only. They do not become canonical merely by
appearing in this document.

`criticality=CORE` is consistent with current canonical Netpay precedent. The
Commercial Intake, Operational Dataset Intake and Service Inbox contract
families all contain contracts with lifecycle `RATIFIED`, operational status
`PLANNED` and criticality `CORE`. `CORE` therefore follows the existing
classification of tenant-authoritative Netpay command, query and event
boundaries; it is not inferred solely from the contracts being `PLANNED`.

Current canonical Netpay definitions omit `architectural_steward` and
`traceability_references`, thereby using the registry defaults `None` and `()`.
This proposal preserves the `None` steward precedent but makes traceability
explicit and ordered for all eight contracts. A future Accepted ADR may add its
own ADR reference only by expressly amending the authorized contract-definition
package; implementation may not infer or invent another reference.

### 4.1 Explicitly excluded identifiers

The following identifiers remain outside MVP-2D1:

- `IC-NETPAY-CMD-019 AcceptNetpayIntakeCandidate`; and
- `IC-NETPAY-EVT-009 NetpayIntakeCandidateAccepted`.

They are not proposed, reserved, assigned or authorized by this document. Their
absence between other numerical identifiers creates no implied reservation.

No MVP-2D1 contract may directly create a `NetpayServiceCase`, invoke
`IC-NETPAY-CMD-009`, create a productive `CommercialIntakeItem`, or perform the
future acceptance semantics deferred beyond MVP-2D1.

## 5. Common contract invariants

If later ratified, every proposed Command and Query must preserve these
invariants:

1. `organization_id` is supplied by the canonical authority envelope and is
   never inferred from Gmail, mailbox data, message data, request headers,
   query parameters or client-provided tenant selectors.
2. The authenticated Principal must have one active, non-revoked Membership in
   the active Organization.
3. Authorization is revalidated before data lookup, receipt lookup or replay.
4. Foreign and missing resources are concealed through the same safe
   not-found result.
5. Commands use Organization-scoped contract identity, idempotency key and
   functional request fingerprint.
6. Identical replay returns the original committed result.
7. Reuse of an idempotency key with a different functional payload fails with
   `IDEMPOTENCY_CONFLICT`.
8. State, receipt, result and Events commit atomically.
9. No provider value can grant authority or select an Organization.
10. No body, HTML, MIME, attachment bytes, token, credential, secret, raw
    provider payload or raw provider exception may enter a contract payload,
    result, Event, receipt, log or error.
11. No contract in this proposal authorizes provider connectivity.
12. Every operation fails closed when identity, Membership, Organization,
    permission, binding, state, version or contract availability is invalid.
13. A `PLANNED` contract remains unavailable to runtime until a separate
    implementation authority explicitly changes its permitted operational
    state and registers its implementation.

Common envelope fields such as correlation, causation, contract identity,
request time, authenticated Principal and canonical Organization remain
governed by existing Yarvis envelope and authority mechanisms. They are not
duplicated as client-controlled payload fields below.

## 6. Proposed Command contracts

### 6.1 IC-NETPAY-CMD-016 — ConfigureNetpayGmailConnector

#### CMD-016 semantic purpose

Define logical configuration and lifecycle transitions for one explicit,
Organization-bound mailbox configuration.

This contract does not perform OAuth, consent, provider discovery, Gmail
communication or credential storage. It carries no secret, token,
authorization code, client identifier, client secret, refresh token or mailbox
content.

#### CMD-016 required permission

`netpay.intake.connect`

#### CMD-016 proposed payload

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `mailbox_configuration_id` | UUID | Conditional | Required for lifecycle changes; absent only when logically creating the initial configuration. |
| `operation` | Enum | Yes | Exactly one of `configure`, `pause`, `resume`, `disconnect`. |
| `mailbox_binding_key` | Opaque non-secret string | Conditional | Required for `configure`; stable logical binding reference only. It is not an address, token or provider credential. |
| `label_binding_key` | Opaque non-secret string | Conditional | Required for `configure`; logical reference only. It is not a provider lookup authorization. |
| `expected_version` | Positive integer | Conditional | Required when changing an existing configuration. |
| `reason_code` | Controlled enum | Conditional | Required for `pause` and `disconnect`; no free-text provider error or secret. |

The closed initial CMD-016 `reason_code` values are:

- `operator_pause`;
- `authorization_pending`;
- `binding_invalid`;
- `security_review`;
- `operator_disconnect`.

The operation matrix is exact:

| Operation | Required fields | Prohibited fields | Permitted prior state | Resulting state | Permitted `reason_code` | `expected_version` | Replay |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `configure` | `operation`, `mailbox_binding_key`, `label_binding_key` | `mailbox_configuration_id`, `reason_code` | No configuration with the supplied logical binding identity | `configured` with a newly generated `mailbox_configuration_id` | None | Prohibited | Same idempotency key and identical functional payload returns the original created result. |
| `pause` | `operation`, `mailbox_configuration_id`, `expected_version`, `reason_code` | `mailbox_binding_key`, `label_binding_key` | `configured` | `paused` | `operator_pause`, `authorization_pending`, `binding_invalid`, `security_review` | Must equal the current committed version | Identical replay returns the original committed paused result. |
| `resume` | `operation`, `mailbox_configuration_id`, `expected_version` | `mailbox_binding_key`, `label_binding_key`, `reason_code` | `paused` | `configured` | None | Must equal the current committed version | Identical replay returns the original committed resumed result. |
| `disconnect` | `operation`, `mailbox_configuration_id`, `expected_version`, `reason_code` | `mailbox_binding_key`, `label_binding_key` | `configured` or `paused` | `disconnected` | `operator_disconnect`, `binding_invalid`, `security_review` | Must equal the current committed version | Identical replay returns the original committed disconnected result. |

Every field not listed as required is prohibited for that operation. A
different functional payload under the same idempotency key fails with
`IDEMPOTENCY_CONFLICT`. A stale `expected_version` fails with
`VERSION_CONFLICT` before mutation.

`disconnected` is terminal for that `mailbox_configuration_id`. A later
`configure` operation must create a new `mailbox_configuration_id`; it cannot
resume, replace or reanimate the disconnected configuration.

`resume` may only leave a logical paused state. It cannot assert that OAuth,
credentials, Gmail access or provider readiness exists.

#### CMD-016 proposed result

| Field | Type | Rule |
| --- | --- | --- |
| `mailbox_configuration_id` | UUID | Safe internal identifier. |
| `organization_id` | UUID | Must equal the authority-envelope Organization. |
| `lifecycle_status` | Enum | One of `configured`, `paused`, `disconnected`. |
| `version` | Positive integer | Committed aggregate version. |
| `replayed` | Boolean | Indicates identical command replay. |
| `provider_access_enabled` | Boolean | Must remain `false` under any package limited to this contract-allocation proposal. |

The result contains no mailbox address, provider identifier, credential
reference, token, secret, label name or provider response.

#### CMD-016 proposed errors

- `AUTHORIZATION_DENIED`
- `VALIDATION_ERROR`
- `RESOURCE_NOT_FOUND`
- `VERSION_CONFLICT`
- `IDEMPOTENCY_CONFLICT`
- `INVALID_LIFECYCLE_TRANSITION`
- `BINDING_CONFLICT`
- `CONTRACT_NOT_OPERATIONAL`

Every error is sanitized and contains only a controlled reason code,
correlation identifier and safe internal resource type.

### 6.2 IC-NETPAY-CMD-017 — SynchronizeNetpayGmailConnector

#### CMD-017 semantic purpose

Represent a future human-triggered synchronization request for one explicit
mailbox configuration.

Assignment of this semantic contract would not enable synchronization. It must
remain unregistered, non-dispatchable and fail closed until a later
implementation gate expressly authorizes its Handler, provider boundary,
persistence effects and runtime composition.

#### CMD-017 required permission

`netpay.intake.connect`

#### CMD-017 proposed payload

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `mailbox_configuration_id` | UUID | Yes | Must resolve within the authority-envelope Organization. |
| `trigger_kind` | Enum | Yes | The only MVP-2D1 value is `manual`. |
| `manifest_id` | UUID | Conditional | Required only by a separately authorized real-pilot gate. Its presence here grants no pilot authority. |
| `expected_checkpoint_version` | Non-negative integer | Yes | Prevents stale or concurrent cursor advancement. |

No cursor value, mailbox address, label value, provider message identifier,
query, token, secret or provider payload is client-supplied.

Validation and failure precedence is exact and stops at the first failing row:

| Precedence | Phase | Condition | Channel |
| --- | --- | --- | --- |
| 1 | Operational availability | Contract is not dispatchable under its canonical lifecycle and operational status. | Contract error `CONTRACT_NOT_OPERATIONAL`; no admitted sync, result or Event. |
| 2 | Authority | Identity, Organization, Membership or `netpay.intake.connect` authority is absent, inactive, revoked, ambiguous or inconsistent. | Contract error `AUTHORIZATION_DENIED`; no admitted sync, result or Event. |
| 3 | Validation | Payload shape, `trigger_kind` or conditional manifest rule is invalid. | Contract error `VALIDATION_ERROR`; no admitted sync, result or Event. |
| 4 | Resource lookup | Configuration is missing or foreign. | Concealed contract error `RESOURCE_NOT_FOUND`; no admitted sync, result or Event. |
| 5 | Idempotency and replay | The key is an identical replay, or is reused with a different functional payload. | Identical replay returns the original committed result; changed payload returns `IDEMPOTENCY_CONFLICT`. No new sync is admitted. |
| 6 | Version and concurrency | `expected_checkpoint_version` is stale or conflicts with the active checkpoint. | Contract error `VERSION_CONFLICT`; no admitted sync, result or Event. |
| 7 | Connector state | The logical connector is paused, disconnected or otherwise disabled. | Contract error `CONNECTOR_DISABLED`; no admitted sync, result or Event. |
| 8 | Binding | Mailbox or label binding is absent, invalid or ambiguous. | Contract error `BINDING_INVALID` or `LABEL_BINDING_INVALID`; no admitted sync, result or Event. |
| 9 | Retention | Retention, purge, legal-hold or readback state blocks ingestion. | Contract error `RETENTION_BLOCKED`; no admitted sync, result or Event. |
| 10 | Credential state | A later authorized credential reference is absent, revoked, expired or invalid. | Contract error `CREDENTIAL_STATE_INVALID`; no admitted sync, result or Event. |
| 11 | Mutual exclusion | Another admitted sync owns the applicable lease or exclusion boundary. | Contract error `SYNC_ALREADY_IN_PROGRESS`; no admitted sync, result or Event. |
| 12 | Execution and batch | Any failure occurs after sync admission and before successful commit. | The sole Dispatcher-owned Unit of Work rolls back completely and CMD-017 terminates with `SYNC_FAILED_CLOSED`; no result, receipt or Event is claimed as durable. |

Rows 1 through 11 are pre-admission failures. They never commit a sync result,
sync failure receipt or EVT-010. Every row-12 failure before commit rolls back
the complete, sole Unit of Work owned by Dispatcher. After rollback, CMD-017
terminates with `SYNC_FAILED_CLOSED` and does not claim that a durable result,
receipt or Event exists.

The CMD-017 Handler never opens a second Unit of Work and never creates or
controls an independent nested transaction. This proposal does not authorize a
second Unit of Work, background task, alternate outbox, savepoint or equivalent
post-failure mechanism.

If the commit itself fails, the ratified Dispatch and Unit-of-Work semantics
preserve the primary exception. CMD-017 promises no subsequent write, receipt
or Event. Absence of EVT-010 after rollback or commit failure must never be
interpreted as success.

Any durable recording after such a failure requires a separate contract, a
later Accepted ADR, an exact Authorized File Boundary, its own Evidence Gate
and explicit implementation authority.

#### CMD-017 proposed result

| Field | Type | Rule |
| --- | --- | --- |
| `sync_request_id` | UUID | Safe internal request identifier. |
| `mailbox_configuration_id` | UUID | Safe internal configuration identifier. |
| `status` | Constant | Exactly `completed`. No failure or asynchronous acceptance state exists in a durable CMD-017 result. |
| `candidate_count` | Non-negative integer | Counts exclusively candidates in the complete committed batch. |
| `checkpoint_advanced` | Boolean | Reflects exclusively whether the checkpoint of that complete batch committed. |
| `failure_code` | Null | Exactly `null`; failures terminate through a contractual error and produce no result object. |
| `replayed` | Boolean | Indicates identical command replay. |

These result fields define a future semantic boundary. They do not authorize a
sync implementation, cursor, candidate persistence or provider access.

Identical replay exists only for a previously committed successful result and
returns that same result, including the same IDs and `completed` status. A
failed attempt with no committed receipt creates no replayable success. Reuse
of an existing committed idempotency key with a different functional payload
always returns `IDEMPOTENCY_CONFLICT` and cannot admit a second sync.

#### CMD-017 proposed errors

- `CONTRACT_NOT_OPERATIONAL`
- `AUTHORIZATION_DENIED`
- `VALIDATION_ERROR`
- `RESOURCE_NOT_FOUND`
- `IDEMPOTENCY_CONFLICT`
- `VERSION_CONFLICT`
- `CONNECTOR_DISABLED`
- `BINDING_INVALID`
- `LABEL_BINDING_INVALID`
- `RETENTION_BLOCKED`
- `CREDENTIAL_STATE_INVALID`
- `SYNC_ALREADY_IN_PROGRESS`
- `SYNC_FAILED_CLOSED`

Until a later gate changes runtime authority, every attempted dispatch must
resolve to `CONTRACT_NOT_OPERATIONAL` or the equivalent governed `gate_closed`
response before provider access or mutation.

### 6.3 IC-NETPAY-CMD-018 — ReviewNetpayIntakeCandidate

#### CMD-018 semantic purpose

Record an explicit human review of one tenant-owned candidate. Review may
confirm or correct the proposed classification, request further correction, or
reject the candidate. It does not create a case or definitive business entity.

#### CMD-018 required permission

`netpay.intake.review`

#### CMD-018 proposed payload

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `candidate_id` | UUID | Yes | Must belong to the authority-envelope Organization. |
| `decision` | Enum | Yes | Exactly one of `accept_classification`, `correct_classification`, `reject_candidate`, `request_correction`. |
| `corrected_category` | Closed category enum or null | Conditional | Governed exclusively by the decision matrix below. |
| `reason_code` | Controlled enum | Yes | No unrestricted provider-derived or sensitive free text. |
| `expected_version` | Positive integer | Yes | Prevents concurrent replacement of a decision. |

The closed category catalog is:

- `commercial_contact_or_rfq`;
- `tpv_physical`;
- `ecommerce`;
- `support_or_incident`;
- `unclassified`.

The closed initial CMD-018 `reason_code` values are:

- `classification_confirmed`;
- `classification_corrected`;
- `insufficient_information`;
- `not_relevant`;
- `duplicate_candidate`;
- `requires_human_follow_up`.

The decision matrix is exact:

| `decision` | `corrected_category` | Allowed `reason_code` | Result `effective_category` | Result `review_status` |
| --- | --- | --- | --- | --- |
| `accept_classification` | Prohibited | `classification_confirmed` | Original proposed category | `classification_accepted` |
| `correct_classification` | Required and different from the proposed category | `classification_corrected` | Corrected category | `classification_corrected` |
| `reject_candidate` | Prohibited | `not_relevant`, `duplicate_candidate` | `null` | `rejected` |
| `request_correction` | Prohibited | `insufficient_information`, `requires_human_follow_up` | `null` | `correction_requested` |

Any combination not present in this matrix fails with
`DECISION_PAYLOAD_INVALID` before mutation. In particular, a corrected category
equal to the proposed category is invalid, and neither rejection nor correction
request carries an effective category.

`accept_classification` and `correct_classification` establish only a human
classification outcome. Neither is acceptance into a Case, Master or
Commercial Intake aggregate.

A candidate with a committed terminal review cannot be silently re-decided.
Any later correction semantics require a separately defined, auditable command
or an expressly ratified amendment.

#### CMD-018 proposed result

| Field | Type | Rule |
| --- | --- | --- |
| `candidate_id` | UUID | Safe candidate identifier. |
| `review_status` | Enum | Exactly one of `classification_accepted`, `classification_corrected`, `rejected`, `correction_requested`. |
| `effective_category` | Closed category enum or null | Original category for `classification_accepted`, corrected category for `classification_corrected`, otherwise `null`. |
| `reviewed_by_principal_id` | UUID | Canonical actor identifier; never inferred from payload. |
| `version` | Positive integer | Committed aggregate version. |
| `commercial_intake_projection_exists` | Boolean | Informational only; this Command cannot create productive Commercial Intake under this proposal. |
| `replayed` | Boolean | Indicates identical command replay. |

The result contains no full body, HTML, MIME, sender or recipient address,
subject, provider message identifier, attachment name, token or secret.

#### CMD-018 proposed errors

- `AUTHORIZATION_DENIED`
- `VALIDATION_ERROR`
- `RESOURCE_NOT_FOUND`
- `VERSION_CONFLICT`
- `IDEMPOTENCY_CONFLICT`
- `CANDIDATE_ALREADY_REVIEWED`
- `CATEGORY_NOT_ALLOWED`
- `DECISION_NOT_ALLOWED`
- `DECISION_PAYLOAD_INVALID`
- `CONTRACT_NOT_OPERATIONAL`

AI, classification rules and sync code may propose a category but may never
produce any of the four decisions, supply the authenticated human decision, or
supply `reviewed_by_principal_id`.

## 7. Proposed Query contracts

### 7.1 IC-NETPAY-QRY-007 — ListNetpayIntakeCandidates

#### QRY-007 semantic purpose

Return a tenant-scoped list of safe candidate summaries and an allowlisted
connector-health summary.

#### QRY-007 required permission

`netpay.intake.read`

#### QRY-007 proposed request

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `status` | Closed enum or null | No | One of `pending`, `classification_accepted`, `classification_corrected`, `rejected`, `correction_requested`, or null for no status filter. |
| `category` | Closed category enum or null | No | Filter by the §6.3 category catalog. |
| `mailbox_configuration_id` | UUID or null | No | Must resolve inside the authority-envelope Organization. |
| `cursor` | Opaque protected pagination token or null | No | Internal token encoding Organization, normalized filters, position and expiry with integrity protection. Alteration, expiry or Organization/filter mismatch fails validation. It is never a Gmail or provider cursor. |
| `limit` | Integer | Yes | Range `1..100`. |

#### QRY-007 proposed result

| Field | Type | Nullable | Closed values | Authority rule | Definition relative to §8.5 |
| --- | --- | --- | --- | --- | --- |
| `items` | Sequence of `CandidateSummary` | No | Length `0..limit` | Every item belongs to the authority-envelope Organization. | Shape defined; privacy-gated members remain `null`. No runtime availability is granted. |
| `next_cursor` | Opaque protected pagination token | Yes | `null` when no next page | Binds Organization, normalized filters, position and expiry under integrity protection; invalid or altered tokens fail closed. Never a provider cursor. | Shape defined; no runtime availability is granted. |
| `total_count` | Non-negative integer | No | Integer `>=0` | Counts only candidates in the authority-envelope Organization after authorized filters. | Shape defined; no runtime availability is granted. |
| `connector_health` | `SafeConnectorHealth` | Yes | Exact structure below | Returned only for an authorized configuration in the same Organization. | Shape defined as allowlisted operational metadata; no runtime availability is granted. |

`CandidateSummary` contains exactly:

| Field | Type | Nullable | Closed values | Authority rule | Definition relative to §8.5 |
| --- | --- | --- | --- | --- | --- |
| `candidate_id` | UUID | No | N/A | Same Organization; foreign and missing values are never exposed. | Shape defined; no runtime availability is granted. |
| `mailbox_configuration_id` | UUID | No | N/A | Must resolve in the same Organization. | Shape defined; no runtime availability is granted. |
| `proposed_category` | Closed category enum | No | The five values in §6.3 | Tenant-owned classification proposal only. | Shape defined; no runtime availability is granted. |
| `effective_category` | Closed category enum | Yes | The five values in §6.3 or `null` | Non-null only for `classification_accepted` or `classification_corrected`. | Shape defined; no runtime availability is granted. |
| `review_status` | Closed enum | No | `pending`, `classification_accepted`, `classification_corrected`, `rejected`, `correction_requested` | Represents only the tenant-owned human-review state. | Shape defined; no runtime availability is granted. |
| `sanitized_excerpt` | UTF-8 plain text, maximum 4096 bytes | Yes | N/A | Never supplies tenant or authority; no prohibited source content. | Must be `null` until §8.5 accepts productive sanitization, redaction and readback. |
| `received_at` | UTC timestamp | Yes | N/A | Tenant-scoped approved metadata; never used as authority. | Must be `null` until §8.5 accepts this productive metadata field. |
| `commercial_intake_projection_exists` | Boolean | No | `true`, `false` | Informational boundary projection only; grants no Commercial Intake authority. | Shape defined; no runtime availability is granted. |
| `version` | Positive integer | No | Integer `>=1` | Version of the tenant-owned candidate projection. | Shape defined; no runtime availability is granted. |

`SafeConnectorHealth` contains exactly:

| Field | Type | Nullable | Closed values | Authority rule | Definition relative to §8.5 |
| --- | --- | --- | --- | --- | --- |
| `mailbox_configuration_id` | UUID | No | N/A | Same Organization only. | Shape defined; no runtime availability is granted. |
| `lifecycle_status` | Closed enum | No | `configured`, `paused`, `disconnected` | Same authorized logical configuration. | Shape defined; no runtime availability is granted. |
| `last_sync_status` | Closed enum | Yes | `completed`, or `null` if no successful sync exists | Aggregate safe status only. A CMD-017 failure creates no durable status result. | Shape defined; no runtime availability is granted. |
| `candidate_count` | Non-negative integer | No | Integer `>=0` | Same-Organization aggregate only. | Shape defined; no runtime availability is granted. |
| `error_code` | Closed safe enum | Yes | EVT-010 failure codes or `null` | Non-null only if a separately authorized future producer created durable safe failure evidence; never inferred from missing EVT-010. | Shape defined; no runtime availability is granted. |
| `checkpoint_available` | Boolean | No | `true`, `false` | Reveals no cursor value. | Shape defined; no runtime availability is granted. |

It contains no mailbox address, sender, recipient, subject, body, HTML, MIME,
provider message identifier, attachment name, provider cursor, credential,
token, raw exception or provider response.

#### QRY-007 proposed errors

- `AUTHORIZATION_DENIED`
- `VALIDATION_ERROR`
- `RESOURCE_NOT_FOUND`
- `CATEGORY_NOT_ALLOWED`
- `CONTRACT_NOT_OPERATIONAL`

### 7.2 IC-NETPAY-QRY-008 — RetrieveNetpayIntakeCandidate

#### QRY-008 semantic purpose

Return one safe, tenant-scoped candidate detail for human review.

#### QRY-008 required permission

`netpay.intake.read`

#### QRY-008 proposed request

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `candidate_id` | UUID | Yes | Must resolve inside the authority-envelope Organization. |

#### QRY-008 proposed result

`CandidateDetail` contains exactly:

| Field | Type | Nullable | Closed values | Authority rule | Definition relative to §8.5 |
| --- | --- | --- | --- | --- | --- |
| `candidate_id` | UUID | No | N/A | Must belong to the authority-envelope Organization. | Shape defined; no runtime availability is granted. |
| `mailbox_configuration_id` | UUID | No | N/A | Must resolve in the same Organization. | Shape defined; no runtime availability is granted. |
| `provenance_kind` | Closed enum | No | `synthetic`, `external_provider` | Classification only; no provider identifier or payload. | `synthetic` is usable only in an authorized synthetic package; `external_provider` remains unavailable until §8.5 and later provider gates allow productive data. |
| `provenance_reference` | Opaque internal reference | Yes | N/A | Same-Organization internal reference; never a provider message or thread identifier. | Must be `null` for productive data until §8.5 accepts the field. |
| `proposed_category` | Closed category enum | No | The five values in §6.3 | Tenant-owned proposal only. | Shape defined; no runtime availability is granted. |
| `effective_category` | Closed category enum | Yes | The five values in §6.3 or `null` | Non-null only for accepted or corrected classification. | Shape defined; no runtime availability is granted. |
| `review_status` | Closed enum | No | `pending`, `classification_accepted`, `classification_corrected`, `rejected`, `correction_requested` | Human-review state only. | Shape defined; no runtime availability is granted. |
| `review_reason_code` | Closed enum | Yes | CMD-018 reasons or `null` while pending | Human decision metadata only. | Shape defined; no runtime availability is granted. |
| `sanitized_excerpt` | UTF-8 plain text, maximum 4096 bytes | Yes | N/A | Never supplies tenant or authority; no prohibited source content. | Must be `null` until §8.5 accepts productive sanitization, redaction and readback. |
| `attachment_metadata` | Null | Yes | Exactly `null` | Contractually reserved; conveys no attachment information. | Must remain exactly `null` until a later Accepted ADR following §8.5 expressly modifies this contract. |
| `reviewed_by_principal_id` | UUID | Yes | N/A | Canonical actor from the authority envelope; never client or provider supplied. | Shape defined; no runtime availability is granted. |
| `reviewed_at` | UTC timestamp | Yes | N/A | Canonical commit time; never an authority source. | Shape defined; no runtime availability is granted. |
| `commercial_intake_projection_exists` | Boolean | No | `true`, `false` | Informational only; this Query cannot create the projection. | Shape defined; no runtime availability is granted. |
| `commercial_intake_projection_reference` | UUID | Yes | N/A | Same-Organization safe internal reference, only if separately authorized and already existent. | Available only after the separate Commercial Intake boundary authorizes the projection; otherwise `null`. |
| `version` | Positive integer | No | Integer `>=1` | Current tenant-owned candidate version. | Shape defined; no runtime availability is granted. |

`attachment_metadata` is a contractually reserved nullable field and must
remain exactly `null`. This proposal does not define `SafeAttachmentMetadata`.
A later Accepted ADR following §8.5 must define its exact fields and closed
enums and expressly modify this contract before any non-null value is permitted.
No filename, provider part identity, content, bytes or unrestricted media type
is returned.

“Defined before §8.5” describes contract shape only and never runtime
availability. QRY-007 and QRY-008 remain unavailable until separately
implemented and made operational. No productive candidate field may be read or
populated before all applicable productive gates pass.

It never returns complete body, HTML, MIME, addresses, subject, raw headers,
provider message or thread identifiers, attachment names or bytes, credentials,
tokens, secrets, provider errors or raw provider payloads.

#### QRY-008 proposed errors

- `AUTHORIZATION_DENIED`
- `VALIDATION_ERROR`
- `RESOURCE_NOT_FOUND`
- `CONTRACT_NOT_OPERATIONAL`

Missing and foreign candidates produce the same concealed
`RESOURCE_NOT_FOUND` response.

## 8. Proposed Event contracts

All Event timestamps, trace identifiers, correlation identifiers and causation
identifiers must use existing canonical event conventions. Event payloads are
immutable, tenant-scoped and safe for durable audit. They cannot contain the
candidate excerpt.

### 8.1 IC-NETPAY-EVT-007 — NetpayIntakeCandidateReceived

The EVT-007 payload contains exactly:

| Field | Type |
| --- | --- |
| `organization_id` | UUID |
| `candidate_id` | UUID |
| `mailbox_configuration_id` | UUID |
| `proposed_category` | Closed category enum |
| `review_status` | Constant `pending` |
| `manifest_id` | UUID or null |
| `occurred_at` | UTC timestamp |
| `correlation_id` | UUID |
| `causation_id` | UUID |

No provider message identifier, mailbox address, sender, recipient, subject,
excerpt, body, HTML, MIME, attachment data, credential or token is allowed.

### 8.2 IC-NETPAY-EVT-008 — NetpayIntakeCandidateReviewed

The EVT-008 payload contains exactly:

| Field | Type |
| --- | --- |
| `organization_id` | UUID |
| `candidate_id` | UUID |
| `mailbox_configuration_id` | UUID |
| `decision` | Closed decision enum from §6.3 |
| `previous_category` | Closed category enum |
| `effective_category` | Closed category enum or null, according to the §6.3 decision matrix |
| `review_status` | Closed review-status enum from §6.3 |
| `reason_code` | Closed reason enum from §6.3 |
| `reviewed_by_principal_id` | UUID |
| `occurred_at` | UTC timestamp |
| `correlation_id` | UUID |
| `causation_id` | UUID |

This Event records a human review. AI, a classifier, sync execution or provider
input cannot populate or impersonate `reviewed_by_principal_id`.

### 8.3 IC-NETPAY-EVT-010 — NetpayGmailConnectorSyncFailed

EVT-010 remains a `RATIFIED` / `PLANNED` semantic contract with no runtime
producer assigned or authorized by this proposal. CMD-017 does not guarantee
that EVT-010 is emitted after rollback or commit failure, and the Event remains
non-operational.

The EVT-010 payload contains exactly:

| Field | Type |
| --- | --- |
| `organization_id` | UUID |
| `mailbox_configuration_id` | UUID |
| `sync_request_id` | UUID |
| `failure_code` | Controlled safe enum |
| `checkpoint_advanced` | Constant `false` |
| `candidate_count_committed` | Constant `0` for this failed `sync_request_id` batch |
| `occurred_at` | UTC timestamp |
| `correlation_id` | UUID |
| `causation_id` | UUID |

The closed initial failure-code catalog is:

- `contract_not_operational`;
- `connector_disabled`;
- `binding_invalid`;
- `label_binding_invalid`;
- `credential_state_invalid`;
- `retention_blocked`;
- `provider_unavailable`;
- `provider_rate_limited`;
- `batch_validation_failed`;
- `batch_commit_failed`;
- `unexpected_failure`.

`unexpected_failure` contains no exception text. Provider response codes,
payloads, addresses, message identifiers, query strings, tokens, credentials,
URLs and stack traces are prohibited.

The Event records a safe failure fact only. It does not authorize retry,
provider access, cursor movement or continued synchronization.

EVT-010 contains no historical candidate count. Any future historical aggregate
requires a separately named field and contract amendment and cannot be
represented as candidates committed by the failed batch.

Any future producer requires a separate Accepted ADR, Authorized File Boundary,
Evidence Gate and proof of compatibility with ADR-017's single Dispatcher-owned
Unit of Work. Allocation of EVT-010 grants no authority for a second Unit of
Work, background task, alternate outbox, savepoint or other transaction
boundary. If a later authorized mechanism produces EVT-010, its invariants
remain `checkpoint_advanced=false` and `candidate_count_committed=0`.

## 9. Proposed permissions

Exactly these three new permissions are proposed semantically:

| Permission | Meaning |
| --- | --- |
| `netpay.intake.read` | Read tenant-scoped safe candidate summaries, details and allowlisted connector health. |
| `netpay.intake.connect` | Perform separately authorized logical connector configuration and manual-trigger operations. |
| `netpay.intake.review` | Record separately authorized human candidate-review decisions. |

The permissions are independent. Possession of one never implies another.

In particular:

- `read` cannot configure, trigger or review;
- `connect` cannot review a candidate;
- `review` cannot configure, connect, pause, resume, disconnect or trigger a
  connector;
- none authorizes Gmail, OAuth, secrets, provider connectivity, productive
  persistence or implementation merely by being defined; and
- every runtime use requires a separately authorized contract, implementation,
  active Membership, canonical temporal assignment and authority check.

These permissions remain absent from runtime until the complete expiry-aware
role package is separately authorized and implemented.

## 10. Temporary pilot role proposal

### 10.1 Proposed role

For a single-person pilot only, this proposal semantically defines the
temporary composite role name:

`netpay_intake_pilot_operator`

Its proposed effective permission set during a valid temporary assignment is
exactly:

```text
netpay.master.read
netpay.master.manage
netpay.inbox.read
netpay.inbox.manage
netpay.intake.read
netpay.intake.connect
netpay.intake.review
```

The first four permissions preserve exactly the authority already provided by
`netpay_operations_operator`. They are not new permissions and this proposal
does not redefine them.

The only proposed new permissions are:

```text
netpay.intake.read
netpay.intake.connect
netpay.intake.review
```

This section defines seven effective permissions as the dynamic union of four
static base permissions and three temporary Intake capabilities. It does not
describe seven entries in the static role map and does not authorize adding the
role or the three Intake permissions to active runtime.

The current resolver maps `PrincipalMembership.role` directly through
`ROLE_PERMISSIONS` without consulting temporal assignment state. Adding the
temporary role to that active map before introducing expiry-aware resolution
would create non-expiring runtime authority. It is therefore prohibited.

No inert executable role catalog exists in the current repository. This
proposal does not create or authorize one.

The role may enter `ROLE_PERMISSIONS` only with the four base Master/Inbox
permissions. The three Intake permissions must never be values returned by
`permissions_for_role("netpay_intake_pilot_operator")` alone. They become
effective exclusively when a separately authorized expiry-aware resolver adds
them after validating one active, effective, unexpired, unrevoked, timely
reviewed and unambiguous canonical assignment.

The static role entry, temporary Intake capabilities and temporal resolution
may enter active runtime only as part of a separately authorized expiry-aware
role package that atomically adds:

- the canonical temporary-assignment source;
- any separately authorized persistence and migration;
- status-, review- and expiry-aware authority resolution;
- the static composite role definition containing exactly the four base
  permissions;
- the three separately represented temporary Intake permission definitions;
- preservation of the four base permissions;
- restoration and reconciliation behavior; and
- the complete operational Evidence Gate.

No Radar, Governance, Identity, Document, Mission, Task, Process, OAuth,
secret-store, deployment or provider permission is included.

### 10.2 Logical separation

The composite role does not merge the meaning of connector administration and
candidate review.

Logical separation is preserved through:

- independent permission checks for every read, connector and review action;
- distinct contract identities;
- distinct command receipts;
- distinct Event types;
- differentiated audit action codes;
- separate correlation and causation chains;
- explicit actor attribution;
- prohibition on sync or classification code recording a human review; and
- prohibition on review code performing connector lifecycle actions.

This is logical separation within one accountable Principal. It is not
separation between two people and must not be represented as dual control,
four-eyes approval or independent reviewer oversight.

### 10.3 Temporary representation exception

`netpay_intake_pilot_operator` is a temporary pilot representation exception
required by the current one-role-per-Membership model.

Three states must remain distinct:

1. the semantic role definition ratified through a future Accepted ADR;
2. the active runtime role-map entry, which remains prohibited until the
   expiry-aware role package is implemented atomically; and
3. an effective temporary assignment, whose authority depends on canonical,
   durable, expiry-aware assignment state.

Ratification of the semantic definition does not add the role to runtime.
Adding the eight contract definitions does not add the role to runtime. The
runtime role entry and its temporal resolver behavior must enter together in
the separately authorized expiry-aware package.

Once that complete mechanism exists, the static role definition may remain in
the active map after a pilot ends with exactly the four base permissions. The
role string alone must never enable the three Intake permissions. Effective
Intake authority always requires a valid canonical temporary assignment.

This is not the definitive multi-role architecture and does not decide whether
Yarvis should later support:

- multiple roles on one Membership;
- role assignments as separate entities;
- scoped grants;
- policy composition;
- dual control; or
- distinct connector administrator and reviewer Principals.

Any definitive multi-role design requires its own proposal, review, Accepted
ADR, migration boundary and implementation authority.

This proposal does not expand the current Membership model, create a second
Principal for Guillermo or select a persistence representation for temporary
assignments.

### 10.4 Existing role remains unchanged

`netpay_operations_operator` remains byte-for-byte semantically unchanged:

- `netpay.master.read`;
- `netpay.master.manage`;
- `netpay.inbox.read`; and
- `netpay.inbox.manage`.

The temporary composite role preserves those four permissions without
modifying the existing role definition.

No existing role gains Intake authority by implication.

### 10.5 Required temporary transition

The intended authority lifecycle remains:

```text
netpay_operations_operator
→ netpay_intake_pilot_operator
→ netpay_operations_operator
```

This expresses the temporary effective authority lifecycle. It does not
authorize implementing that lifecycle through an unguarded replacement of
`PrincipalMembership.role`.

A simple `UPDATE PrincipalMembership.role` is prohibited unless and until a
separately ratified expiry-aware canonical assignment mechanism exists and the
productive authority resolver enforces its status, review deadline, expiry and
revocation.

The future canonical assignment source must record at minimum:

- assignment ID;
- target Membership;
- prior role;
- temporary role;
- effective time;
- mandatory review deadline;
- expiry time;
- assignment status;
- authority reference; and
- optimistic-concurrency token.

The future operational design must also represent whether the mandatory day-14
review was completed under valid authority. This proposal does not select a
table, model, migration, repository, service, filename or physical storage
representation.

The canonical assignment source—not an audit log—must govern whether temporary
Intake authority is effective and which prior role is eligible for restoration.

Audit records must reflect assignment, review, expiry, revocation and
restoration, but they are evidence only. They are not the sole canonical source
for permission resolution or restoration.

No effective pilot-role assignment may occur until an Accepted ADR separately
authorizes an expiry-aware canonical assignment mechanism and its productive
authority-resolution checks.

The future expiry-aware role package may define the machinery required to make
this lifecycle possible, but it may not perform the productive assignment.

After that mechanism is implemented and conformant, a separate operational
Architecture Authority act and transaction remain mandatory before any
productive Membership receives the temporary role.

Neither this proposal, a future Accepted ADR, the contract-definition package
nor the expiry-aware role package assigns the role by implication.

## 11. Intended temporary assignee and operational separation

Guillermo de Hoyos is the intended candidate for a future temporary assignment
on the already verified canonical Principal, Membership and Organization
chain.

This proposal does not publish the Principal or Membership UUID and does not
modify that Membership.

Before any effective assignment, a separately ratified operational design must
define an expiry-aware canonical assignment mechanism. That mechanism must:

1. resolve the canonical Principal, active Membership and active Organization
   through the existing authority path;
2. require the Membership's prior role to be exactly
   `netpay_operations_operator`;
3. fail closed without mutation if the prior role is missing, changed, unknown
   or unexpected;
4. create exactly one unambiguous canonical temporary-assignment record;
5. record the assignment ID, target Membership, exact prior role, temporary
   role, effective time, review deadline, expiry time, status, authority
   reference and optimistic-concurrency token;
6. preserve a canonical indication of whether the mandatory review has been
   completed under valid authority;
7. use an idempotency key and functional request fingerprint;
8. make identical replay return the original committed result;
9. reject changed-payload replay as an idempotency conflict;
10. use optimistic concurrency against the Membership and assignment state;
11. prevent overlapping or ambiguous temporary assignments;
12. preserve the four existing Netpay Master and Inbox permissions throughout
    the temporary lifecycle and restoration reconciliation;
13. leave Principal, Person, Identity Binding and Organization unchanged;
14. write separate audit evidence reflecting the canonical assignment without
    treating that audit evidence as the source of authority;
15. commit canonical assignment state, receipt and audit evidence atomically;
    and
16. roll back every mutation if canonical state, receipt or audit evidence
    cannot commit.

Before the role is usable, every productive call site that constructs or
validates authority from `permissions_for_role` must migrate atomically to the
expiry-aware resolution path. At the reviewed baseline this inventory includes:

- `AuthorityResolutionService.resolve`;
- `ProductiveSessionService.create`;
- `ProductiveSessionService.authenticate`; and
- Governance role validation that calls `permissions_for_role` before
  Membership activation.

The future package must repeat this inventory against its own HEAD and include
every additional direct or indirect call site found. No residual productive
path may obtain Intake permission from the role string alone.

The future productive authority resolver must evaluate the canonical temporary
assignment on every operation requiring an Intake permission.

It must deny all three Intake permissions immediately when:

- no unique canonical assignment exists;
- the assignment is not active;
- the effective time has not arrived;
- the assignment has expired;
- the assignment has been revoked;
- the mandatory day-14 review deadline has passed without a valid completed
  review;
- the assignment does not match the active Membership;
- the Membership no longer has the expected state;
- the authority reference is invalid;
- the concurrency state is stale; or
- any assignment ambiguity or inconsistency exists.

This denial must not depend on physical restoration of
`PrincipalMembership.role`. Intake access fails closed immediately even when
restoration remains pending.

While restoration is pending, the resolver must preserve only the four
pre-existing permissions represented by `netpay_operations_operator`:

```text
netpay.master.read
netpay.master.manage
netpay.inbox.read
netpay.inbox.manage
```

The static `ROLE_PERMISSIONS["netpay_intake_pilot_operator"]` entry provides
exactly those four base permissions. The additional three Intake permissions
become effective only through a valid, active, reviewed, unexpired and
unambiguous canonical temporary assignment.

An audit record alone cannot make the assignment active, preserve it, extend it
or authorize restoration.

`PrincipalMembership` currently has no dedicated integer `version` column. It
inherits `updated_at` from `TimestampedUUIDMixin`. A future operational design
must therefore either:

- use a verified atomic compare-and-swap token based on persisted assignment
  state and the Membership's expected `updated_at`, role and status; or
- obtain separate authority for an explicit version mechanism.

It may not perform an unchecked read-then-write update.

No specific mutation or persistence implementation is authorized here.

The required authority and implementation sequence is:

1. independent review of this proposal;
2. an Accepted ADR ratifying the eight contract assignments, the semantic
   seven-permission temporary-role definition, the three new Intake permissions
   and the separation between definitions, runtime mechanism and assignment;
3. a first bounded package adding only the eight contracts as `RATIFIED` and
   `PLANNED`;
4. conformance review and Architecture Authority acceptance of that package;
5. a separate operational-design proposal for the expiry-aware canonical
   assignment mechanism and productive authority-resolution checks;
6. independent review of the expiry-aware design;
7. an Accepted ADR expressly authorizing its exact models, migrations,
   authority resolver, active role-map changes, services and tests;
8. one atomic expiry-aware role package introducing canonical assignment state,
   role, permissions, temporal resolution, restoration and tests;
9. conformance review and Architecture Authority acceptance of that package;
10. an express Architecture Authority act closing §8.3; and
11. only afterward, a separate productive operational act and authorized
    transaction assigning the temporary role to the verified Membership.

A package that only adds the eight contract definitions cannot modify
`ROLE_PERMISSIONS`, authority resolution, a Membership or temporary-assignment
state.

The expiry-aware role package cannot assign the role to Guillermo or any other
Principal. It installs governed capability but performs no productive
assignment.

No identity, mailbox, display name, email address, provider claim, request
header or documentation reference may identify or select the productive
Principal for mutation.

## 12. Duration, review and revocation

Any future canonical temporary assignment must:

- last no more than 30 calendar days from its effective time;
- have a mandatory authority review no later than day 14;
- default to non-renewal;
- preserve `netpay_operations_operator` as the exact canonical prior role;
- expose an unambiguous canonical status;
- fail closed when expired, revoked, ambiguous, inconsistent or not reviewed on
  time;
- deny all Intake permissions immediately at expiry, revocation or missed
  review, independently of physical Membership-role restoration;
- preserve the four original Netpay Master and Inbox permissions while
  restoration is pending;
- be revoked immediately on account compromise, Membership revocation,
  Organization suspension, mailbox-control change, authority mismatch,
  cross-tenant evidence, security incident or addition of a second reviewer;
- require optimistic concurrency and idempotency for assignment, review,
  revocation and restoration; and
- require a new explicit Architecture Authority act for any extension,
  replacement or deviation.

The intended effective lifecycle is the transition defined in §10.5.

The expiry-aware assignment source governs whether the three Intake permissions
are effective. The static role map alone cannot grant them during the pilot.

When the day-14 review deadline passes without a canonically recorded valid
review:

1. all three Intake permissions fail closed immediately;
2. the assignment can no longer be treated as active;
3. the four original Master and Inbox permissions remain available;
4. physical restoration may proceed only through the separately authorized
   compare-and-swap procedure; and
5. no audit entry can substitute for the missing canonical review state.

The 30-day maximum does not authorize a real pilot or establish its start date.
The clock begins only if a later operational assignment is separately
authorized and its canonical state commits.

Physical restoration must:

- obtain `prior role` from the canonical temporary-assignment source;
- require it to equal `netpay_operations_operator`;
- verify the current Membership and assignment concurrency state;
- be idempotent;
- fail closed rather than overwrite an unexpected Membership role;
- restore exactly `netpay_operations_operator`; and
- reflect the result in audit evidence.

The audit log supports evidence and investigation. It is not the canonical
source for the prior role, assignment status, review completion, expiry,
permission resolution or restoration target.

Revocation or expiry must not alter Principal, Person, Identity Binding,
Organization, Membership identity or unrelated canonical records.

None of these models, checks, mutations or restoration operations is authorized
by this proposal, by an Accepted ADR ratifying only static definitions, or by a
contract-definition implementation package.

## 13. Registration and runtime boundary

The first future canonical implementation package may add only the eight
contract definitions specified in §4.

That package must:

- add all eight contracts with lifecycle `RATIFIED`;
- give all eight contracts initial operational status `PLANNED`;
- use owner module `netpay_merchant_operations`;
- use owning context `Netpay Merchant Operations`;
- use owning capability `Netpay Gmail intake`;
- preserve `criticality=CORE`;
- add no Handler or Handler factory;
- add no Query implementation;
- add no Event publisher;
- add no route;
- add no model, repository, service, migration or configuration;
- add no runtime composition entry;
- leave `netpay_operations_operator` unchanged;
- leave `netpay_intake_pilot_operator` absent from `ROLE_PERMISSIONS`;
- leave every `netpay.intake.*` permission without runtime authority; and
- leave CMD-017 unregistered, non-dispatchable and `gate_closed`.

The semantic role and permission definitions may be ratified by a future ADR,
but they cannot enter the active runtime map through this first package.

The current resolver grants permissions directly from
`PrincipalMembership.role → ROLE_PERMISSIONS`. Adding the temporary role to
`ROLE_PERMISSIONS` without simultaneous expiry-aware assignment checks would
create authority that does not expire safely.

The static four-permission role entry and the separately represented temporary
Intake permissions may enter runtime only in the separately authorized
expiry-aware role package. That package must introduce the canonical assignment
source, temporal resolution, base-only static role entry, temporary Intake
capabilities and fail-closed behavior atomically.

Even a conformant expiry-aware role package cannot perform an effective
productive assignment. Assignment requires a later, separate operational act.

Canonical contract assignment, contract-definition implementation,
expiry-aware role implementation, §8.3 closure and productive role assignment
are distinct stages. Completion of one does not imply completion of another.

The prohibition in §10.5 remains controlling: effective pilot-role assignment
requires a separate Accepted ADR for both the expiry-aware canonical mechanism
and its productive authority-resolution checks.

For the expiry-aware package, “atomic” means that no unsafe intermediate
combination is externally observable or capable of granting Intake authority.
Database migration and application deployment may use ordered, compatible
phases rather than one PostgreSQL-plus-deployment transaction, but every
intermediate phase must fail closed. The role must remain absent or base-only
until every productive authority path enforces canonical temporal state.

## 14. Explicit non-goals and prohibitions

This proposal does not authorize:

- modifying `canonical_contracts.py`;
- modifying `ROLE_PERMISSIONS`;
- modifying any application contract definition;
- creating a Handler, Handler factory, service, repository, model or route;
- modifying bootstrap or the default runtime composition root;
- registering or dispatching any Gmail Command;
- implementing any Query or Event;
- modifying a Person, Principal, Identity Binding, Membership or Organization;
- creating another Principal for Guillermo;
- changing the one-role-per-Membership model;
- creating a canonical temporary-assignment source;
- assigning `netpay_intake_pilot_operator`;
- adding `netpay_intake_pilot_operator` to the active role map;
- adding `netpay.intake.*` to active runtime authority;
- expanding `netpay_operations_operator`;
- creating a mailbox configuration or binding;
- productive persistence or migrations;
- privacy or retention implementation;
- secrets or credential storage;
- Google project or consent configuration;
- OAuth or token handling;
- Gmail or mailbox access;
- synchronization or cursor movement;
- workers, schedulers, queues, webhooks, Pub/Sub or polling;
- `CommercialIntakeItem` or `NetpayServiceCase` creation;
- CMD-019 or EVT-009 allocation;
- deployment;
- a synthetic or real pilot; or
- any contract, role, permission or capability not expressly listed.

No later gate is opened by implication.

## 15. Proposed Evidence Gates

### 15.1 Contract-definition package

The first future implementation package may claim conformance only if
reproducible evidence proves:

1. exactly the eight authorized contract IDs were added;
2. CMD-019 and EVT-009 remain absent and unreserved;
3. every owner module is `netpay_merchant_operations`;
4. every owning context is `Netpay Merchant Operations`;
5. every owning capability is `Netpay Gmail intake`;
6. every lifecycle is `RATIFIED`;
7. every initial operational status is `PLANNED`;
8. every criticality is `CORE`;
9. all eight definitions have the exact approved names, purposes,
   `architectural_steward=None` and ordered traceability tuple specified in
   §4;
10. duplicate IDs and invalid metadata fail closed;
11. canonical contract and module registries remain valid and sealed;
12. no Handler or Handler factory is registered for any of the eight;
13. no Query implementation exists for QRY-007 or QRY-008;
14. no Event publisher exists for EVT-007, EVT-008 or EVT-010;
15. CMD-017 is rejected as non-operational before any side effect;
16. `netpay_intake_pilot_operator` is absent from the active
    `ROLE_PERMISSIONS` map;
17. `netpay.intake.read`, `netpay.intake.connect` and
    `netpay.intake.review` grant no runtime authority;
18. `netpay_operations_operator` remains byte-for-byte semantically unchanged;
19. no authority resolver changed;
20. no canonical temporary-assignment source was introduced;
21. no Principal, Person, Identity Binding, Membership or Organization changed;
22. no route, service, repository, model, migration, configuration, dependency
    or deployment file changed;
23. no Gmail, Google, OAuth, secret, mailbox or network code was introduced;
24. no productive assignment occurred;
25. focused canonical-contract and registry tests pass;
26. existing authority-map and authority-resolution regressions pass;
27. Pyright passes for the authorized files and tests;
28. Ruff check and Ruff format check pass;
29. `git diff --check` passes;
30. the diff contains only the future ADR's exact Authorized File Boundary; and
31. independent conformance review confirms zero exceptions or records each
    expressly accepted exception;
32. CMD-017's durable result schema admits only `status=completed` with
    `failure_code=null`;
33. every CMD-017 failure path terminates through a contractual error without a
    committed result object;
34. no CMD-017 failure path authorizes a second Unit of Work, nested
    transaction, savepoint, background task, alternate outbox or post-rollback
    persistence;
35. EVT-010 remains `PLANNED`, non-operational and without a runtime producer;
    and
36. QRY-008 reserves `attachment_metadata` as exactly `null` until a later
    Accepted ADR following §8.5 expressly modifies the contract.

This Evidence Gate does not authorize the package. Passing it does not close
§8.3 because the expiry-aware role mechanism remains mandatory.

### 15.2 Expiry-aware role package

A separately authorized expiry-aware role package may claim conformance only
if reproducible evidence proves:

1. the package has its own Accepted ADR and Authorized File Boundary;
2. an expiry-aware canonical assignment source exists;
3. any required model and migration were explicitly authorized;
4. every assignment records the required canonical fields;
5. productive authority resolution consults that canonical source;
6. the role definition, three Intake permissions, canonical assignment source
   and expiry-aware resolver enter runtime atomically in one package;
7. partial deployment cannot leave the role active without temporal checks;
8. `ROLE_PERMISSIONS["netpay_intake_pilot_operator"]` contains exactly the four
   preserved base permissions, while valid temporal resolution produces the
   seven-permission effective union;
9. `netpay_operations_operator` remains byte-for-byte semantically unchanged;
10. the role string alone never grants `netpay.intake.*`;
11. no canonical assignment means all three Intake permissions deny;
12. inactive, future, expired or revoked assignment means all three Intake
    permissions deny;
13. overdue day-14 review means all three Intake permissions deny;
14. ambiguous, inconsistent or stale assignment state means all three Intake
    permissions deny;
15. denial occurs even when physical Membership-role restoration is pending;
16. the four Master and Inbox permissions remain effective during restoration
    reconciliation;
17. `read`, `connect` and `review` are checked independently;
18. assignment and restoration require optimistic concurrency;
19. assignment and restoration are idempotent;
20. restoration uses the canonical prior role, never audit as authority;
21. audit records reflect canonical changes but do not determine authority;
22. failed audit persistence rolls back the associated canonical mutation;
23. unexpected roles fail closed without overwrite;
24. no second Principal or multi-role Membership model is introduced unless
    separately authorized;
25. no effective productive role assignment occurs during implementation or
    tests;
26. no Gmail, Google, OAuth, secret, mailbox or provider access occurs;
27. focused temporal, resolver, concurrency, rollback and restoration tests
    pass;
28. relevant productive-auth and authority regressions pass;
29. a structural inventory identifies every direct and indirect production
    call site of `permissions_for_role`, including authority resolution,
    productive session creation/authentication and Governance role validation;
30. tests prove every inventoried authority-construction call site uses the
    temporal resolver before the role is usable and no residual call site can
    obtain Intake permission from the role string alone;
31. Pyright, Ruff and format checks pass;
32. `git diff --check` passes;
33. the diff stays within the separately authorized boundary; and
34. independent conformance review confirms the complete mechanism entered
    runtime without partial authority.

Passing this Evidence Gate still does not assign
`netpay_intake_pilot_operator` to Guillermo or any other Principal.

## 16. Rollback strategy

Before ratification or implementation, rejection or withdrawal requires no
runtime rollback because this proposal creates no state.

Rollback is package-specific.

The contract-definition package rollback affects only the eight canonical
contract definitions. It must not touch `ROLE_PERMISSIONS`, authority
resolution, temporary-assignment state, Memberships or productive data.

CMD-017 uses only the Unit of Work created and owned by Dispatcher. Any
post-admission failure before commit rolls back that Unit of Work and terminates
with `SYNC_FAILED_CLOSED`. Rollback creates no durable result, receipt or Event,
and no rollback procedure may open or imply a second transaction boundary to
record the failure. A commit failure preserves the primary exception and makes
no subsequent persistence guarantee.

If contract definitions have never been promoted, registered, referenced by
runtime or used in durable records, the bounded package may be reverted. Once
used, their deprecation or retirement requires separate authority.

The expiry-aware role package must be deployed and rolled back without an
externally observable or authority-granting unsafe intermediate combination.
Ordered compatible migration and deployment phases are permitted, but every
phase and rollback point must fail closed. This is not a claim that PostgreSQL
migration and application deployment form one transaction. Rollback must not
leave:

- `netpay_intake_pilot_operator` in the active role map without temporal
  resolution;
- any `netpay.intake.*` permission reachable solely from a role string;
- an authority resolver expecting absent assignment persistence; or
- assignment persistence active without its fail-closed resolver.

If atomic rollback cannot be demonstrated, the package must not be deployed.

No rollback of either implementation package may perform a productive role
assignment.

If a future effective assignment exists, expiry and revocation first remove
effective Intake authority through canonical assignment state and productive
authority resolution. This fail-closed denial must not wait for physical
restoration.

During restoration reconciliation:

- `netpay.intake.read`, `netpay.intake.connect` and `netpay.intake.review` are
  denied;
- `netpay.master.read`, `netpay.master.manage`, `netpay.inbox.read` and
  `netpay.inbox.manage` remain available;
- no audit record can reactivate or extend the assignment; and
- no unexpected Membership role may be overwritten.

The separately authorized physical restoration is:

```text
netpay_intake_pilot_operator
→ netpay_operations_operator
```

That restoration must:

1. load the exact `prior role` from the canonical assignment source;
2. require that prior role to be `netpay_operations_operator`;
3. require canonical assignment status to demand restoration;
4. require the current effective temporary role to be
   `netpay_intake_pilot_operator`;
5. compare the expected Membership and assignment concurrency tokens;
6. fail closed on any mismatch;
7. restore exactly `netpay_operations_operator`;
8. be idempotent;
9. commit canonical assignment state, role restoration, receipt and audit
   evidence atomically;
10. roll back the role mutation if canonical state, receipt or audit evidence
    cannot commit;
11. preserve Principal, Person, Identity Binding, Organization, Membership
    identity and Membership status; and
12. prove the four original permissions remain effective and all three Intake
    permissions deny afterward.

Audit records reflect the attempted and completed restoration but cannot supply
the restoration target. The canonical assignment source supplies the prior role
and lifecycle state.

If physical restoration fails, the canonical assignment remains non-effective
for Intake permission resolution. The system must not reactivate Intake
authority merely because `PrincipalMembership.role` still contains the
temporary role name.

An already completed identical restoration returns the original committed
result and performs no second mutation.

No rollback may delete identity, Membership, Organization, canonical assignment
history, audit or historical authority evidence.

## 17. Risks and mitigations

| Risk | Consequence | Required mitigation |
| --- | --- | --- |
| Composite pilot role is mistaken for dual control | One person could be represented as two independent approvers. | State explicitly that separation is logical only; audit every permission path separately. |
| Role enters active map before temporal resolver | Any Membership carrying a static role entry that included Intake would receive non-expiring Intake authority. | Keep the role absent during the contract package; later add only its four-permission base entry while the canonical assignment source, temporal resolver and separately represented Intake capabilities enter safely as one package. |
| Partial expiry-aware deployment | Runtime could contain a role without expiry checks or a resolver without its canonical state. | Use one separately authorized atomic package, migration/deployment ordering tests and fail-closed conformance checks. |
| Contract package is mistaken for role authority | Semantic ratification could be treated as permission to edit `ROLE_PERMISSIONS`. | Limit the first package to eight `RATIFIED`/`PLANNED` contract definitions and assert role absence. |
| Expiry-aware package is mistaken for assignment authority | Installing the mechanism could mutate Guillermo's Membership. | Prohibit productive assignment in the package and require a later operational act. |
| Static role string grants authority directly | Current `Membership.role → ROLE_PERMISSIONS` behavior would bypass assignment state. | Keep the static entry base-only, migrate every productive authority-construction call site, and require canonical active assignment before the resolver adds Intake. |
| Temporary replacement drops existing authority | Guillermo could lose Netpay Master or Inbox access during the pilot. | Include exactly the four existing operations permissions plus the three new Intake permissions in the temporary role. |
| Temporary role becomes permanent | Additional Intake authority survives the pilot. | Maximum 30 days, day-14 review, default non-renewal and fail-closed expiry. |
| Physical restoration fails | The Membership may still contain the temporary role name after authority expires. | Deny Intake permissions from canonical assignment state immediately while preserving the four base permissions. |
| Day-14 review is missed | Temporary elevated authority could silently continue. | Treat overdue review as immediate fail-closed termination of all Intake permissions. |
| Audit log is treated as authority | Incomplete evidence could select permissions or restoration targets. | Use a separate canonical assignment source; audit only reflects decisions and outcomes. |
| Canonical assignment is ambiguous | More than one record could appear to govern the same Membership. | Require one unique active assignment and fail closed on ambiguity or inconsistency. |
| Unexpected role is overwritten | Concurrent or separately authorized role changes could be lost. | Require exact prior/current roles and optimistic concurrency; fail closed on mismatch. |
| Prior role is unavailable | Restoration could grant the wrong authority. | Persist prior role in canonical assignment state and require it to equal `netpay_operations_operator`; never recover it solely from audit. |
| Base permissions are lost during reconciliation | Netpay Inbox and Master become unavailable after expiry or failed restoration. | Retain exactly the four base permissions while filtering the expired Intake permissions. |
| Existing operations role is silently expanded | Every current operations user could acquire Intake authority. | Keep `netpay_operations_operator` byte-for-byte semantically unchanged and test its exact permission set. |
| Assignment source becomes a permanent multi-role model by implication | A pilot mechanism could silently redefine Membership architecture. | Bound it as temporary; defer definitive multi-role architecture to a separate ADR. |
| Contract assignment is mistaken for runtime authority | Planned Commands could be registered or invoked prematurely. | Initial status `PLANNED`, no runtime registration, structural tests and separate implementation gate. |
| CMD-017 appears executable because it has an ID | Sync or provider access could begin without later gates. | Preserve explicit `gate_closed` semantics and reject before side effects. |
| CMD-017 failure recording opens a second transaction | A rollback could be followed by an unauthorized Unit of Work, savepoint, outbox or background write. | End the Command with `SYNC_FAILED_CLOSED`, claim no durable result, receipt or Event, and require a separate future contract and ADR for any durable post-failure recording. |
| Missing EVT-010 is mistaken for successful sync | Rollback or commit failure may leave no durable failure Event. | Treat only a committed `completed` CMD-017 result as success; event absence is never success evidence. |
| Safe schemas pre-empt privacy review | Proposed fields could be treated as approval to persist real Gmail data. | Treat schemas as semantic maxima; productive sanitization, persistence and retention remain separately gated. |
| Numerical gaps imply reservation | CMD-019/EVT-009 could be treated as implicitly allocated. | State that they are outside, unreserved and unassigned. |
| Candidate review is confused with business acceptance | Review could create Commercial Intake or Cases. | Define `accept_classification` narrowly and prohibit CMD-019, case and business-entity creation. |

## 18. Required authority sequence

The minimum sequence is:

```text
reviewed proposal
→ Accepted ADR
→ contract-definition package
→ conformance
→ separately authorized expiry-aware role package
→ conformance
→ §8.3 closure act
→ separately authorized productive assignment
```

In detail:

1. this proposal completes independent review;
2. an Accepted ADR ratifies the eight contract assignments, semantic temporary
   role, seven effective pilot permissions, 30-day maximum, day-14 review and
   separation between definition, runtime mechanism and productive assignment;
3. a bounded contract-definition package adds only the eight contracts as
   `RATIFIED` and `PLANNED`;
4. independent review and Architecture Authority accept its conformance;
5. a separate proposal and Accepted ADR authorize the expiry-aware canonical
   assignment mechanism and productive authority-resolution changes;
6. the expiry-aware role package atomically introduces canonical assignment
   state, role, permissions, temporal resolution, restoration and tests;
7. independent review and Architecture Authority accept its conformance;
8. Architecture Authority expressly closes §8.3;
9. a later operational act authorizes one productive assignment; and
10. only the separately authorized transaction may create that assignment.

No step opens privacy, secrets, OAuth, Google, Gmail, deployment or pilot gates.

## 19. Conditions for closing Amendment 018 §8.3

Section 8.3 may be declared complete only after:

1. this proposal is independently reviewed with no unresolved blocking
   findings;
2. an Accepted ADR ratifies the final contract and role semantics;
3. the first ADR expressly authorizes the bounded contract-definition package;
4. exactly the eight contract definitions are implemented as `RATIFIED` and
   `PLANNED`;
5. contract-package conformance is independently reviewed and accepted;
6. a separate expiry-aware role design is reviewed and ratified through an
   Accepted ADR;
7. that ADR authorizes the canonical assignment source, any required
   persistence or migration, productive authority-resolution changes, active
   role entry, permissions, restoration and tests as one atomic package;
8. the expiry-aware role package is implemented without boundary violations;
9. its complete Evidence Gate passes;
10. its independent conformance review passes; and
11. Architecture Authority expressly accepts both conformance records and
    closes §8.3.

The contract-definition package alone cannot close §8.3.

The semantic definition of `netpay_intake_pilot_operator` does not permit
adding it to the active role map before the expiry-aware package.

The expiry-aware role package establishes governed runtime capability but must
not create an effective productive assignment.

Guillermo's effective assignment remains subsequent and separate. It requires
its own Architecture Authority act, transactional execution authority and
evidence. Section 8.3 may close before that assignment because closing the gate
establishes canonical contracts and safe role machinery, not the exercise of
productive authority.

Closing §8.3 does not open §8.5 or any later productive gate.

## 20. Downstream gates remain closed

This proposal does not open:

- §8.5 Privacy and Retention;
- §8.6 Secrets;
- §8.7 Productive OAuth Topology;
- §8.8 Google Project and Consent;
- §8.9 Connector Implementation;
- §8.10 Worker and Scheduler;
- §8.11 Real Pilot; or
- §8.12 GO/NO-GO and Deployment.

It also does not declare Amendment 018 §12.2 complete.

No contract assignment, semantic role definition, permission definition,
catalog entry or future ADR may be used as implied authority for those gates.

## 21. Independent-review disposition

| Review finding | Integrated resolution | Result |
| --- | --- | --- |
| Runtime representation of the temporary role | Defines seven effective permissions as a dynamic union; the static role entry contains only the four base permissions, and the temporal resolver alone may add the three Intake permissions after canonical assignment validation. Every productive `permissions_for_role` call site must migrate and be tested. | Resolved in §§10–13 and §15.2. |
| CMD-018 decision ambiguity | Defines four decisions and an exact matrix for corrected category, allowed reason, nullable effective category and review status; invalid combinations fail with `DECISION_PAYLOAD_INVALID`. | Resolved in §6.3 and EVT-008. |
| CMD-017 failure-channel ambiguity | Defines ordered errors, a success-only durable result and full rollback of the sole Dispatcher-owned Unit of Work; failures claim no durable result, receipt or Event and authorize no alternate transaction boundary. | Resolved in §6.2, §15.1 and §16. |
| EVT-010 partial-commit ambiguity | Keeps EVT-010 non-operational and producerless, fixes `checkpoint_advanced=false` and `candidate_count_committed=0` for any later authorized producer, and excludes historical counts. | Resolved in §8.3. |
| Query schema incompleteness | Defines exact fields, types, nullability, closed values, authority rules and protected cursor semantics; `attachment_metadata` is reserved as exactly `null`, and “defined” grants no runtime availability. | Resolved in §7. |
| CMD-016 lifecycle ambiguity | Defines the exact operation matrix, conditional fields, state transitions, reasons, versions, replay and terminal disconnection. | Resolved in §6.1. |
| Contract traceability incompleteness | Sets `architectural_steward=None` and one exact ordered traceability tuple for every contract, consistent with current canonical Netpay defaults while avoiding invented authority. | Resolved in §4. |
| Atomic-deployment interpretation | Defines atomicity as no externally observable or authority-granting unsafe intermediate state; permits ordered compatible phases that fail closed and rejects a fictitious cross-system transaction. | Resolved in §§13, 15.2 and 16. |

These resolutions do not open §8.5 or any later productive gate and create no
canonical assignment, implementation or operational authority while this
document remains Proposed.

## Future Architecture Authority Act

- Decision: **ACCEPTED PROPOSAL — ADR REQUIRED**
- Architecture Authority: **Guillermo de Hoyos, Architecture Authority**
- Decision date: **2026-09-08**
- Reviewed proposal SHA-256: **`3F9A2B533FB7EDA3D840C945831812631A0707C12551D88A614A0B2F3DE38B8B`**
- Hash basis: **Canonical UTF-8 without BOM, with CRLF and lone CR normalized to LF before hashing**
- Independent review verdict: **ACCEPT**
- Accepted scope: **Accepted exclusively as the reviewed basis for preparing a separate ADR for Contract and Role Allocation under Amendment 018 §8.3 and AR-001**
- Authorized status: **ACCEPTED PROPOSAL — ADR REQUIRED — NO CANONICAL ASSIGNMENT OR IMPLEMENTATION AUTHORITY**
- Exceptions: **None**
- Downstream authority: **None**

This acceptance is not an Accepted ADR and does not satisfy or close §8.3. It
does not authorize registering the eight contracts in runtime, creating the
temporary role, creating the Intake permissions or temporal resolver, modifying
`ROLE_PERMISSIONS` or productive call sites, or assigning any role or permission
to Guillermo de Hoyos or any other person.

It does not authorize implementation, migrations, data changes, configuration,
secrets, OAuth, Google resources, Gmail, mailbox access, deployment or a pilot.
It does not open §8.5 or any later gate.
