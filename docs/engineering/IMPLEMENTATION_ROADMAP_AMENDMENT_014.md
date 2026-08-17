# YARVIS
# Implementation Roadmap Amendment 014

## Status

**RATIFIED — DESIGN AUTHORITY ONLY — NO IMPLEMENTATION AUTHORIZATION.**

This ratification is effective only as design authority for MVP-2D1 Manual
Review Variant. It is not an implementation authorization and creates no
runtime authority, external access, persisted state, or canonical-contract
allocation.

## 1. Purpose, sources, and accepted evidence base

This independent amendment proposes ratification of the design named
**MVP-2D1 Manual Review Variant**. Its normative source is
`NETPAY_MVP2D1_GMAIL_INTAKE_RATIFICATION_DRAFT.md`.

The review evidence is:

- `NETPAY_MVP2D1_GMAIL_INTAKE_RATIFICATION_DRAFT_REVIEW.md`;
- `NETPAY_MVP2D1_GMAIL_INTAKE_RATIFICATION_DRAFT_SECOND_REVIEW.md`; and
- `NETPAY_MVP2D1_GMAIL_INTAKE_RATIFICATION_DRAFT_THIRD_REVIEW.md`.

The third review decision is **Ratifiable**, with zero open BLOCKER, MAJOR,
MINOR, EDITORIAL, or OBSERVATION findings. That review does not itself ratify
this amendment or authorize implementation.

The accepted design evidence base is:

| Element | Exact value |
| --- | --- |
| Branch | `feat/netpay-operational-radar` |
| Accepted base | `50cbb26e1828a711382cb35818b722eb69a04ce2` |
| Design HEAD antecedent | `5406b2485957e078bb7dd426986e5098b8529461` |

The previously cited SHA containing `...358b...` is not a valid object and is
not an authority for this amendment.

## 2. Ratified design scope

This amendment ratifies only the design, invariants, decision limits, and
future-gate prerequisites of
**MVP-2D1 Manual Review Variant**.

It will substitute only the D1 definition of `NETPAY_MVP2D_GMAIL_INTAKE_DESIGN.md`
for Gmail Intake of `Distribución Netpay`, within the explicit mailbox binding
defined below. It will not modify other tenants, mailboxes, connectors,
providers, D2–D5, Radar, F-011, or existing canonical contracts.

Gmail remains external evidence. It is not canonical identity, authority, or
truth. The variant is human-review-oriented and preserves no authority for
automatic case, Master, Radar, Document Registry, Mission Work, or Operational
Task mutation.

`IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` is ratified for Netpay Inbox
contracts and authority, and expressly excludes Gmail and synchronization.
This proposal neither changes that amendment nor uses it as implementation
authority.

## 3. Ratified operational design decisions

### 3.1 Explicit mailbox-to-tenant binding

The sole dedicated mailbox in the ratified design is
`guillermo.dehoyos@netpay.com.mx`. A
future implementation may bind its stable provider mailbox identity explicitly
and only to `Distribución Netpay`
(`59650e6f-ad62-40c3-8cb0-7710a122ce8b`). One mailbox may have no more than one
active Organization binding.

No sender, recipient, domain, message content, header, token claim, Store ID,
workspace value, or other provider metadata may infer or select an
Organization. A missing, conflicting, or ambiguous binding fails closed.

### 3.2 Label selection and fail-closed behavior

`Yarvis/Netpay-Intake` is the exact human-configured label name. A future
implementation must resolve its canonical Gmail `label_id`, persist the mailbox
binding plus `label_id`, and verify that `label_id` on every future
synchronization.

An absent, invalid, ambiguous, deleted, or inconsistent `label_id` blocks the
operation fail closed: no fallback by visible name, no query outside the
binding, no candidate creation, and no cursor advance. Only minimum non-sensitive
health evidence may be recorded.

### 3.3 Backfill, content limit, and review boundary

