# YARVIS
# Implementation Roadmap Amendment 020

## Netpay Gmail restricted productive pilot and D2 review slice

## Status

**RATIFIED — NETPAY GMAIL RESTRICTED PRODUCTIVE PILOT AND D2 AUTHORIZED**

This amendment is the ratified decision package requested after the accepted
synthetic/local Gmail Intake D1 Evidence Gate. Its companion `IG-008` opens
Gate A offline implementation only. Google resources, OAuth consent,
credentials, mailbox access, synchronization and real-message persistence
remain closed until the later Gate B and Gate C decisions in this document.

If ratified, this amendment opens only:

1. a local, operator-triggered, read-only productive Gmail connector pilot;
2. the D2 candidate extraction, correlation and human-review slice; and
3. the minimum Inbox UI needed to connect, validate, synchronize and review.

**GMAIL INTAKE D3 REMAINS NOT AUTHORIZED.** There is no scheduler, polling,
worker, queue, Pub/Sub, webhook, Gmail `watch`, automatic follow-up, send,
reply, draft creation in Gmail, label mutation, archive or delete.

## 1. Base, authority and documentary reconciliation

| Field | Value |
| --- | --- |
| Branch | `feat/netpay-gmail-intake-sentinel` |
| Exact base | `b6bc5930ae8b608ff55aa9849e995cb7639966d7` |
| D1 result | `ACCEPTED EVIDENCE — D1 CONFORMANCE ESTABLISHED — GATE PASSED` for the synthetic/local source slice |
| Proposed amendment ID | `IMPLEMENTATION_ROADMAP_AMENDMENT_020` |
| Proposed implementation gate ID | `IG-008` |
| Existing D1/D2 contracts | Amendment 019 §5, registered as ratified/planned metadata |
| D3 | Not authorized |
| D2-Lite Operational Data | Unchanged; not authorized by this amendment |

Amendment 019 §§1, 8, 10 and 13 and IG-007 §§2, 3 and 6 close productive
OAuth/Google/real-pilot work and condition D2 on a separate decision after the
D1 Evidence Gate. This amendment is that proposed later act; it has no effect
until ratified.

IG-007 §4 previously overdeclared D2 evidence as part of D1. The corrected
text now matches Amendment 019 §9.1 and the reproducible D1 record: D1 proved
source capture, deduplication, failure/cursor behavior and readback only.
Classification, candidate state, aging, human acceptance and frontend review
remain D2 work governed here.

## 2. Decisions requested

Ratification accepts all of the following as one bounded pilot package:

1. activate D2 after the already accepted D1 synthetic Evidence Gate;
2. implement the official Gmail API adapter using only
   `https://www.googleapis.com/auth/gmail.readonly`;
3. configure a local loopback OAuth client and an encrypted local pilot secret
   store referenced only through opaque `credential_secret_ref` values;
4. perform a manual, maximum 30-day, single-mailbox pilot for the canonically
   verified Netpay Organization;
5. add the minimum `/netpay/inbox` Gmail UI for connection status, validation,
   manual sync, candidate/source review and unresolved items; and
6. produce real-message evidence for at least one approved pilot message while
   keeping all real content out of Git, test fixtures, screenshots and logs.

Ratification does not authorize D3 or broader deployment.

## 3. Canonical pilot binding

The pilot is limited to the identifiers already recorded by ratified design:

| Binding | Required value |
| --- | --- |
| Organization | `Distribución Netpay` |
| Organization ID | `59650e6f-ad62-40c3-8cb0-7710a122ce8b` |
| Mailbox | The single mailbox recorded in Amendment 018 and reverified by Gmail `users.getProfile` during connection |
| Label display name | `Yarvis/Netpay-Intake` |
| Canonical label | Exact provider `label_id`, discovered once and revalidated before every sync |
| Initial window | Maximum 30 calendar days |
| Trigger | Authorized human manual action only |
| Scope | `https://www.googleapis.com/auth/gmail.readonly` only |

The mailbox address, sender, recipient, domain, subject, body, Store ID, OIDC
claim or request payload never selects the Organization. Current canonical
Principal and active Membership evidence must be revalidated at use time; the
withheld UUIDs remain outside documentation and logs.

## 4. Existing Google project reuse decision

Repository inspection found Google Workspace OIDC configuration surfaces and
deployment placeholders, but no non-secret Google Cloud project ID, Gmail API
configuration, consent-screen record or locally configured `gcloud` project.
The repository therefore cannot prove that an existing Yarvis Google project
is reusable.

Before creating a project, the authorized operator must inspect the existing
Google Cloud organization and record only these non-secret facts in the pilot
manifest:

- project ID and project number;
- enterprise owner/organization;
- consent-screen audience and publishing status;
- whether Gmail API can be enabled without affecting the login OIDC client;
- whether a separate OAuth client can be created for this pilot; and
- confirmation that no broader Gmail scopes are already granted to that client.

Reuse is approved only when all facts pass and the pilot uses a distinct OAuth
client and credential from Yarvis login OIDC. The Gmail token must never share
the OIDC client secret or session path. If evidence is missing or ownership is
ambiguous, fail closed; a dedicated enterprise project named
`yarvis-netpay-intake` remains the approved fallback, but its creation still
requires the ratified `IG-008` gate.

## 5. OAuth topology and secret boundary

The restricted local pilot uses an OAuth Web application client with exactly
this loopback callback:

`http://127.0.0.1:8000/netpay/gmail/oauth/callback`

For this pilot, this Web application client decision supersedes only the
provisional Desktop/local client choice recorded before a Yarvis browser UI
existed. It does not authorize a deployed redirect URI. Google permits an HTTP
localhost/IP redirect for local testing, but the configured URI must match
exactly, including scheme, host, port and path.

The authorization request must use the exact Gmail read-only scope, offline
access, PKCE, a server-generated state bound to the authenticated Principal,
Organization and short expiry, and incremental authorization disabled. The
callback verifies state and the Gmail profile before storing a credential.

The local pilot secret boundary is an AES-256-GCM encrypted file store mounted
outside the repository. PostgreSQL stores only an opaque reference of the
form `file-aesgcm://netpay-gmail/<connection-id>`. The encryption key, OAuth
client secret and encrypted token files are separate host files with access
limited to the API process and the operator account. No secret value may enter
Git, Compose YAML, frontend state, URL query logging, Events, ordinary logs,
fixtures, screenshots or evidence documents.

The exact configuration names and non-secret values are:

| Name | Exact pilot value |
| --- | --- |
| `YARVIS_GMAIL_INTAKE_ENABLED` | `true` only during the approved pilot |
| `YARVIS_GMAIL_PROVIDER` | `google` |
| `YARVIS_GMAIL_GOOGLE_PROJECT_ID` | Existing project ID after §4 verification, otherwise the created `yarvis-netpay-intake` project ID |
| `YARVIS_GMAIL_OAUTH_REDIRECT_URI` | `http://127.0.0.1:8000/netpay/gmail/oauth/callback` |
| `YARVIS_GMAIL_OAUTH_SCOPES` | `https://www.googleapis.com/auth/gmail.readonly` |
| `YARVIS_GMAIL_OAUTH_CLIENT_ID_FILE` | `/run/secrets/netpay-gmail-client-id` |
| `YARVIS_GMAIL_OAUTH_CLIENT_SECRET_FILE` | `/run/secrets/netpay-gmail-client-secret` |
| `YARVIS_GMAIL_TOKEN_KEY_FILE` | `/run/secrets/netpay-gmail-token-key` |
| `YARVIS_GMAIL_TOKEN_STORE_ROOT` | `/run/secrets/netpay-gmail-tokens` |
| `YARVIS_GMAIL_MAILBOX_BINDING` | opaque local binding key; never an email address |
| `YARVIS_GMAIL_LABEL_NAME` | `Yarvis/Netpay-Intake` |
| `YARVIS_GMAIL_BACKFILL_DAYS` | `30` |

Secret contents are supplied through files outside the checkout. They must not
be pasted into chat or passed on command lines. Disabling the feature flag must
fail closed before provider access.

`gmail.readonly` is a Google restricted scope. Gate B must therefore record
whether the project is an Internal Workspace application or an External app in
Testing, whether Workspace Admin approval is required, and which verification
or security-assessment exception applies. An External Testing token's limited
lifetime is an operational constraint, not a reason to broaden scope or store
credentials less safely. If the account and project do not belong to the same
verified Workspace organization and no acceptable testing/internal path is
available, Gate B fails closed.

## 6. Productive source adapter behavior

The adapter may call only read operations required for:

- `users.getProfile` to verify the stable mailbox account;
- `users.labels.list/get` to resolve and revalidate the exact `label_id`;
- `users.messages.list/get` for approved messages and bounded metadata/content;
- `users.history.list` for incremental manual synchronization after the first
  accepted cursor.

It may request only the minimum message representation needed to extract
headers, sanitized plain text and safe attachment metadata. It never downloads
attachment bytes. Provider errors are mapped to controlled codes; raw Google
responses, addresses, bodies, message IDs, tokens and exceptions never enter
ordinary logs or Events.

