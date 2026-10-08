# YARVIS
# Implementation Roadmap Amendment 019

## Netpay Gmail Intake — canonical implementation mandate

## Status

**RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2**

This document is the ratified future implementation mandate for Gmail Intake
D1/D2. This execution only closes and registers governance documentation; it
performs no productive code, OAuth, credential, migration, synchronization or
Gmail access. The companion
`IG-007_NETPAY_GMAIL_INTAKE_IMPLEMENTATION_AUTHORIZATION.md` is ratified with
the same boundary.

The mandate remains intentionally separate from implementation. The current
branch has no Gmail implementation changes and remains at the D1 Operational
Data closure base.

**GMAIL INTAKE D3 — NOT AUTHORIZED.** Scheduler runtime, polling, workers,
Pub/Sub, webhooks, Gmail watch, autonomous follow-up and send/mutation remain
outside this authority.

## 1. Baseline, authority and current gate

| Field | Value |
| --- | --- |
| Candidate branch | `feat/netpay-gmail-intake-sentinel` |
| Reviewed base | `f71780d161502fef0709759118b381d583d6afd2` |
| D1 Operational Data | `ACCEPTED EVIDENCE — D1 CONFORMANCE ESTABLISHED — GATE PASSED` |
| D2-Lite Operational Data | Separate decision; unchanged and not authorized here |
| Governing Gmail design | `IMPLEMENTATION_ROADMAP_AMENDMENT_014.md` and `IMPLEMENTATION_ROADMAP_AMENDMENT_018.md` |
| Governing Inbox contracts | `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` and `NETPAY_MVP2_INBOX_CASE_CONTRACT.md` |
| Governing Commercial Intake | `IMPLEMENTATION_ROADMAP_AMENDMENT_015.md` |
| Ratified implementation gate | `IG-007` (this package and its companion) |

IG-007 is ratified as bounded future authority for a synthetic/local D1 package
and a D2 package conditional on the D1 Evidence Gate. Runtime implementation,
productive OAuth, credentials and Gmail access remain unperformed in this
execution and require later operational gates. Amendment 012 still excludes
Gmail synchronization; existing Commercial Intake authority remains the owner
boundary. D1 is the next active work package; D2 is conditional; D3 is not
authorized.

The authority sequence is mandatory:

```text
Amendment 019 and IG-007 ratification (this execution)
  -> canonical contract allocation and registry conformance
  -> canonical Principal/Organization/Membership evidence
  -> privacy, retention and secrets approval
  -> fake/local implementation gate for synthetic D1/D2
  -> productive OAuth topology and Google-project gates
  -> productive Gmail connector gate
  -> separate scheduler/Pub/Sub gates, if ever proposed
```

No step may be inferred from a later step, a branch name, a fixture, a Gmail
address, a token, a role string, a contract number or a passing synthetic test.

## 2. Repository inspection and reuse decision

The following existing boundaries were inspected at the reviewed base:

| Existing boundary | Decision for the future package |
| --- | --- |
| `CommercialIntakeItem` and `/netpay/inbox/contacts` | Reuse for human-confirmed pre-Master commercial intake. Candidate acceptance may call the existing owner command; it must not create a second intake aggregate. |
| Tenant-owned `netpay_inbox_cases` and `NetpayServiceCase` | Reuse for human-confirmed known-client case creation/linking. Gmail code may not write the aggregate directly. |
| `/netpay/inbox` and `NetpayInboxWorkspace` | Reuse as the only operator surface. Add a Gmail section inside this surface; do not create a second Inbox. |
| `Principal`, `PrincipalMembership`, `AuthorityResolutionService` and Inbox permissions | Reuse tenancy and authority resolution. Proposed Gmail permissions require a separate role/catalog act and are not added by this package. |
| `NetpayInboxCommandReceipt`, `CommercialIntakeCommandReceipt`, `DomainEvent` | Reuse their atomic receipt/event patterns. Candidate review/acceptance needs a candidate-scoped receipt shape because neither existing receipt owns a candidate result. |
| `Message` and `IntakeItem` | Do not reuse as the Gmail source aggregate. They lack the required tenant, connector/account, Gmail thread, cursor and retention boundaries. Their existing routes remain untouched. |
| Legacy `/netpay/import-email` and `netpay_service_cases` | Do not call, migrate, link, backfill or treat as the new connector contract. Their tenancy and ownership are incompatible with this package. |
| `Settings.scheduler_*`, worker flags and current bootstrap | No runtime scheduler exists. These flags do not authorize or implement D3; the package leaves them unchanged. |