The initial backfill is at most 30 calendar days before a future first manual
request and uses the verified binding and `label_id`. Expanding that interval
requires a new audited administrative decision. It does not reach the 62
excluded historical Radar records.

A sanitized plain-text excerpt is at most 4 KiB. Review and disposition are
human acts only; an extractor, rule, or future model cannot accept a candidate,
create a case, or mutate a Netpay owner record.

### 3.4 Retention, legal hold, and failure containment

The ordinary maximum local retention for body, excerpt, and non-essential
metadata is 90 days. At expiry, the target preservation boundary is only a
tombstone, hash, timestamps, and auditable purge record.

A future legal hold may suspend purge only under explicit canonical authority
and must record `scope`, `reason`, `authorized_by`, `started_at`, `review_at`,
and `expires_at`. This amendment creates and activates no hold. On hold expiry,
the ordinary retention policy applies immediately.

If a mandatory purge fails, future configuration state becomes
`retention_blocked`. It fails closed: no new synchronization or ingestion, no
cursor advance, no candidate creation, and no silent retention extension. A
future recovery requires remediation, auditable evidence, and human
reauthorization. No hold, purge, recovery, or deletion mechanism is implemented
or authorized by this amendment; a later implementation gate must prove
effective, auditable, and idempotent deletion and these failure branches.

### 3.5 Ratified role design and conditional bootstrap

The following are design proposals only:

| Proposed role | Proposed permissions |
| --- | --- |
| `netpay_intake_viewer` | `netpay.intake.read` |
| `netpay_intake_reviewer` | `netpay.intake.read`, `netpay.intake.review` |
| `netpay_intake_connector_admin` | `netpay.intake.read`, `netpay.intake.connect` |

This amendment creates no Principal, PrincipalMembership, role, permission,
or assignment. No UUID, `external_subject`, membership, or role is inferred or
invented.

Any future bootstrap exception is conditional on an unequivocal canonical
Principal, active Membership in Distribución Netpay, and approval by the
competent canonical authority. If later approved, it lasts at most 30 days from
authorization of the first real pilot, is reviewed on day 14, and is revoked on
expiry, account compromise, mailbox-control change, or addition of a second
reviewer. This paragraph is not an assignment or an executable bootstrap.

### 3.6 Health-data boundary

Any future health response or record is restricted to this closed allowlist:
`mailbox_configuration_id`, `organization_id`, `status` enum,
`last_attempt_at`, `last_success_at`, aggregate `candidate_count`, controlled
`error_code`, and boolean `cursor_present`.

`error_code` must come from a controlled catalog. Senders, recipients, email
addresses, subjects, bodies, snippets, message IDs, header values, attachment
names, tokens, label names, Gmail-originated free text, provider exceptions,
and raw provider responses are prohibited.

## 4. Future contract design proposals; no canonical allocation

The following identities are design proposals only. They are neither added to
the canonical Interaction Contract Catalog nor allocated, registered,
dispatchable, or effective under this amendment.

| Proposed ID | Semantic name | Proposed future boundary |
| --- | --- | --- |
| `IC-NETPAY-CMD-016` | `ConfigureNetpayGmailConnector` | Future human configuration, pause, or disconnection of one explicit binding; no OAuth or secret persistence under this amendment. |
| `IC-NETPAY-CMD-017` | `SynchronizeNetpayGmailConnector` | Future manual synchronization request proposal. Until canonical allocation and an independent gate, it is unregistered and non-dispatchable; every invocation is `gate_closed`, with no Gmail access, candidates, cursor movement, or external/persistent effects. |
| `IC-NETPAY-CMD-018` | `ReviewNetpayIntakeCandidate` | Future human correction or non-mutating disposition of a candidate. |
| `IC-NETPAY-QRY-007` | `ListNetpayIntakeCandidates` | Future tenant-scoped candidate list and allowlisted health only. |
| `IC-NETPAY-QRY-008` | `RetrieveNetpayIntakeCandidate` | Future tenant-scoped safe candidate detail. |
| `IC-NETPAY-EVT-007` | `NetpayIntakeCandidateReceived` | Future safe fact with IDs, Organization, status, and trace only. |
| `IC-NETPAY-EVT-008` | `NetpayIntakeCandidateReviewed` | Future safe disposition, actor, reason code, and trace. |
| `IC-NETPAY-EVT-010` | `NetpayGmailConnectorSyncFailed` | Future connector ID and controlled failure category only. |