Invalid/revoked credentials, mailbox mismatch, label mismatch, tenant
ambiguity, history expiry, retention failure or a changed immutable fingerprint
fails closed. A bounded rescan retains D1 deduplication and advances the cursor
only after the entire accepted transaction commits.

## 7. D2 candidate and analysis boundary

Each source item produces at most one tenant-owned candidate. D2 preserves the
source item and records extracted facts separately from suggestions and
inferences.

The minimum candidate includes:

- request type and normalized request description;
- exact ticket/case references found in subject or content;
- Gmail message/thread IDs through protected source references;
- exact commerce, branch or Store identifiers when present;
- terminal identifiers and serial numbers when present;
- carrier, tracking number and reported shipment state when present;
- request, pending information and suggested next action;
- received time, derived age, priority, suggested responsible and follow-up;
- extraction method/version/confidence and source spans;
- contradiction and missing-data codes; and
- review state and any human-confirmed owner link.

Initial analysis is deterministic and versioned. An external AI provider is
not authorized by this amendment; adding one requires a later privacy/provider
decision because it would transmit real mailbox content externally.

Correlation across different Gmail threads may use exact ticket/case number,
tracking number, terminal serial, Store ID or another verifiable identifier.
Name similarity alone may suggest a match but may never confirm it. Missing or
conflicting evidence produces `pending_link` and remains visible for review.

Facts and inferences are distinct. A shipment fact does not establish delivery
or activation. “Esperando recolección” does not establish a terminal return.
Contradictory values remain side by side with source references.

Only an authorized human may accept, reject, mark duplicate or link. Any
creation/link of `CommercialIntakeItem` or `NetpayServiceCase` must call the
existing owning contract and remain same-tenant and idempotent. Automatic owner
creation and Master mutation are prohibited.

## 8. Minimum interface

The existing `NetpayInboxWorkspace` receives one Gmail section containing:

- connection state, safe last attempt/success and actionable controlled error;
- `Connect`, `Validate`, `Synchronize now` and local `Disconnect` actions;
- explicit 30-day initial window and label binding;
- candidate list with new, needs-review, pending-link and overdue filters;
- candidate detail with facts, inferences, contradictions and source evidence;
- source message/thread provenance and safe attachment references;
- human accept, reject, duplicate and link actions; and
- a persistent banner stating that no Gmail or external mutation is available.

No token, authorization code, client secret, refresh token, provider exception
or raw provider payload reaches the browser.

## 9. Real-pilot manifest and execution

The pilot is restricted to exactly 10 messages from the verified label and
30-day window. Before content ingestion, the connector may run a metadata-only
discovery step that returns at most 10 opaque message IDs and timestamps to the
server. It stores only HMAC identifiers bound to the connection and label.
The authorized operator approves that immutable manifest before the first
message-content fetch.

Only manifest entries may be ingested during the pilot. Other labelled
messages do not create source items and do not advance the pilot cursor. Real
content, subjects, addresses and raw IDs stay out of Git and evidence files.

The pilot succeeds only when at least one manifest message completes:

`Gmail read -> source persistence -> D2 analysis -> UI review -> database-session reload/readback`

Evidence records safe local object IDs, counts, timestamps, contract IDs,
controlled states and hashes. It never records mailbox content or credentials.

## 10. Contract use

The package activates only the already allocated Amendment 019 contracts:

- connector/manual source: `CMD-016`, `CMD-017`, `QRY-014..017`,
  `EVT-020..025` and failure `EVT-010`;
- D2 candidates: `CMD-018`, `CMD-031..035`, `QRY-007..008`,
  `QRY-018..019`, and `EVT-007..008`.

`CMD-036` reply-draft generation is not activated by this pilot. No new
canonical contract ID is created or reserved.

## 11. Authorized File Boundary after ratification

The implementation may modify only:

- `apps/api/requirements.txt`
- `apps/api/src/yarvis_api/config.py`
- `apps/api/src/yarvis_api/bootstrap.py`
- `apps/api/src/yarvis_api/models/__init__.py`
- `apps/api/src/yarvis_api/models/netpay_gmail_intake.py`
- `apps/api/src/yarvis_api/schemas/netpay_gmail_intake.py`
- `apps/api/src/yarvis_api/services/netpay_gmail_provider.py`
- `apps/api/src/yarvis_api/services/netpay_gmail_intake.py`
- `apps/api/src/yarvis_api/api/routes/netpay_gmail_intake.py`
- `apps/api/src/yarvis_api/api/routes/netpay_inbox.py`
- `apps/api/tests/test_netpay_gmail_intake.py`
- `apps/web/src/api/netpay.ts`
- `apps/web/src/components/netpay/NetpayInboxWorkspace.tsx`
- `apps/web/src/components/netpay/NetpayInboxWorkspace.test.tsx`
- `docker-compose.yml` only for non-secret file mounts and typed settings;
- `.gitignore` only for local Gmail secret/evidence artifacts; and
- current-state, gate, runbook and non-sensitive evidence documents.