## 3. Future scope: Gmail Intake D1 — source connector and manual sync

The following is the exact scope that a later ratified implementation gate may
open. It is not open in this execution.

### 3.1 Source binding and OAuth boundary

The connector binds one stable Gmail provider account to one Organization:

```text
Gmail account identity -> NetpayGmailConnection -> Organization
```

The binding is explicit and unique. Sender, recipient, domain, subject, body,
header, Store ID, workspace value, token claim or visible mailbox address may
not select an Organization. A conflicting or ambiguous binding fails closed.

The productive adapter may use only Google's `gmail.readonly` scope. Gmail
OAuth is separate from login OIDC. Access and refresh tokens remain behind the
approved encrypted credential-store boundary; the database stores only an
opaque `credential_secret_ref` and safe status. Tokens, client secrets,
authorization codes and provider responses never reach the frontend, Git,
ordinary logs, events, fixtures or test snapshots.

The local/fake provider is the first implementation target. It must prove the
same port and invariants without a Google client, network access or real
credentials. A productive Google client dependency and OAuth configuration
require the later productive OAuth gates listed in §1.

### 3.2 Manual sync and bounded backfill

Only an explicit manual sync may run in D1. The initial backfill is at most 30
calendar days before the approved first manual run, uses the configured query
and verified Gmail `label_id`, and never reaches the 62 excluded historical
Radar records. The visible label name is configuration only; the canonical
`label_id` is persisted and revalidated for every sync.

If the account, Organization binding, label, credential state or cursor is
missing, invalid, ambiguous, revoked or inconsistent, the operation fails
closed: it does not query Gmail, create source items, advance a cursor or emit
provider payloads. A bounded full rescan may replace an expired history cursor
only under the same label/query and dedupe key.

The D1 sync writes source evidence only. It creates no candidate, Commercial
Intake item, NetpayServiceCase, Master record, task, follow-up or external
action. No Gmail message is sent, modified, archived, deleted or labelled.

### 3.3 Source identity and idempotency

The durable source identity is:

```text
(organization_id, connection_id, provider_account_id, gmail_message_id)
```

`gmail_thread_id` is correlation and conversation grouping; it is not the
dedupe key. A reused message ID with a changed immutable fingerprint is
quarantined as a conflict and does not overwrite the original source item.
Repeated delivery produces one source item and one deduplication fact. Cursor
advancement occurs only after the complete accepted batch commits.

### 3.4 D1 source states and safe content

The proposed source state vocabulary is:

`disconnected`, `connected`, `validating`, `ready`, `running`, `succeeded`,
`partially_failed`, `failed`, `revoked`.

The source item stores only the minimum approved metadata: opaque local source
ID, Organization and connection IDs, provider account/message/thread IDs,
provider timestamp, synchronized timestamp, bounded sender/recipient metadata,
subject, sanitized plain-text excerpt (maximum 4 KiB), source fingerprint,
safe attachment metadata, and provenance. Full MIME bodies, HTML, active links,
attachment bytes, tokens and raw provider payloads are excluded. Retention,
legal hold and purge are not implemented by this mandate; they require the
approved retention gate and fail closed on purge failure.

## 4. Future scope: Gmail Intake D2 — candidate extraction and human acceptance

### 4.1 Candidate aggregate

The future `NetpayIntakeCandidate` is evidence derived from one source item. It
is not a Case, Commercial Intake item, Master record, Person, Principal,
Document or Mission Work item. It is tenant-owned and links to the source by
opaque local IDs while preserving the provider message/thread IDs under the
approved retention boundary.

The minimum candidate data is:

- source item, connection, Organization and provenance references;
- sanitized subject/excerpt and source timestamps;
- `request_type`, `product`, `description`, `expected_outcome` and candidate
  Client/Company/Branch/Store hints;
- `priority` using `urgent`, `high`, `normal`, `low`;
- `received_at`, derived `age_days`, optional `target_at` and derived
  `overdue`;