`IC-NETPAY-CMD-019` and `IC-NETPAY-EVT-009` are completely outside MVP-2D1
Manual Review Variant. They are not proposed, allocated, reserved, or ratified
here and are deferred in their entirety to MVP-2D2.

## 5. Explicit non-effects and exclusions

This amendment does not:

- modify the canonical catalog or allocate contracts;
- create a Principal, Membership, role, permission, or role assignment;
- reconcile `CURRENT_STATE`, `CURRENT_SPRINT`, roadmap, IG-006, F-011 Stage I,
  Radar, or `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`;
- authorize implementation, code, tests, models, routes, migrations, schema,
  configuration, synchronization, ingestion, or expunge;
- create a Google project, OAuth client, resource, secret, token, credential,
  credential store, or mailbox binding;
- authorize OAuth, consent, credential use, Google access, Gmail access,
  mailbox reading, message querying, or real synchronization; or
- modify `authentication.py`, legacy data, historical Radar records, or any
  existing contract.

No provision above grants authority by implication. Headers, claims, email
metadata, configuration names, design references, or a proposed ID cannot
grant a permission, select an Organization, or authorize an external action.

## 6. Rollback and revocation boundaries

Before any future implementation exists, withdrawal of this ratification has no
runtime rollback because it creates no runtime state. This design is ratified,
but all operations remain closed unless a later gate is issued.

For any later authorized implementation, the mandatory design rollback is to
disable the explicit connector and all manual triggers, reject CMD-017 as
`gate_closed`, stop candidate creation and cursor advance, and preserve only
the approved audit boundary. Account compromise, binding conflict, invalid
`label_id`, `retention_blocked`, authority revocation, or loss of active
Membership requires fail-closed suspension. Credential revocation/deletion and
any provider-side action remain subject to the separate security, OAuth, and
implementation gates.

## 7. Mandatory sequence after ratification

Human ratification is completed as step (a). The remaining sequence is
mandatory and no step implies completion of a later one:

1. **Human ratification (completed):** Architecture Authority ratifies Amendment 014.
2. **Documentary reconciliation:** reconcile `CURRENT_STATE`,
   `CURRENT_SPRINT`, roadmap, IG-006, F-011 Stage I, Radar, and
   `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`; determine the prevailing status
   without retroactively changing authority.
3. **Canonical identity proof:** resolve a canonical Principal and active
   Membership for the intended Organization; no identifier may be invented.
4. **Separate canonical-contract authority:** allocate any approved IDs through
   the canonical catalog procedure.
5. **Independent implementation gate:** explicitly authorize only the approved
   design slice, branch/base, environment, migrations if any, validation, and
   rollback evidence.
6. **Security/privacy prerequisites:** approve enterprise project ownership,
   credential-store boundary, credential lifecycle, and compatible loopback
   flow; these remain unimplemented until separately authorized.
7. **Separate OAuth and real-pilot gate:** expressly authorize any OAuth
   consent, Google resource, credential, mailbox connection, or real pilot.

## 8. Ratification record

| Field | Value |
| --- | --- |
| Decision | Ratified — MVP-2D1 Manual Review Variant design authority only; all exclusions and future preconditions preserved. |
| Ratified by | Human Architecture Authority (user-confirmed) |
| Ratified at | 2026-08-17 America/Mexico_City |
| Effective commit | TO BE RECORDED — no commit created by this ratification action. |
