# Netpay MVP-2D0 — Gmail Intake Technical and Contract Design

## Status and decision boundary

**DESIGN PROPOSAL — REQUIRES INDEPENDENT CONTRACT AND AUTHORITY RATIFICATION BEFORE IMPLEMENTATION**

This document designs Gmail as a replaceable, read-only intake adapter for the
Netpay operational Inbox. Gmail supplies evidence from which Yarvis creates a
human-review candidate. It never creates, updates, transitions, or closes a
`NetpayServiceCase` automatically, and it never mutates the Netpay Master.

The accepted baseline is branch `feat/netpay-operational-radar` at
`50cbb26e1828a711382cb35818b722eb69a04ce2`, with Alembic
`20260814_39`. The target Organization is `Distribución Netpay`
(`59650e6f-ad62-40c3-8cb0-7710a122ce8b`). The historical
`manual-close-validation` (11) and `netpay-demo` (51) sets remain immutable,
unlinked, and outside this design.

## Repository findings and reusable boundaries

| Area | Factual state | Decision for MVP-2D |
| --- | --- | --- |
| Gmail/OAuth | No Gmail client, OAuth flow, credential store, mailbox configuration, history cursor, or Pub/Sub integration exists. | Build a new provider adapter and connector configuration; do not generalize the legacy importer. |
| Runtime scheduling | Settings expose disabled worker/scheduler flags, but application bootstrap and Docker Compose create no worker, scheduler, queue, broker, lease runner, or outbox dispatcher. | D1 is manual. D3 needs a separately implemented durable scheduler/lease boundary; flags alone are not a runtime. |
| Deterministic Intake | `IntakeItem`, `Message`, tenant-scoped idempotency, provenance, trace metadata, and deterministic persistence exist. The current adapter is fixture-oriented and duplicates content in metadata. | Reuse its ownership, idempotency, provenance, correlation, and fail-closed patterns, not its fixture or raw-content shape. |
| Netpay Inbox | The canonical `netpay_inbox_cases` aggregate, CMD-009..015, QRY-005..006, receipts, events, authority, and MVP-2C operator UI exist. | A candidate is a separate aggregate. Acceptance composes the existing CMD-009 only after explicit human confirmation. |
| Legacy Netpay email import | `/netpay/import-email` and legacy `netpay_service_cases` accept normalized email and Gmail IDs but have nullable/global tenancy and incompatible ownership. | Retain and isolate. Do not call, migrate, link, backfill, or treat it as the connector contract. |
| Attachments/Documents | Legacy email payloads accept attachment metadata. Document Registry owns governed metadata/versioning, but its allowed association subjects do not include a Netpay service case or intake candidate. | Store candidate attachment metadata only. Bytes, download, malware scanning, and Document Registry association require later contracts. |
| Secrets and diagnostics | Typed settings use `SecretStr`; observability redacts common token/secret keys. No durable secret manager abstraction exists. | Add a credential-reference boundary before OAuth implementation. Redaction is defense in depth, not token storage. |
| Web | MVP-2C operates Master and Inbox. No Gmail screen or OAuth client exists. | Add `Netpay Inbox → Entradas Gmail` only in D2; OAuth tokens never reach the browser. |

The repository's proposed DI-001 architecture supports provider-neutral
preservation and Gmail-first incremental intake, but it is not implementation
authority. Its `preserve first, interpret second, act third` rule is adopted
here because it conforms to the Constitution and the accepted Netpay ownership
boundary.

## Recommended synchronization strategy

| Strategy | Reliability and complexity | Cost and rollback | Decision |
| --- | --- | --- | --- |
| Manual on demand | Smallest operational surface; operator sees each run; no background availability requirement. It can still exercise pagination, cursor, dedupe, and retry. | No always-on infrastructure. Disable the connector or revoke OAuth to stop it. | **D1 starting mode.** |
| Incremental polling every three hours | Uses persisted `historyId`, is easy to observe, and tolerates a local deployment. It needs a single-run lease, retry/backoff, and durable scheduling that do not exist yet. | Predictable low call volume. Disable schedule while preserving cursor and candidates. | **D3 default, configurable; three hours recommended.** |
| Gmail `watch` + Cloud Pub/Sub | Lower latency, but requires a Google Cloud topic/subscription, delivery acknowledgement, public or pull consumer infrastructure, periodic fallback sync, and watch renewal. Notifications can be delayed or dropped. | Additional cloud operations and failure modes; rollback stops the watch/subscription and returns to polling. | **D5 evaluation after deployed infrastructure exists.** |