- nullable suggested responsible Principal (suggestion only, never authority);
- suggested next action and an allowlisted `missing_data` code set;
- deterministic/AI method, version, confidence and reasons per suggestion;
- explicit candidate state, reviewer, review time, safe disposition reason and
  accepted/link target;
- immutable source fingerprint and correlation/causation identifiers.

Age is derived from `received_at` and the evaluation clock. Priority,
responsible Principal and next action remain suggestions until a human command
writes them through the owning Commercial Intake or Inbox contract. The
pending/overdue query is read-only and never mutates state.

### 4.2 Classification boundary

The classifier has two attributable layers:

1. deterministic normalization and rule classification; and
2. an optional versioned AI suggestion behind a provider-neutral interface.

The initial closed request catalog is:

`merchant_onboarding`, `new_store`, `new_branch`, `ecommerce_activation`,
`terminal_replacement`, `bank_account_change`, `legal_entity_change`,
`support_incident`, `follow_up`, `unclassified`.

The synthetic acceptance fixture is derived from the scenario “alta de
e-commerce Stores para nuevas sucursales”. It must exercise a known
`new_branch`/`ecommerce_activation` suggestion, an unknown classification,
missing Client/Company evidence and a multi-message thread. The classifier
must never accept a candidate, infer a tenant, grant authority, create a case,
or send content to an external model. AI output is untrusted, versioned and
explainable; email text is data, never an instruction.

### 4.3 Human disposition and existing owners

Only an authorized human reviewer may accept, reject, mark duplicate or link a
candidate. Acceptance must first validate the candidate and target in the same
Organization, then call the existing owner operation:

- unresolved pre-Master work becomes one `CommercialIntakeItem`; or
- a known same-tenant Master target becomes one `NetpayServiceCase` through the
  existing Inbox contract.

The candidate-to-source-to-decision-to-owner trace is immutable and read back
after reload. An accepted candidate replays the same target. A changed replay
returns a conflict. The candidate service never directly inserts or updates
Master, Commercial Intake or Case rows.

Reply generation is an optional D2 command that stores a non-sent draft
artifact only. It cannot call Gmail send, create a draft in Gmail, modify a
message, apply a label, archive, delete or reply.

### 4.4 Candidate states

The proposed candidate lifecycle is:

`new -> needs_review -> accepted | rejected | duplicate | linked | superseded`.

Terminal states are immutable except for an append-only correction record
authorized by a later contract. `accepted` and `linked` always reference one
same-tenant owner result. `superseded` requires an explicit source/candidate
relationship and never deletes evidence.

## 5. Ratified contract allocation

The current catalog was inspected at the reviewed base. It contains Netpay
commands through `IC-NETPAY-CMD-030`, queries through `IC-NETPAY-QRY-013`, and
events through `IC-NETPAY-EVT-019`. `CMD-019` and `EVT-009` remain absent and
are not reused. Amendment 019 registers the next-free D1/D2 IDs in
`apps/api/src/yarvis_api/canonical_contracts.py` as ratified/planned metadata;
registration does not make an unimplemented ID dispatchable.

### 5.1 Commands

| Requested operation | Canonical ID | Semantic name / operation |
| --- | --- | --- |
| Connect, disconnect, validate source | `IC-NETPAY-CMD-016` (existing planned) | `ConfigureNetpayGmailConnector`, operation `connect`, `disconnect` or `validate` |
| Start manual sync | `IC-NETPAY-CMD-017` (existing planned) | `SynchronizeNetpayGmailConnector` |
| Edit/review classification | `IC-NETPAY-CMD-018` (existing planned) | `ReviewNetpayIntakeCandidate`, operation `edit` |
| Create candidate from source | `IC-NETPAY-CMD-031` (registered ratified/planned) | `CreateNetpayIntakeCandidateFromSource` |
| Accept candidate | `IC-NETPAY-CMD-032` (registered ratified/planned) | `AcceptNetpayIntakeCandidate` |
| Reject candidate | `IC-NETPAY-CMD-033` (registered ratified/planned) | `RejectNetpayIntakeCandidate` |
| Mark candidate duplicate | `IC-NETPAY-CMD-034` (registered ratified/planned) | `MarkNetpayIntakeCandidateDuplicate` |
| Link candidate to existing Intake/Case | `IC-NETPAY-CMD-035` (registered ratified/planned) | `LinkNetpayIntakeCandidate` |
| Generate non-sent reply draft | `IC-NETPAY-CMD-036` (registered ratified/planned) | `GenerateNetpayCandidateReplyDraft` |