It may create only:

- `apps/api/src/yarvis_api/services/netpay_gmail_google_provider.py`
- `apps/api/src/yarvis_api/services/netpay_gmail_secret_store.py`
- `apps/api/src/yarvis_api/services/netpay_gmail_classification.py`
- one Alembic revision after the actual graph is verified;
- focused provider, security, migration and D2 tests;
- `apps/web/e2e/netpay-gmail-intake.spec.ts` and synthetic fixtures; and
- an ignored local directory for real-pilot safe runtime evidence.

No migration revision is reserved. At this base, `20261008_48` is the single
merge head descending from the four D1 heads. Implementation must run
`alembic heads` again and prove upgrade, downgrade and re-upgrade.

## 12. Evidence Gates

### Gate A — implementation conformance before Google access

Must pass with fake Google transport and synthetic data:

- scope and endpoint allowlists;
- PKCE/state/expiry/replay and callback tenant binding;
- encrypted store non-disclosure, rotation and revocation;
- exact mailbox/Organization/label fail-closed behavior;
- D1 backfill, incremental retry, dedupe, conflict and cursor invariants;
- deterministic D2 extraction, cross-thread correlation and pending-link logic;
- facts/inferences/contradictions separation;
- same-tenant human review and owner-link idempotency;
- reload/readback and UI/browser E2E;
- migration round-trip, backend/frontend regression, typecheck/build and static
  checks; and
- negative proof for all Gmail mutation methods and D3 infrastructure.

Gate A acceptance is required before OAuth consent or mailbox access.

### Gate B — Google/OAuth and immutable manifest

The Architecture Authority must accept the non-secret project reuse record,
exact client type/callback, consent audience, scope, verified Principal,
Membership, Organization, mailbox profile, label ID and 10-message HMAC
manifest. Secrets remain outside the acceptance record.

### Gate C — restricted real-pilot evidence

Run once manually. Prove at least one real message through persistence,
analysis, UI review and database-session readback; prove idempotent retry;
prove no message or mailbox mutation; record only safe counts, IDs/hashes and
controlled states. A pass authorizes no continuation, scheduling, deployment
or second mailbox.

## 13. Rollback and revocation

Rollback sets `YARVIS_GMAIL_INTAKE_ENABLED=false`, disables all provider routes,
revokes the OAuth grant in Google, deletes the encrypted token through the
approved store, preserves safe source/candidate/audit evidence, and leaves
existing Inbox/Commercial Intake/Case records intact. Credential compromise,
Membership loss, mailbox mismatch, cross-tenant anomaly or retention failure
triggers immediate fail-closed disablement.

## 14. Ratification record required

To activate this amendment, the Architecture Authority must record:

- Decision: `RATIFIED — NETPAY GMAIL RESTRICTED PRODUCTIVE PILOT AND D2 AUTHORIZED`;
- Authority name;
- decision date;
- accepted commit/SHA-256 after publication;
- accepted project path: reuse after evidence, or dedicated fallback;
- `IG-008 — RATIFIED`; and
- explicit confirmation that D3 and D2-Lite remain unauthorized.

### Ratification record

| Field | Accepted value |
| --- | --- |
| Decision | `RATIFIED — NETPAY GMAIL RESTRICTED PRODUCTIVE PILOT AND D2 AUTHORIZED` |
| Authority | User-confirmed Architecture Authority |
| Decision date | `2026-10-08 America/Mexico_City` |
| Accepted Amendment 020 SHA-256 | `3f407daf60f780ea8e12c836b631952d067a476f019d0fa47c2af138248a4936` |
| Accepted IG-008 SHA-256 | `e3810e4f5a0b02b5059b923be4356b78bc53b4e08028de668bc934931cf15b43` |
| Hash basis | Canonical UTF-8 without BOM; CRLF and lone CR normalized to LF |
| Active gate | `IG-008 Gate A — OFFLINE IMPLEMENTATION AND CONFORMANCE` |
| Closed gates | Gate B Google/OAuth/manifest; Gate C real pilot; D3; D2-Lite |

The explicit user decision verified both hashes before this record was added.
Gate A may proceed from base
`b6bc5930ae8b608ff55aa9849e995cb7639966d7`. Passing Gate A prepares Gate B;
it does not itself authorize Google access.