Manual and scheduled runs use the same incremental sync service. A run acquires
one connector lease, lists changes after the persisted cursor, fetches selected
messages, upserts candidates idempotently, and advances the cursor only after
the batch is durably accepted. Repeated polling therefore creates neither a
duplicate candidate nor a duplicate case.

Google documents that `history.list` performs partial synchronization from a
recent `startHistoryId`; an expired or invalid cursor returns HTTP 404 and
requires a full synchronization. Recovery must therefore run a bounded full
scan using the configured query, label, and backfill date, upserting against
the same uniqueness key before replacing the cursor. A thread ID is correlation
only and never the dedupe identity.

Gmail `watch` uses Cloud Pub/Sub and expires unless renewed at least every seven
days; Google recommends daily renewal. Even after D5, a periodic reconciliation
poll remains required because notifications can be delayed or dropped.

## OAuth, scopes, and credential lifecycle

- Use Google's official OAuth 2.0 authorization-code flow for a server-side
  application and official Google client libraries.
- Request only `https://www.googleapis.com/auth/gmail.readonly`. Do not request
  `gmail.modify`, `gmail.send`, `mail.google.com`, SMTP, IMAP, or an application
  password. If a later requirement needs modification or sending, it requires a
  new privacy and contract review.
- Request offline access only when a configured mailbox must synchronize while
  its administrator is absent. Keep access and refresh tokens server-side.
- Store the OAuth client secret in environment/deployment secret management and
  each refresh token encrypted at rest behind a credential-store interface.
  Persist only an opaque `credential_secret_ref` with connector state. Never
  place credentials or tokens in Git, relational JSON payloads, logs, events,
  traces, error details, test snapshots, or the frontend.
- Record granted scopes, consent time, safe mailbox identity, token status, and
  last successful refresh without storing access tokens in ordinary domain
  records. Treat scope reduction, `invalid_grant`, expiration, or revocation as
  `reauthorization_required`; stop sync fail-closed and preserve prior evidence.
- Disconnect revokes the Google grant when possible, deletes the stored token,
  disables the connector, and retains only audit-safe configuration and sync
  history. Rotation is a new consent/exchange followed by atomic credential
  reference replacement; it does not rewrite candidates.

The user must configure a Google Cloud project, enable Gmail API, configure the
OAuth consent screen, create a Web application OAuth client, register exact
local/deployed redirect URIs, and supply the client ID/secret through secret
management. Production use of `gmail.readonly` may require Google's restricted
scope verification and related data-handling review.

## Mailbox-to-tenant binding

Introduce a tenant-owned `NetpayGmailConnector` configuration:

- `id`, non-null `organization_id`, provider (`gmail`), stable Google mailbox
  identity, display address, opaque credential reference, granted scopes;
- configurable Gmail query and label IDs, bounded initial backfill date;
- `active`, `reauthorization_required`, `paused`, or `failed` status;
- last accepted `history_id`, last attempted/successful sync, failure category,
  lease/version, audit Principal IDs, and timestamps.

The binding is explicit:

`Gmail mailbox → NetpayGmailConnector → Organization Distribución Netpay`.

No recipient, sender, domain, message content, token claim, header, Store ID, or
legacy workspace value may infer or select the Organization. A stable mailbox
identity can have at most one active Organization binding. A mailbox already
bound elsewhere conflicts without mutation. An absent configuration makes sync
unavailable; revoked OAuth pauses it and asks an authorized connector
administrator to reconnect. Multiple future mailboxes use separate connector
rows and cursors, and their IDs participate in dedupe.

## `NetpayIntakeCandidate`

`NetpayIntakeCandidate` is tenant-owned intake evidence, not a
`NetpayServiceCase`, Master record, Mission Inbox item, Document, or legacy
Netpay email case.

| Field group | Minimum persisted fields |
| --- | --- |
| Identity/tenancy | `id`, `organization_id`, `connector_id`, provider, stable mailbox ID, Gmail message ID, Gmail thread ID |
| Parties/time | sender, relevant `to`/`cc` recipients, provider message date, received/synchronized timestamps |
| Safe content | subject, sanitized plain-text excerpt/body according to the approved retention policy, safe server-resolved source link when allowed |
| Attachments | provider part ID, filename, declared MIME type, reported size, inline flag; no bytes or storage reference in this cut |
| Suggested interpretation | request type, description, expected outcome, product, candidate Client/Company/Branch/Store IDs or text hints, mentioned documents, suggested next action, per-field confidence and reasons |
| Review | `new`, `needs_review`, `accepted`, `dismissed`, `duplicate`, or `failed`; reviewer Principal, reviewed time, safe disposition reason, optional accepted case ID |
| Provenance/audit | provider/config/sync-run references, extraction version/method, source fingerprint, created/updated actor class and timestamps, correlation/causation |