`CMD-016` keeps the ratified lifecycle grouping rather than inventing three
colliding connector commands. `CMD-018` remains the classification-edit
command; disposition commands are separate and explicit. Every mutating
command requires Organization, canonical actor, correlation/causation,
`Idempotency-Key`, functional fingerprint, timestamp and an atomic receipt.
Authority is revalidated before receipt lookup or replay.

### 5.2 Queries

| Query | Canonical ID | Boundary |
| --- | --- | --- |
| List candidates | `IC-NETPAY-QRY-007` (existing planned) | Tenant-scoped safe candidate summaries and allowlisted health |
| Get candidate | `IC-NETPAY-QRY-008` (existing planned) | Tenant-scoped safe detail, provenance, suggestions and owner link |
| Get Gmail connection status | `IC-NETPAY-QRY-014` (registered ratified/planned) | State, safe timestamps, controlled error and cursor-present flag |
| Get Gmail sync status | `IC-NETPAY-QRY-015` (registered ratified/planned) | Run counts/status and safe failure categories; no provider payload |
| List Gmail source items | `IC-NETPAY-QRY-016` (registered ratified/planned) | Tenant-scoped source summaries with bounded content |
| Get Gmail source item | `IC-NETPAY-QRY-017` (registered ratified/planned) | One tenant-scoped source item and provenance |
| Preview candidate acceptance | `IC-NETPAY-QRY-018` (registered ratified/planned) | Side-effect-free validation and proposed owner result |
| List overdue candidates | `IC-NETPAY-QRY-019` (registered ratified/planned) | Derived aging/overdue queue, deterministically ordered |

Queries never infer tenancy from request data and never mutate cursors,
candidates, cases or Gmail.

### 5.3 Events

| Event intent | Canonical ID | Boundary |
| --- | --- | --- |
| Gmail source connected | `IC-NETPAY-EVT-020` (registered ratified/planned) | Safe connection ID, Organization, actor and trace |
| Gmail source disconnected | `IC-NETPAY-EVT-021` (registered ratified/planned) | Safe connection ID, reason code and trace |
| Manual sync started | `IC-NETPAY-EVT-022` (registered ratified/planned) | Run ID, connection ID, Organization and trace |
| Manual sync completed | `IC-NETPAY-EVT-023` (registered ratified/planned) | Safe counts and cursor-present result only |
| Source item captured | `IC-NETPAY-EVT-024` (registered ratified/planned) | Opaque source ID and safe trace; no body or addresses |
| Source item deduplicated | `IC-NETPAY-EVT-025` (registered ratified/planned) | Opaque source/reference IDs and safe dedupe reason |
| Candidate reply draft generated | `IC-NETPAY-EVT-026` (registered ratified/planned) | Candidate/draft IDs, actor and trace; never content or send result |
| Manual sync failed | `IC-NETPAY-EVT-010` (existing planned) | Controlled failure category and `cursor_advanced=false` |
| Intake candidate created | `IC-NETPAY-EVT-007` (existing planned) | Candidate/source IDs, Organization and trace |
| Intake candidate accepted | `IC-NETPAY-EVT-008` (existing planned; `decision=accepted`) | Human reviewer, safe reason, owner-result reference and trace |
| Intake candidate rejected | `IC-NETPAY-EVT-008` (existing planned; `decision=rejected`) | Human reviewer, controlled reason and trace |
| Intake candidate marked duplicate | `IC-NETPAY-EVT-008` (existing planned; `decision=duplicate`) | Human reviewer, duplicate reference and trace |
| Intake candidate linked | `IC-NETPAY-EVT-008` (existing planned; `decision=linked`) | Human reviewer, same-tenant owner reference and trace |

The existing `EVT-007`, `EVT-008` and `EVT-010` are preserved; the ratified allocation
does not reassign them. `EVT-008` is the existing review fact with an explicit
decision discriminator, so the requested accepted, rejected, duplicate and
linked outcomes do not create semantically colliding event IDs. The owner-link
result remains in the candidate trace and the existing owner event stream. All
events exclude raw Gmail IDs from health summaries, bodies, headers, tokens,
attachments and provider exceptions.

## 6. Minimal persistence proposal

If the future implementation gate proves that existing tables cannot represent
the boundary, one linear reversible migration is proposed:

No migration revision is reserved by this ratification. The inspected
repository currently has four Alembic heads: `20260712_04`, `20260802_25`,
`20260802_26` and `20260823_47`. A future implementation must run
`alembic heads` against the actual checkout, choose one valid next revision or
an explicit merge revision when multiple heads remain, set exactly one valid
`down_revision`, and prove `upgrade -> downgrade -> upgrade`. Neither
`20261009_48` nor `20260823_47` is ratified as a future parent.

If persistence is necessary, the future migration may create only:

- `netpay_gmail_connections` — explicit Organization/account binding, opaque
  credential reference, label/query policy, state and safe health timestamps;
- `netpay_gmail_sync_runs` — manual run state, bounded counts, cursor metadata,
  lease/version and controlled failure code;
- `netpay_gmail_source_items` — tenant/source identity, message/thread IDs,
  immutable fingerprint, safe content boundary, timestamps and provenance;
- `netpay_intake_candidates` — source link, suggestions, confidence/reasons,
  priority/aging/owner/next-action fields, state and owner-link trace;
- `netpay_intake_reply_drafts` — candidate link, safe draft metadata/body
  policy, author and timestamps; no Gmail draft ID or send state; and
- `netpay_intake_command_receipts` — Organization/contract/key/fingerprint,
  actor, result target, response snapshot and timestamps.

The migration must add tenant and foreign-key constraints, the source dedupe
unique key, candidate indexes for state/priority/overdue ordering, and no
legacy table alterations. If a reviewed design finds a safe existing table
representation, the migration is omitted rather than adding duplicate state.

## 7. Security, privacy and human authority

- Gmail OAuth is separate from OIDC and uses only `gmail.readonly` initially.
- Tokens and client secrets are encrypted outside ordinary domain records;
  only opaque references are persisted.
- Organization and Membership are resolved server-side. Sender, address,
  domain, message content and Store ID never select a tenant or grant rights.
- Proposed `netpay.intake.read`, `netpay.intake.review` and
  `netpay.intake.connect` permissions require a separate authority/catalog
  act. This package does not edit `ROLE_PERMISSIONS`, create a Principal or
  assign a Membership.
- AI is optional and replaceable. No email content is sent to an external AI
  provider without a separate privacy decision.
- Fixtures are synthetic only. Logs, events and metrics redact PII, content,
  provider IDs, tokens, headers and raw exceptions.
- Body/excerpt, header and attachment retention is bounded and requires a
  future retention/expunge gate. Legal hold is not activated here.
- Every sync, classification, review, acceptance, rejection, duplicate,
  link and draft operation records canonical actor/technical identity,
  Organization, timestamp, correlation, causation and safe provenance.

## 8. Matrix of future scope and exclusions

| Capability | D1 source connector/manual sync | D2 candidate/human acceptance | D3 and later |
| --- | --- | --- | --- |
| Fake/local provider | Required first | Required | N/A |
| Productive Gmail OAuth | Separate gate after D1 synthetic evidence | Reuses approved connector | N/A |
| 30-day backfill | Bounded manual only | Read-only source context | No expansion without new decision |
| Deterministic classification | Not persisted as candidate | Required suggestion layer | No autonomous decisions |
| AI suggestion | Not required | Optional, versioned and synthetic first | No external model without privacy gate |
| Commercial Intake / Case | Prohibited | Human acceptance only through existing owners | No autonomous creation |
| Aging/priority/owner/next action | Source timestamps only | Derived/suggested; human confirmation | No task automation |
| Scheduler/polling/worker | Prohibited | Prohibited | Separate D3 proposal/gate |
| Pub/Sub/watch/webhooks | Prohibited | Prohibited | Separate D5 evaluation |
| Gmail send/modify/archive/delete/label | Prohibited | Prohibited | Permanently outside this mandate |