Database uniqueness is `(organization_id, connector_id, gmail_message_id)`.
The connector also validates that a reused provider identity has no conflicting
immutable fingerprint; a conflict becomes `failed`/quarantined for review.
`gmail_thread_id` groups messages but is not unique.

New messages in a thread associated with a case become new candidates linked by
thread/case context. They may propose an append-only activity, but cannot mutate
the case. Accepting such a candidate must either explicitly create one case or,
under a separately ratified future contract, link evidence/activity to the
existing case. It must never create a second case merely because a thread has a
new message.

## Selection and bounded backfill

Do not scan the entire mailbox by default. Each connector requires an explicit
label and/or Gmail query. The recommended initial rule is a configurable Netpay
label plus a bounded query that excludes spam and the Promotions and Social
categories. Known Foodbot or merchant senders may increase confidence or be an
optional allowlist, but they must not be hard-coded and do not establish tenant,
identity, or truth.

Initial backfill is bounded by a user-approved start date and the same
label/query. Runs expose counts for matched, accepted, duplicate, failed, and
skipped messages. Expanding the window is an explicit administrative action;
it never reaches the 62 excluded Radar records.

## Extraction and human review

Keep four attributable layers separate:

1. provider metadata and the permitted source content;
2. deterministic normalization/extraction;
3. replaceable classification suggestions, including any future LLM output;
4. human-confirmed Master links and case input.

Initial deterministic extraction may suggest request type, description,
expected outcome, product, Client, Company, Branch, Store ID, mentioned
documents, and next action. Every suggestion records method, version,
confidence, and reasons. Unknown values remain unknown. An LLM is optional,
versioned, evaluated against a fixed dataset, and never a source of truth.
Email text is untrusted data, never a system instruction; future model prompts
must delimit it and ignore embedded instructions or requests to expose secrets.

The D2 workflow is:

`Gmail message → candidate → Yarvis review → edit/link Master → confirm → IC-NETPAY-CMD-009 CreateNetpayServiceCase → candidate/case link`.

Acceptance requires `netpay.intake.review` plus the authority required by
CMD-009, a caller idempotency key, authority revalidation before replay, a
transactional accepted-state/case link, and preservation of provenance. A
candidate already accepted replays the same case; a changed acceptance payload
conflicts. Dismissal preserves minimum evidence and a safe reason. Review shows
only content permitted by retention policy and never renders active HTML.

## Attachments

MVP-2D4 stores metadata only; D1-D3 may discover the same metadata without
downloading bytes. No binary belongs in relational JSON, events, logs, or model
prompts. A later Document Registry integration needs a ratified
`netpay_intake_candidate`/`netpay_service_case` association, controlled
download/storage, filename and MIME verification, configured size/type limits,
checksum, antivirus/quarantine, retention, and tenant-safe access. Until then,
the UI reports attachment presence and unsupported/oversized metadata without
fetching content.

## Operator screen

Add `Netpay Inbox → Entradas Gmail` in D2 with tabs for new, needs review,
accepted, dismissed, and failed candidates; filters for sender, date, suggested
Client, and confidence; a safe plain-text preview; editable suggestions; Master
lookup/linking; `Crear caso`; and a link to the accepted case. HTML is sanitized
and rendered inert or converted to text; remote images, scripts, forms, links
with unsafe schemes, and active content are disabled. OAuth administration is a
separate surface and never exposes credentials.

## Authority and technical identity

The following matrix is proposed and is **not ratified**:

| Role | Proposed permissions | Exact human scope |
| --- | --- | --- |
| `netpay_intake_viewer` | `netpay.intake.read` | List and retrieve tenant candidates and connector health; no review or configuration. |
| `netpay_intake_reviewer` | `netpay.intake.read`, `netpay.intake.review` | Edit suggestions, dismiss, and accept candidates; acceptance also requires existing Inbox/Master permissions for the selected operation. |
| `netpay_intake_connector_admin` | `netpay.intake.read`, `netpay.intake.connect` | Create/authorize/pause/reconnect/disconnect mailbox configuration and trigger manual sync; no candidate disposition or case mutation. |