## 9. Mandatory future acceptance evidence

The future implementation package must provide synthetic, reproducible evidence
for all of the following:

1. tenant isolation for connection, source, candidate, Inbox and owner links;
2. connect, validation, disconnect and revoked/expired credential behavior;
3. maximum 30-day backfill and exact label-ID fail-closed behavior;
4. repeated message replay and message/thread deduplication;
5. a thread with multiple messages producing distinct source items and no
   duplicate owner case;
6. partial batch failure preserving the last cursor and safe failure counts;
7. unknown classification, missing Client and existing Company/Branch paths;
8. deterministic classification and versioned fake-AI suggestion parity;
9. derived aging, priority, suggested responsible, next action and overdue
   pending queue ordering;
10. two simultaneous human accept attempts, repeated acceptance and conflicting
    idempotency replay;
11. explicit prohibition of automatic Commercial Intake or Case creation;
12. human acceptance creates or links exactly one same-tenant owner record and
    preserves the complete source/thread/decision trace;
13. reply draft readback with proof that no Gmail send or message mutation was
    attempted;
14. reload/readback of Inbox candidate and owner state;
15. sanitized hostile HTML and attachment metadata handling with no bytes;
16. no token, secret, PII or real mailbox data in logs, events, fixtures or
    snapshots; and
17. migration upgrade/downgrade/re-upgrade, focused backend tests, frontend
    tests/typecheck/build, static checks and browser E2E against fake/local
    provider fixtures.

The mandatory browser fixture is synthetic and derived from “alta de e-commerce
Stores para nuevas sucursales”. It must include at least one message with a
known request, one unknown/missing-data message, and one repeated thread message.

## 10. Exact future allowlist

The following route-level allowlist is the maximum implementation boundary for
the future fake/local D1/D2 package. A file not listed here is not authorized by
implication.

### Existing files permitted to change

- `apps/api/src/yarvis_api/bootstrap.py` — import and register the new route
  only.
- `apps/api/src/yarvis_api/config.py` — typed connector/synthetic settings only;
  no secrets and no scheduler flags.
- `apps/api/src/yarvis_api/models/__init__.py` — register only the new models.
- `apps/api/src/yarvis_api/api/routes/netpay_inbox.py` — only the minimal
  `/netpay/inbox` pending/overdue composition needed to expose the new query.
- `apps/web/src/api/netpay.ts` — Gmail source/candidate query and command
  clients only.
- `apps/web/src/components/netpay/NetpayInboxWorkspace.tsx` — Gmail candidate,
  pending and overdue sections inside the existing Inbox.
- `apps/web/src/components/netpay/NetpayInboxWorkspace.test.tsx` — focused
  component coverage for the added Inbox section.

### New files permitted to be created

- `apps/api/src/yarvis_api/models/netpay_gmail_intake.py`
- `apps/api/src/yarvis_api/schemas/netpay_gmail_intake.py`
- `apps/api/src/yarvis_api/services/netpay_gmail_intake.py`
- `apps/api/src/yarvis_api/services/netpay_gmail_provider.py`
- `apps/api/src/yarvis_api/services/netpay_gmail_classification.py`
- `apps/api/src/yarvis_api/api/routes/netpay_gmail_intake.py`
- `apps/api/migrations/versions/<next_netpay_gmail_intake_revision>.py` (only
  after the actual Alembic graph and schema review confirm new persistence is
  necessary; the revision is not reserved by this mandate)
- `apps/api/tests/test_netpay_gmail_intake.py`
- `apps/api/tests/test_netpay_gmail_provider.py`
- `apps/api/tests/test_netpay_gmail_security.py`
- `apps/api/tests/test_netpay_gmail_migration.py`
- `apps/web/e2e/netpay-gmail-intake.spec.ts`
- `apps/web/e2e/fixtures/netpay-gmail-stores-new-branches.json`

### Conditional productive files

Only after the separate secrets/OAuth/Google gates may the following be
considered, one at a time: `apps/api/requirements.txt` for an official Gmail
client dependency, and a reviewed secret-store adapter file whose exact path
must be approved by the productive OAuth gate. No such file is authorized by
this proposal's fake/local package.

### Current ratification execution allowlist