Do not expand `netpay_operations_operator` automatically. A future composed job
role needs an explicit ratification. Principal, active Organization,
PrincipalMembership, persisted role, and `AuthorityResolutionService` remain
the sole source of human authority; headers/tokens cannot grant permissions or
select tenancy.

The connector executor is a non-human technical identity bound to one active
connector and Organization. Its authority derives from the persisted connector
configuration and credential reference, not a human Principal, request header,
or Gmail token claim. It can read the configured mailbox and upsert connector
sync state/candidates only. It cannot review, accept, invoke CMD-009, mutate the
Master, or act across Organizations. This technical authority and its
revocation/lease model require independent ratification before D1.

## Proposed contracts

Repository inspection found the following next Netpay IDs unused. Allocation is
proposed only and requires an Amendment plus canonical-catalog update in the
later implementation mandate.

| Proposed ID | Semantic name | Scope |
| --- | --- | --- |
| `IC-NETPAY-CMD-016` | `ConfigureNetpayGmailConnector` | Human connector admin creates/authorizes, pauses, reconnects, or disconnects one explicit mailbox binding; secrets remain behind the credential store. |
| `IC-NETPAY-CMD-017` | `SynchronizeNetpayGmailConnector` | Authorized manual trigger; internal scheduled execution uses the same owner service without human impersonation. It persists sync state and candidates only. |
| `IC-NETPAY-CMD-018` | `ReviewNetpayIntakeCandidate` | Edit suggestions or mark a candidate needs-review/dismissed/duplicate/failed without case mutation. |
| `IC-NETPAY-CMD-019` | `AcceptNetpayIntakeCandidate` | Atomically marks acceptance and invokes CMD-009 under separately validated Inbox/Master authority; no double acceptance. |
| `IC-NETPAY-QRY-007` | `ListNetpayIntakeCandidates` | Tenant-scoped filtered list and safe connector health. |
| `IC-NETPAY-QRY-008` | `RetrieveNetpayIntakeCandidate` | Tenant-scoped safe detail, provenance, suggestions, attachment metadata, and accepted-case link. |
| `IC-NETPAY-EVT-007` | `NetpayIntakeCandidateReceived` | Safe IDs, connector, Organization, status, and trace only; no body, addresses, token, or attachment content. |
| `IC-NETPAY-EVT-008` | `NetpayIntakeCandidateReviewed` | Safe disposition, reviewer, reasons code, and trace. |
| `IC-NETPAY-EVT-009` | `NetpayIntakeCandidateAccepted` | Candidate/case IDs, canonical actor, Organization, correlation, and causation. |
| `IC-NETPAY-EVT-010` | `NetpayGmailConnectorSyncFailed` | Connector ID and safe failure category; never provider payload or credential detail. |

All human commands revalidate authority before receipt lookup/replay, are
tenant-scoped and idempotent, conceal foreign targets, and persist aggregate,
receipt, event, and result atomically. Connector delivery dedupe is independent
of human command receipts.

## Security, privacy, and operations

- Apply least privilege, TLS, encrypted token storage, key rotation, explicit
  disconnect/revocation, audit trails, tenant filters, and fail-closed errors.
- Default to a sanitized necessary excerpt, not a full body, until the user
  approves retention. Redact addresses/content from operational logs; metrics
  use counts and safe categories only.
- Store provider content for the shortest approved period. Candidate dismissal
  retains only the approved audit minimum; deletion/retention jobs require a
  later policy and implementation mandate.
- Treat HTML and MIME as hostile: enforce parse depth/part/count/size limits,
  reject dangerous encodings, strip active content, and prevent external image
  loading. Do not follow links automatically.
- Rate-limit per mailbox, use exponential backoff with jitter and Gmail retry
  guidance, cap attempts, surface actionable OAuth/quota failures, and retain
  the last valid cursor until a batch commits.
- Keep provider payload, message bodies, personal addresses, filenames, and
  model inputs out of ordinary events. Never send email content to an external
  AI provider without a separate privacy decision.

## Build versus buy

| Option | Fit | Risks | Position |
| --- | --- | --- | --- |
| Direct Gmail API | Exact read-only scope, native message/thread/history IDs, labels/query, and direct control of tenant/dedupe/provenance. One mailbox keeps the adapter small. | Yarvis owns OAuth, MIME, quotas, cursor recovery, and operations. | **Recommended for D1-D4.** |
| Managed integration provider | Can reduce OAuth/connectivity work and add providers later. | Additional processor, cost, lock-in, data residency, token custody, webhook semantics, and mapping compromises. | Re-evaluate with pricing, security, residency, export, and SLA evidence; select none now. |
| Automation tool | Fast prototype for triggers. | Often weak fit for durable cursor/dedupe, atomic acceptance, tenant concealment, provenance, and secret boundaries. | Do not place in the canonical path; a future tool may call a governed intake API only. |

This follows the vision's `Build → Use → Learn → Improve` rule: integrate the
official provider capability, and build only the tenant binding, candidate,
review, provenance, and case-acceptance layer specific to Netpay operations.

## Delivery slices, acceptance, and rollback

| Slice | Scope | Acceptance evidence | Rollback |
| --- | --- | --- | --- |
| MVP-2D1 | OAuth/configuration, encrypted credential-reference boundary, explicit mailbox/Organization binding, safe connection status, bounded manual sync service and cursor/delivery persistence. No review UI or case creation. | Official `gmail.readonly`; no secret leakage; wrong/ambiguous tenant rejected; repeated sync idempotent; revoked OAuth fail-closed; invalid cursor bounded-resync test; local disconnect. | Disable connector, revoke/delete token, retain audit/cursor state; no case/Master rollback exists because none is mutated. |
| MVP-2D2 | Candidate aggregate, deterministic extraction, list/detail/review UI, dismiss and human acceptance through CMD-009. | Cross-tenant concealment; role separation; hostile HTML inert; suggestions cannot mutate; matching replay returns one candidate/case; conflicting replay 409; revoked Membership denies before replay. | Disable candidate creation/review routes; existing candidates remain evidence and accepted cases remain owner records. |
| MVP-2D3 | Configurable polling, default three hours, one-connector lease, retry/backoff and health. | One active run per connector; cursor advances only after commit; restart resumes; retry creates no duplicate; scheduler-off returns to manual mode. | Disable schedule and keep manual sync/cursor. |
| MVP-2D4 | Attachment metadata acquisition and display only. | Part-level dedupe; limits visible; no bytes in DB/log/event; no download or document association. | Stop metadata fetch/display; message candidates remain valid. |
| MVP-2D5 | Evidence-based evaluation of Gmail `watch` + Pub/Sub in deployed infrastructure. | Topic IAM, authenticated delivery, ack/retry, daily watch renewal, dropped-notification reconciliation, quota/cost/operational runbook. | Stop watch/subscription and return to D3 polling without changing candidate identity. |

Every slice needs migration upgrade/downgrade/re-upgrade where schema changes,
focused unit/integration/security tests, Gmail adapter contract tests with a fake
provider, API/web tests where applicable, compile/build checks, and proportional
regression. No test uses a real mailbox or durable commercial data by default.

## Decisions required from the user

Implementation cannot begin until these values/policies are explicit:

1. Gmail account to connect and whether it is dedicated or shared.
2. Initial Gmail label and/or query; no address/domain is assumed.
3. Initial backfill start date or duration.
4. Known Foodbot and merchant sender addresses/domains, and whether they filter
   or merely raise confidence.
5. Retention period for candidate metadata, sanitized content, dismissed
   candidates, and sync audit.
6. Whether Yarvis may persist the full sanitized body or only a bounded
   sanitized excerpt; the recommendation is the excerpt until operational need
   proves otherwise.
7. Initial frequency; **three hours is recommended** after manual D1 evidence.
8. Who may administer OAuth connections and who may review/accept candidates.
9. Local-only versus deployed redirect URI and Google Cloud project ownership.

## Required ratification and next action

MVP-2D0 creates no implementation authority. Before MVP-2D1, an independent
Amendment must ratify the proposed contract IDs, the three human permissions and
roles, technical connector identity, mailbox/tenant uniqueness, credential
boundary, candidate ownership, and the rule that acceptance alone composes
CMD-009.

**Recommendation:** obtain the nine user decisions, ratify the narrow connector
and intake authority/contract matrix, then implement MVP-2D1 with one explicitly
configured mailbox, `gmail.readonly`, manual bounded synchronization, encrypted
refresh-token storage, and no case creation. Add three-hour polling only after
manual cursor/dedupe/revocation behavior is proven.

## Official technical references

- [Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [Synchronize clients with Gmail](https://developers.google.com/workspace/gmail/api/guides/sync)
- [Configure Gmail push notifications](https://developers.google.com/workspace/gmail/api/guides/push)
- [OAuth 2.0 for web server applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Google OAuth 2.0 best practices](https://developers.google.com/identity/protocols/oauth2/resources/best-practices)