- `docs/engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_019.md`
- `docs/engineering/IG-007_NETPAY_GMAIL_INTAKE_IMPLEMENTATION_AUTHORIZATION.md`
- `docs/development/CURRENT_STATE.md`
- `docs/development/CURRENT_SPRINT.md`
- `apps/api/src/yarvis_api/canonical_contracts.py`
- `apps/api/tests/test_canonical_contracts.py`

No runtime, model, schema, route, frontend, dependency, configuration or
migration file is authorized in this execution.

## 11. Explicit denylist

The future package must not modify, create, stage or execute any of the
following without a new authority act:

- `AUDIT_REPORT.md` under every circumstance;
- any D2-Lite Operational Data, Store 360, Gmail D3, WhatsApp, Salesforce,
  NUFI, Mission Work, Task, Radar or deployment file;
- `apps/api/src/yarvis_api/api/authentication.py`, OIDC/session files,
  `application/authority.py`, role maps or Membership data for this package;
- legacy `/netpay/import-email`, `models/netpay.py`, legacy
  `netpay_service_cases`, or any historical Radar record;
- worker, scheduler, queue, broker, lease runner, polling loop, Pub/Sub,
  webhook, Gmail `watch`, Cloud Run or deployment configuration;
- Gmail scopes other than `gmail.readonly`, SMTP, IMAP, `gmail.modify`,
  `gmail.send`, archive, delete, label, draft-send or message mutation;
- raw body/HTML, unrestricted headers, attachment bytes, tokens, credentials,
  real addresses, real names, real RFCs, production data or provider payloads;
- a second Inbox, Case, Commercial Intake aggregate, user system or CRM;
- `git add .`, `git add -A`, broad globs, commit, push, merge, rebase or
  force-push while this mandate is only proposed.

## 12. Risks and rollback

| Risk | Required control | Rollback |
| --- | --- | --- |
| Cross-tenant source or owner link | Backend binding and tenant checks on every read/write | Disable connector; preserve safe evidence; no cross-tenant repair by inference |
| Duplicate Gmail delivery | Source unique key plus immutable fingerprint | Keep first item, record safe dedupe fact, retain cursor |
| Thread creates duplicate case | Thread is correlation only; acceptance idempotency and owner command | Replay prior owner result; conflicting payload returns 409 |
| AI or email prompt injection | Treat body as data; deterministic rules and bounded model adapter | Disable AI suggestion; preserve deterministic evidence |
| Token leakage/revocation | Opaque credential reference, encrypted store, fail-closed status | Disconnect/revoke connector and retain only safe status |
| Partial sync failure | Batch transaction and cursor-after-commit invariant | Retry from last valid cursor or bounded rescan |
| PII/content over-retention | 4 KiB excerpt cap, retention gate, redaction and purge evidence | Stop ingestion on `retention_blocked`; require reauthorization |
| Human acceptance race | Candidate-scoped receipt, optimistic version and owner idempotency | Roll back losing transaction; replay winning result |
| Accidental Gmail mutation | Read-only client port with no mutation methods and negative tests | Disable provider adapter; no message-side rollback is needed |

The synthetic package rollback is removal/disablement of the fake connector and
candidate routes while preserving migration reversibility and safe synthetic
evidence. Productive OAuth rollback requires a separate revoke/delete and
credential-store act; this proposal performs none.

## 13. Ratified gate decision

The ratified decision is:

> **RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2.**
>
> This authority opens only the bounded future synthetic/local D1 package and
> D2 after the D1 Evidence Gate. It does not authorize D3.

The next permitted work is a bounded fake/local D1 implementation under
`IG-007`, followed by D2 only after the D1 Evidence Gate. Productive OAuth,
real Gmail access, credential storage, a real mailbox pilot, scheduler/polling
and Pub/Sub remain separate gates. D3 is explicitly not authorized.

## 14. Required ratification record

| Field | Value |
| --- | --- |
| Decision | `RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2` |
| Architecture Authority | User-directed conceptual ratification; canonical person identity `UNKNOWN` |
| Decision date | `2026-10-08` |
| Accepted SHA-256 | Documentation/catalog commit recorded at publication |
| Implementation gate | `IG-007 — RATIFIED; D3 NOT AUTHORIZED` |
| Effective commit | This documentation/catalog commit |
