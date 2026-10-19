# Netpay Gmail Gate A continuity checkpoint

Last updated: 2026-10-09 (America/Mexico_City)

## Authority and gates

- Base HEAD: `b6bc5930ae8b608ff55aa9849e995cb7639966d7`.
- Active authority: ratified Amendment 020 and IG-008.
- Active gate: Gate A, offline implementation and conformance.
- Closed: Gate B Google/OAuth/manifest, Gate C real mailbox pilot, D3 and D2-Lite.
- A later bounded real OAuth consent reached profile/label validation and failed closed on mailbox
  mismatch. No Gmail message access or manifest discovery has occurred.

## Completed blocks

- Canonical ratification hashes verified and recorded.
- Alembic graph: single head `20261008_49`, descending from `20261008_48`.
- Migration round trip completed: clean upgrade, downgrade to `20261008_48`, re-upgrade and idempotent re-upgrade.
- Focused backend tests: 7 passed before the final OAuth/config additions.
- Focused Gmail intake tests after OAuth additions: 6 passed.
- Focused frontend tests: 11 passed after the Gmail workspace changes.
- Explicit TypeScript traversal from `src/main.tsx`: passed after removing one stale undefined reference.
- Vite production build: passed to an ephemeral `%TEMP%` output directory.
- Ruff on the Gate A Python surface: passed after the latest fixes.

## Work present in the tree

- Restricted Google provider and local OAuth coordinator with exact readonly scope.
- AES-GCM credential-reference store and local revocation path.
- 30-day/label/approved-manifest boundary with metadata-only discovery.
- D2 deterministic extraction, exact-identifier cross-thread correlation, pending-link behavior,
  facts/inferences/contradictions and human review dispositions.
- Minimal Gmail Inbox UI with connection state, controlled errors, manual actions, filters,
  overdue candidates and source evidence readback.
- Synthetic browser seed and Playwright scenario.

## Closure

Gate A passed on 2026-10-09. Accepted results are recorded in
`docs/engineering/evidence/netpay-gmail-gate-a-conformance-20261009.txt`.
The browser scenario passed twice with real Microsoft Edge and SQL readback. Backend relevant
regression, fake Google transport, frontend regression, types, lint, compilation, build,
migration round trip and mutation-negative checks passed. Gate B handoff is prepared in
`docs/engineering/NETPAY_GMAIL_GATE_B_HANDOFF.md`; Gate B/C remain closed.

## Reproduction commands

Use the four Compose files in this order:

```text
docker compose --env-file NUL -f docker-compose.yml -f scripts/d1-conformance.compose.yml -f scripts/d1-browser.compose.yml -f scripts/d1-gmail-browser.compose.yml up -d postgres api web
```

The real-browser command uses the installed Microsoft Edge channel and ephemeral output paths:

```text
set D1_BROWSER_BASE_URL=http://127.0.0.1:5174
set D1_BROWSER_CHANNEL=msedge
npx playwright test e2e/netpay-gmail-intake.spec.ts --workers=1
```

## Safety

This checkpoint contains synthetic identifiers only. It contains no credential, OAuth code,
token, Gmail content, real mailbox address or real provider identifier. `AUDIT_REPORT.md` is
outside the work package and must remain untouched and unstaged.

## Gate B continuity — local preparation

- The supplied directory contained exactly one OAuth JSON candidate.
- Safe validation passed: Web application, project `yarvis-pilot`, project-number prefix
  `1030218466633`, exact callback and standard Google OAuth endpoints.
- OAuth values were split into protected host files outside the repository without printing them.
- No previous Gate B key existed. A 32-byte nonzero random AES key was created. An unsupported
  initial RNG call was replaced before any ciphertext existed; the replacement was verified as
  exactly 32 decoded bytes.
- The encrypted token directory remains empty. No token, code or mailbox binding exists.
- Local runtime and Compose configuration contain the exact readonly scope, callback, 30-day
  boundary and label, with scheduler and worker disabled.
- The hidden-input mailbox binding helper and non-secret preflight helper are ready.

Gate B remains **PENDING**. Offline configuration proves the scope Yarvis will request, while
Google consent-screen scope configuration, applicable Workspace Admin trust/approval and the
label `Yarvis/Netpay-Intake` require operator verification. The mailbox binding must be created
through hidden local input before runtime preflight can pass. At this preparation stage no OAuth
URL had been generated and no Google or Gmail API call had occurred.

## Gate B continuity — verified runtime and next boundary

- The reuse record now identifies `Yarvis Pilot` / `yarvis-pilot` / `1030218466633`, Internal
  audience and the separate `Yarvis Netpay Intake` Web client.
- API health and the Gmail Inbox UI returned HTTP 200 at the ratified callback host and local UI
  runtime; the database is at Alembic head `20261008_49`.
- Runtime preflight passed the exact provider, project, scope, callback, 30-day window, label and
  disabled scheduler/worker checks. Only `mailbox_binding_present` remains pending locally.
- Both Gate B helpers compile with an ephemeral cache and pass Ruff; `git diff --check` passes.
- The non-secret preflight record is
  `docs/engineering/evidence/netpay-gmail-gate-b-preflight-20261009.txt`.
- Before OAuth, the operator must confirm the exact Data Access scope, obtain the applicable
  Workspace API Controls decision, confirm the Gmail label and create the mailbox binding using
  hidden local input.
- The UI entry point is `http://127.0.0.1:5173/netpay-inbox/gmail`. Do not select Connect until
  those checks are recorded. The one-time Google URL will then be generated with state and PKCE.

Gate B is still **PENDING**. Gate C, content access, synchronization, D3 and D2-Lite remain
closed. At this runtime-verification stage no OAuth flow or Google/Gmail API request had been made.

## Gate B continuity — Workspace administration disposition

- Workspace administration is `UNVERIFIED`: the pilot operator cannot enter Google Admin
  Console because an administrator account is required.
- This is not evidence that OAuth is blocked. Effective Workspace policy remains `UNKNOWN`.
- IG-008 §4.B.4, §4.B.10 and §9 permit one bounded normal consent attempt after scope, mailbox
  binding and label readiness. Amendment 020 §12 requires profile and label-ID verification as
  part of Gate B.
- The existing callback exchanges the code and calls only Gmail profile and label-list endpoints;
  it does not list or fetch messages. Any denial or validation mismatch stops the path.
- At this governance-disposition stage the consent attempt had not run. A later bounded attempt
  failed closed on mailbox mismatch and is recorded below.

## Gate B continuity — local authority correction

- The first browser visit produced HTTP 403 for Gmail connections/candidates and `oauth/start`.
- The runtime uses deterministic local authentication. The Gate B web overlay omitted its subject
  and token, and the current database contained no Principal, Membership or productive session.
- An idempotent seed now creates one active `netpay-gmail:operator` Principal with one active
  `netpay_inbox_operator` Membership in the active `Netpay Gmail Pilot` Organization.
- The frontend sends that bounded deterministic identity and advertises only
  `netpay.inbox.read,netpay.inbox.manage`. No global role or permission bypass was added.
- `GET /netpay/gmail/connections` and `GET /netpay/gmail/candidates` now return HTTP 200.
- The protected preflight now reports `mailbox_binding_present=PASS`; no binding value was shown.
- That rejected `oauth/start` request did not enter its handler, generate an authorization URL or
  contact Google. A later authorized consent attempt is recorded below.

Gate B remains **PENDING** for exact Google scope confirmation, label confirmation, bounded
consent/profile/label validation and the immutable ten-message manifest.

## Gate B continuity — mailbox mismatch remediation

- The rejected consent returned `mailbox_mismatch`. Safe inspection found one control character
  at the beginning of the encrypted binding, consistent with terminal paste framing. The domain,
  token, authorization code, callback parameters and complete addresses were not printed.
- Case normalization was already strict and was not the cause. The callback continues to require
  an exact case-folded mailbox match; no alternate account or bypass is accepted.
- The binding helper now rejects non-ASCII/control characters, requires two matching hidden
  entries and permits replacement only with explicit `--replace`.
- The callback now consumes a failed OAuth attempt and deletes its PKCE verifier before returning
  the controlled mismatch error. A replay of the same synthetic attempt returns 409.
- Focused binding-helper tests: 3 passed. Focused fake-Google callback test: 1 passed, 5
  deselected. Ruff and `git diff --check`: passed.
- The first containerized callback-test invocation stopped during configuration validation because
  productive Gmail was enabled in a test environment. It made no provider call. The successful
  rerun explicitly disabled the productive adapter and used only the in-memory fake coordinator.
- The pre-existing rejected real attempt was explicitly invalidated: 0 unconsumed attempts, 1
  consumed audit row and 0 encrypted OAuth-attempt verifier files.
- Post-cleanup state: 0 Google connections and 0 encrypted credential files.
- Current preflight: binding present but `mailbox_binding_valid=PENDING` until the operator replaces
  it by typing the authorized address manually twice.

Gate A retains its accepted evidence except for these affected controls, which now pass with
synthetic transport. Gate B remains **PENDING** and Gate C remains closed. No message or manifest
operation occurred.

## Gate B continuity — successful connection and manifest hold point

- A fresh OAuth flow completed with the corrected binding. One Google connection is persisted in
  `ready` state with a nonempty label ID, verified-mailbox timestamp, no controlled error, manifest
  `none` and no previous sync.
- A separate Validate action rechecked only Gmail profile and the exact label and returned `ready`.
  It did not list or fetch messages.
- The encrypted binding matches the persisted provider account after normalization. The credential
  reference is opaque, the stored scope list is exactly `gmail.readonly`, access/refresh values are
  present and no manifest message IDs are stored yet. No secret value was printed.
- Principal, `netpay_inbox_operator` Membership and `Netpay Gmail Pilot` Organization are active.
- Persisted content boundary: 1 ready Google connection, 0 sync executions, 0 source items and 0
  candidates.
- Existing-project reuse, Web client/callback, Internal audience, exact scope, Principal,
  Membership, Organization, mailbox profile and label ID pass. Workspace administration remains
  `UNVERIFIED`; the successful consent establishes that the effective policy allowed this bounded
  account flow and did not return an administrative denial.
- Gate B is **PENDING**, because IG-008 §4.B.11 and Amendment 020 §12 still require discovery,
  operator review and Architecture Authority acceptance of exactly ten HMAC manifest entries.
- The UI now renders every opaque HMAC handle and receipt timestamp before approval. Approval is
  disabled unless status is `discovered` and the entry count is exactly 10.
- Focused frontend result: 4 tests passed. Explicit TypeScript traversal with `vite/client`: PASS.
  Vite production build: PASS. `git diff --check`: PASS.

The next authorized action is manual selection and labeling of exactly ten messages within the
30-day window, followed by **Discover manifest** only. Stop before **Approve 10 messages** or
**Synchronize 30 days** so the ten opaque entries can be reviewed. Gate C remains closed and no
automation is active.

## Gate B continuity — duplicate OAuth and exact-label boundary

- A second Connect action against the already-ready mailbox reached the callback and returned an
  infrastructure failure. Sanitized logs identified a unique-key violation on
  `uq_netpay_gmail_connections_org_account`; no callback parameters, complete address or token was
  retained in this record.
- The original connection remained the sole persisted Google connection. A fresh profile/label
  validation returned `ready`, no controlled error, manifest `none` and no prior sync.
- The failed duplicate left one unconsumed OAuth attempt/PKCE file and one credential file not
  referenced by any connection. The cleanup consumed exactly that attempt and removed exactly the
  PKCE and orphan credential. Final state: 1 credential file, 1 referenced credential, 0
  unconsumed attempts and 0 OAuth-attempt files.
- The API now rejects OAuth start with HTTP 409 `gmail_connection_already_ready` when the
  Organization already has a ready/succeeded Google connection. A racing duplicate callback
  preserves the existing credential, consumes its attempt and redirects without storing the new
  credential. The UI disables Connect while such a connection is active.
- Focused fake-Google OAuth test: 1 passed, 5 deselected. Gmail UI tests: 4 passed. Ruff,
  TypeScript and `git diff --check`: passed.
- Manifest discovery calls `messages.list` with only the persisted parent `label_id`. Gmail label
  IDs are exact and immutable; sublabels have separate IDs. Messages carrying only a child label
  are excluded. A message carrying the exact parent label is included even if it also carries a
  child label.
- To keep the pilot bounded, remove the exact parent label from all other messages and apply that
  parent label directly to exactly ten selected messages. Child labels may organize those ten but
  do not substitute for the parent label.

Gate B remains **PENDING**. No manifest discovery, approval, synchronization or message-content
read occurred during this remediation. Gate C remains closed.

## Gate B continuity — discovered-manifest UI recovery

- The persisted connection reports manifest status `discovered`, exactly 10 opaque HMAC entries,
  `manifest_approved=false` and no synchronization execution.
- The API returned all ten review entries, but the active Vite development server was still
  serving an older transformed module that omitted the review section. The bind mount already
  contained the current source, so only the `web` service was restarted; API, database, OAuth
  connection and encrypted credentials were not restarted or modified.
- After restart, the module served over HTTP contains the `Manifiesto HMAC para revisión`
  section and the opaque-entry count text. The focused component suite passes: 4 tests, including
  the ten-entry pre-approval view.
- No manifest approval or synchronization was invoked. Gate B remains **PENDING** until the ten
  entries are reviewed and accepted under IG-008; Gate C remains closed.

Next action: reload `/netpay-inbox/gmail` without cache and review the ten opaque handles and
receipt timestamps. Stop before **Approve 10 messages** and **Synchronize 30 days**.

## Gate B PASS and Gate C entry — 2026-10-10

- The Architecture Authority manually reviewed and approved the immutable manifest.
- API and fresh database-session checks show one connection in `ready`, no controlled error,
  verified mailbox and exact label, manifest `approved`, exactly 10 entries, a persisted approval
  timestamp, zero sync runs and no prior `last_sync_at`.
- The encrypted credential record remains opaque and contains exactly 10 manifest message IDs and
  the manifest HMAC key. No identifier or secret was printed.
- The offline runtime preflight passes: feature enabled, Google provider, accepted project,
  readonly-only scope, exact callback, 30-day backfill, exact parent label, scheduler disabled,
  worker disabled and valid encrypted mailbox binding.
- Existing evidence already establishes the separate Web client, Internal audience, effective
  bounded consent, Principal, Membership, Organization, profile and label validation. Workspace
  administration remains `UNVERIFIED`; no administrative denial occurred and no broader policy
  claim is made.
- The productive provider intersects Gmail results with the ten protected manifest IDs before any
  `messages.get` call. Its initial list query also applies the exact label and explicit 30-day
  start/end bounds. It now fails closed with `pilot_manifest_invalid` unless the protected record
  contains exactly ten distinct IDs. New or unrelated mailbox messages cannot enter this first
  pilot run. Two direct synthetic boundary checks and Ruff pass.

**Gate B: PASS.** The IG-008 Gate C entry conditions are met. The next allowed action is one
operator-triggered **Synchronize 30 days** request. No synchronization or automation was executed
while recording this checkpoint. Gate C remains pending evidence; D3 and D2-Lite remain closed.

## Gate C first attempt and concurrency remediation — 2026-10-10

- The operator selected **Synchronize 30 days** twice. Fresh API and database-session readback
  found two completed runs, both `succeeded`, each with captured 0, deduplicated 0, conflicts 0,
  failed 0 and no failure code.
- Persisted result: 0 source items, 0 candidates, 0 candidate-owner effects, 2 start Events and 2
  completion Events. There are no source/candidate duplicates. Manifest-membership comparison is
  vacuously true because no content record was created; this attempt does not prove real ingestion.
- Root cause: OAuth connection setup persisted the Gmail profile history cursor. The first content
  sync treated that bootstrap cursor as an accepted incremental cursor and therefore did not run
  the initial bounded manifest query.
- The service now uses an incremental cursor only after at least one source item exists. A
  source-empty connection always performs the bounded initial manifest read. The Google provider
  still intersects results with exactly ten protected IDs before content fetch.
- Frontend operations now have a synchronous in-memory guard and hide/disable mutation controls
  while one request is active. Backend sync acquires a per-connection PostgreSQL row lock with
  `SKIP LOCKED` and rejects an overlapping/running request with `gmail_sync_in_progress`.
- Focused backend check: 1 passed, proving bootstrap-cursor suppression and running-request 409.
  Focused frontend check: 5 passed, including one-call behavior while sync is active. Ruff and
  compileall pass. The Vite production build passes using an isolated temporary output directory.
  A standalone strict TypeScript project is not configured and React type declarations are absent;
  the attempted ad-hoc compiler invocation is therefore not claimed as a TypeScript pass.
- The API service was restarted to load the remediation. PostgreSQL, OAuth connection and encrypted
  credentials were preserved. No further sync was executed.

**Gate C remains PENDING.** A later explicitly operator-triggered run must produce real source and
candidate records before UI review, reload/readback and idempotent retry evidence can be collected.

## Gate C local candidate review correction — 2026-10-10

- A later operator run had already produced 10 source items and 10 one-to-one candidates from the
  approved manifest. No additional synchronization or Gmail call was made during this block.
- Human inspection of the first candidate exposed three deterministic-rule defects: generic
  e-commerce mention implied activation, explanatory failure language implied high priority, and
  alternative MIME representations produced a repeated review description.
- The authorized `support_or_incident` taxonomy value now covers explicit e-commerce rejection and
  response-code review. Activation requires activation language. Priority is normal unless the
  message contains an explicit urgency or blocking signal.
- Subject observations now retain an unverified commerce name and an untyped external identifier;
  neither creates a ticket, correlation key or owner link. The requested review and numeric claims
  are attributed to the message and marked unverified. The proposed next action combines verified
  commerce identification with routing the rejection review, without inventing an assignee.
- The UI now labels the calculated timestamp as a derived follow-up threshold and separately shows
  that no explicit deadline was reported. Exceeding that threshold is not presented as an asserted
  contractual deadline.
- Future MIME ingestion prefers `text/plain` within `multipart/alternative` and falls back to HTML
  only when plain text is absent. Attachment metadata remains metadata-only. The persisted source
  was not rewritten; its candidate description uses a local duplicate-suppressed review view.
- Immediately before local reprojection, the candidate again had no human decision, immutable
  disposition or owner link. The guarded reprojection retained the same candidate ID, source ID and
  fingerprint; source content was byte-for-byte unchanged. Result: D2 rules v2, normal priority,
  pending link, three attributed reported claims, no ticket and no automatic link.
- Persisted readback: 3 runs (first two empty; third captured 10), 10 unique source items, 10
  candidates with 10 unique source references, 0 reviewed dispositions and 0 owner links. All ten
  source IDs equal the ten protected IDs in the approved manifest; no raw ID was printed.
- Verification: backend classification/MIME suite 7 passed; direct classification/reprocessing
  checks 3 passed; Gmail UI 5 passed; Ruff, compileall, Vite build and `git diff --check` passed.

**Gate C remains PENDING.** The corrected candidate still requires operator visual review. A
post-success idempotent retry and final safe mutation-negative/readback evidence also remain.

## Gate C operational review UI — 2026-10-10

- The candidate workspace now renders a one-row-per-candidate operational list with subject,
  observed commerce, Spanish request type, priority, state and an explicit selected state.
- The detail places request, observed commerce/external ID, state, next action and follow-up before
  the message body. Facts, sender-reported claims, inferences and missing data remain distinct and
  show provenance/verification when persisted. Raw JSON, the complete locally persisted message,
  source evidence and attachment metadata are collapsed by default; attachments are not fetched.
- Acceptance and linking explain their prerequisite and remain disabled until the operator searches
  the authorized local case/commercial-intake endpoints and selects a verified destination record.
  An observed external ID is never copied into the internal owner ID.
- Responsive `minmax(0, …)`, wrapping and single-column breakpoints prevent horizontal overflow;
  the review controls remain sticky on wide layouts and become inline on narrow layouts. The shared
  in-flight guard and disabled controls protect mutations from repeated clicks, and successful
  mutations expose a persisted-result notice.
- Verification commands: `npm.cmd test -- --run
  src/components/netpay/NetpayGmailIntakeWorkspace.test.tsx`; `npx.cmd vite build --outDir
  %TEMP%\yarvis-gmail-ui-build --emptyOutDir`; `git diff --check`. No Gmail request,
  synchronization, attachment download, source mutation or candidate decision occurred.

**Gate C remains PENDING.** Operator visual confirmation of this presentation and the remaining
post-success idempotent retry plus final mutation-negative/readback evidence are still required.

## Gate C served-runtime and visual verification — 2026-10-10

- `127.0.0.1:5173` is served by Compose service `web` (`ctooffice-web-1`), working directory
  `/app`, with the repository `apps/web` directory bind-mounted read/write at `/app`; its command is
  `npm install && npm run dev`.
- The mounted component contained the current operational UI, while Vite initially returned a stale
  transformed module. Only the `web` service was restarted. The subsequently served module contains
  `Hechos observados` and `Registro destino verificado`, excludes `ID del dueño`, and serves the new
  responsive Gmail styles.
- A read-only Microsoft Edge/Playwright inspection selected the already persisted corrected
  candidate and verified: subject and observed commerce in its list row; operational summary before
  evidence; collapsed complete-message, source-evidence and technical-JSON sections; local target
  search and the blocked-action explanation; and no horizontal overflow at 1440 px
  (`scrollWidth == clientWidth`, all three `details` closed). No control that mutates state was used.
- The visual screenshot is ephemeral at `%TEMP%\yarvis-gmail-ui.png` and is not repository evidence
  because it contains pilot mailbox material. No Gmail request, synchronization, attachment access,
  candidate decision or persisted-data mutation occurred.

**Gate C remains PENDING.** The UI runtime mismatch is resolved and the operational presentation is
visually verified. The remaining Gate C requirements are the authorized post-success idempotent
retry and final safe mutation-negative/readback evidence.

## Gate C controlled-retry hold point — 2026-10-10

- The Architecture Authority confirmed the corrected candidate visually. Visible request types,
  states, extracted fields, provenance, verification, attribution and missing-data labels are now
  translated to Spanish; the original persisted values remain available only in technical JSON.
- Fresh-session baseline: 10 sources/10 distinct message identities; 10 candidates/10 distinct
  source references; 0 owner links; 0 reviewed or immutable decisions; 3 runs; maximum Gmail event
  sequence 27. Event counts are connected 1, sync started 3, sync completed 3, captured 10 and
  candidate created 10. The connection is succeeded with zero active runs.
- Frontend focused tests pass 5/5, the Vite build to `%TEMP%` passes, and `git diff --check` passes.
- The next allowed action is exactly one operator click on **Sincronizar 30 días**. Wait for the
  loading state to finish and do not click again. Post-retry verification must use a new database
  session and compare sources, candidates, links, decisions, immutable flags and every Gmail Event
  count against this baseline before Gate C can be decided.

**Gate C remains PENDING.** No retry was initiated while recording this checkpoint.

## Human follow-up recording assessment — 2026-10-10

- Operator-supplied follow-up must remain separate from immutable Gmail source evidence and from
  deterministic extraction. It must not imply a ticket, shipment, approval, application or
  resolution that the operator did not confirm.
- The current candidate edit contract can change request type, priority, proposed next action and
  follow-up timestamp. It does not persist a separately readable operator note with author and
  occurrence time. Its `reason` is only command metadata and is not a review-note read model.
- Case activities provide attributed notes only after a verified case exists. Using them now would
  require an unsupported owner link, so they are not applicable.
- MVP gap: an append-only, tenant-scoped candidate follow-up/note contract is required, with operator
  principal, recorded time, optional operator-supplied occurrence time, safe text, provenance
  `operator_reported`, idempotency and readback. It must never modify source evidence or silently
  create/link an owner record. This gap is documented; no new capability is implemented here.
- The proposed candidate next action can be updated through the existing edit command only after the
  controlled retry baseline comparison: verify the status of the internally prepared operational
  form and record post-meeting pending actions; separately confirm whether a ticket exists. No due
  date should be supplied without operator evidence.
- Baseline recheck remains unchanged: sources 10, candidates 10, owner links 0, reviewed decisions 0,
  runs 3 and maximum Gmail event sequence 27. No candidate, source, decision, link or Event was
  modified while assessing this follow-up.

## Gate C PASS and post-gate follow-up edit — 2026-10-11

- One operator-triggered retry produced run 4, `succeeded`, with captured/deduplicated/conflict/
  failed counts 0/0/0/0 and no failure. Sources and candidates remained 10/10 unique; links,
  dispositions and immutable candidates remained 0/0/0; capture/create Events remained 10/10.
  Only the expected unique sync-started/completed audit Events changed sequence 27 to 29.
- The empty incremental run is not the sole idempotency proof. Persistent uniqueness constraints,
  unchanged real readback and previously accepted synthetic redelivery coverage jointly prove no
  duplicate source, candidate, owner link or derived capture/create Event.
- Read-only scope and adapter inspection confirm no Gmail mutation or attachment-download path and
  no D3 infrastructure. All IG-008 acceptance criteria were contrasted and are satisfied. The
  confirmed visual review of one candidate satisfies the minimum human-review requirement; no
  unsupported disposition or owner link was created.
- Only after the retry comparison, one idempotent edit updated that candidate's proposed next
  action. Fresh readback shows one command receipt, `needs_review`, no owner, disposition,
  immutability or explicit deadline, plus one review Event at sequence 30. Browser reload reproduced
  the persisted action. This edit is explicitly excluded from the retry baseline comparison.
- The attributed append-only candidate follow-up-note capability remains an MVP gap. The source and
  extracted evidence were not modified.

**Gate C: PASS.** The restricted Gmail pilot and authorized D2 review slice are evidenced. D3,
D2-Lite, scheduling, Pub/Sub, webhooks, automation and Gmail mutation remain closed.

## IG-009 H1 ratification and implementation preflight — 2026-10-11

- The accepted proposal hashes for the human-follow-up design, Amendment 021 and IG-009 were
  recomputed byte-for-byte and matched the ratification statement.
- `IC-NETPAY-CMD-037`, `IC-NETPAY-QRY-020` and `IC-NETPAY-EVT-027` remain absent from the
  implementation/catalog and are therefore free for the ratified registrations.
- `python -m alembic heads --verbose` reports exactly one real head, `20261008_49`; the H1
  migration must use it as its direct parent.
- Branch is `feat/netpay-gmail-intake-sentinel`; base remains
  `b6bc5930ae8b608ff55aa9849e995cb7639966d7`. Existing Gmail work is preserved.
- Current gate is IG-009 H1 active with evidence pending. IG-008 A/B/C remain PASS. No Gmail
  provider call, synchronization, real note creation, owner link, decision mutation, D3 or
  D2-Lite work is authorized by this block.

**Next reproducible action:** register the three canonical contracts and implement the
candidate-owned append-only model/API with a migration parented by `20261008_49`.

## IG-009 H1 implementation and evidence closure — 2026-10-11

- Registered `IC-NETPAY-CMD-037`, `IC-NETPAY-QRY-020` and `IC-NETPAY-EVT-027` with Amendment
  021/IG-009 traceability. Added append-only candidate follow-up persistence, bounded chronology
  query, idempotent tenant-scoped append command and a safe Event without note content.
- Migration `20261011_50` directly parents `20261008_49`. On isolated `ctooffice_h1/yarvis_test`,
  upgrade/downgrade/upgrade produced `50 -> 49 -> 50`; current and heads both report the single
  `20261011_50 (head)`. The productive pilot database was not downgraded or used for H1 tests.
- Compose backend verification passed 16/16. It covers the five synthetic kinds, null/supplied
  event dates, server-owned actor/time/provenance, replay/conflict, cross-tenant failure before
  replay, stable fresh-session chronology, one-row/one-Event behavior and unchanged source,
  extraction, owner, disposition and next action. Event payload checks exclude note content.
- Frontend focused Vitest passed 6/6; focused TypeScript passed; Vite build passed with 109 modules;
  Ruff, compileall and `git diff --check` passed.
- Playwright CLI 1.64.0 with Microsoft Edge ran against the isolated synthetic runtime at
  `127.0.0.1:5174`: 2/2 passed in 4.9 seconds. The create/review/readback path persisted exactly
  one entry after a double click and full reload. Blank input stayed disabled. The served Vite
  mount contains the current chronology component and API client.
- Evidence: `docs/engineering/evidence/netpay-candidate-human-follow-up-h1-20261011.txt`.
- No real Rock N' Wok note was created or preloaded. No Gmail provider call, sync, OAuth action,
  manifest change, attachment download, owner link, disposition or next-action mutation occurred.

**IG-009 H1: PASS.** IG-008 Gates A/B/C remain PASS and the Gmail pilot is unchanged. D3 and
D2-Lite remain unauthorized.

**Next operator action:** open `/netpay-inbox/gmail`, select the candidate, use **Seguimiento
humano**, enter the note and optional event date, choose **Revisar nota**, verify the exact text,
then choose **Registrar seguimiento** once and confirm the readback notice and chronology row.

## IG-009 pilot-runtime availability activation — 2026-10-11

- The H1 evidence gate above had passed in the isolated runtime, but the productive local pilot
  runtime had not yet been activated: `5173` served a transformed module without H1, the process at
  `8000` exposed no follow-up path in OpenAPI, and the pilot database was still at `20261008_49`.
  This was a deployment/runtime discrepancy, not a browser-cache assumption.
- Applied the forward-only migration `20261008_49 -> 20261011_50` to the pilot database. Existing
  data was preserved; no downgrade was run. Restarted only `api` and `web`.
- Post-restart, the Vite source endpoint at `5173` contains **Seguimiento humano** and
  `listCandidateFollowUps`; OpenAPI at `8000` exposes
  `/netpay/gmail/candidates/{candidate_id}/follow-ups`; Alembic reports `20261011_50 (head)`.
- Sanitized readback found the existing target candidate, no owner link, an Organization membership
  with Inbox read/manage authority and zero follow-up rows before visual inspection.
- Microsoft Edge inspected the actual `5173` pilot runtime read-only. Selecting the target candidate
  produced GET follow-up HTTP 200 and rendered the H1 heading, note form, optional event date,
  empty chronology fallback and disabled review action for blank input. No form field was changed
  and no mutation control was used.
- Post-inspection readback remains zero follow-up rows and zero follow-up Events; owner and
  disposition remain null. The screenshot is ephemeral under the operating-system temporary
  directory and is not a Git candidate because it contains pilot material.

**Pilot-runtime H1 availability: PASS.** This availability check is separate from the already
completed synthetic H1 conformance gate. No Gmail request, synchronization, manifest change,
attachment access or business mutation occurred.

## Alta MVP assessment and bounded correction — 2026-10-12

- Local readback located one onboarding candidate whose immutable source explicitly requests a
  terminal, e-commerce onboarding and multiple new branches. The extractor already classified it
  as `new_branch`, but its commerce hint incorrectly swallowed the branch list and following prose.
- The only persisted H1 note belongs to a different support candidate. The onboarding candidate
  has zero follow-ups. This discrepancy was recorded rather than treating operator-reported text
  as message evidence.
- Same-tenant read-only lookup found no matching `NetpayServiceCase` or `CommercialIntakeItem`.
  Destination search is wired to tenant-scoped QRY surfaces and correctly returns no selectable
  owner, so Accept/Link remain blocked. No record, link, decision or follow-up was created.
- Added a brand-neutral deterministic rule that recognizes singular/plural branch onboarding,
  separates a repeated merchant prefix from each observed branch, stops before document prose,
  and records the onboarding request as `reported_by_message`.
- After confirming the target had no H1 note, owner, review or immutable disposition, reprocessed
  exactly that candidate from its already-persisted local source and read it back. Counts stayed
  at 10 sources, 10 candidates and 1 follow-up; the source fingerprint was unchanged. Readback now
  contains one unverified observed merchant, four unverified observed branches and the onboarding
  request attributed to the message. State remains `pending_link`; owner and review remain null.
- Added the existing CMD-018 edit surface for request type, priority and next action. It explicitly
  leaves email evidence and H1 notes unchanged. Correcting observed commerce/branch facts and the
  end-to-end promotion workflow remain outside current authority.
- Verification:
  - API synthetic suite with `YARVIS_GMAIL_PROVIDER=fake` and the productive feature flag disabled:
    `14 passed` (one dependency warning). A preceding run was invalid because the productive
    Google configuration was inherited; a concurrent retry then collided on the disposable test
    database. Neither touched the pilot database.
  - Focused Vitest: `8 passed`, including empty same-tenant destination search and blocked
    acceptance.
  - Ruff on classifier and tests: PASS.
  - Vite production build in the web container: PASS, 109 modules.
  - `git diff --check`: PASS (line-ending notices only).
- Prepared non-authoritative review package:
  `NETPAY_ALTA_CANDIDATE_TO_COMMERCIAL_INTAKE_DESIGN.md`, Amendment 022 and IG-010. Proposed IDs
  CMD-038..040, QRY-021 and EVT-028..029 were absent in the 2026-10-12 repository search; they are
  not registered or reserved. IG-010 also defines a separate, still-closed 20-message P2 batch
  that preserves the first manifest.

**Gate status remains unchanged:** IG-008 A/B/C PASS; IG-009 H1 PASS. Amendment 022 and IG-010 are
PROPOSED/NOT RATIFIED, all of their gates are closed. No Gmail call, discovery, synchronization,
attachment access, manifest change or productive business mutation occurred.

**Next reproducible action:** review and, if acceptable, ratify the design, Amendment 022 and
IG-010 by canonical SHA-256. Until then, the operator may use **Guardar corrección** only for the
already-authorized classification/priority/next-action fields and may manually create a standalone
commercial intake in the existing Inbox; the candidate-to-intake trace and subsequent linked
acceptance must wait for H2 authority.

## Alta runtime authorization and five-branch correction — 2026-10-12

- Sanitized API logs identified the reported 403 before case creation:
  `GET /netpay/master?query=...` and `POST /netpay/master/clients` returned 403. These operations
  require `netpay.master.read` and `netpay.master.manage` respectively.
- Persistence readback confirms the pilot principal has one active `netpay_inbox_operator`
  membership in Netpay Gmail Pilot, with exactly `netpay.inbox.read` and
  `netpay.inbox.manage`. Amendment 019 expressly prohibits role-map or Membership mutation in this
  package, and Amendment 020 prohibits Master mutation. No permission or role was changed.
- The correct current destination for an unresolved, not-yet-Master merchant is the existing
  `CommercialIntakeItem` owner surface. Its create command requires `netpay.inbox.manage`, which
  the pilot operator has. A Netpay case is the known-client path and depends on a verified Master
  Client/Company/Branch.
- Updated the Inbox UI to expose **Registrar ingreso comercial** and hide **Nuevo caso Netpay**
  when `netpay.master.manage` is absent, with a visible explanation. This removes the misleading
  route to forbidden Master calls without bypassing backend authorization.
- Local-only source comparison found two separate pilot messages. One requests TPV plus e-commerce
  and names four branches. A distinct reply/source explicitly requests five branches and contains
  the missing Paseo Acoxpa observation plus TPV evidence. Name similarity did not create a
  cross-thread link.
- Added a generic repeated-heading extractor and reprocessed only the second unreviewed,
  unlinked candidate from its immutable local source. Readback contains five separate unverified
  branch facts, request type `new_branch`, product `tpv`, unchanged fingerprint and no owner or
  decision. Counts remain 10 sources, 10 candidates and 1 H1 follow-up.
- Gmail candidate detail now renders **Producto solicitado** with a readable label and explicitly
  marks it as a rules-derived value pending human verification. Branch facts retain source and
  verification labels. Product/branch human correction remains outside CMD-018 and was added to
  proposed Design/Amendment 022/IG-010 together with mixed-product Commercial Intake and
  multi-branch draft preservation.
- Verification:
  - classifier: `6 passed`;
  - focused frontend suites: `17 passed`;
  - Ruff: PASS;
  - real `127.0.0.1:5173` Edge check: initial FAIL because Vite served stale transformed modules
    while mounted source was current; restarted only `web`; repeated read-only test PASS (`1/1`).
    It verified pilot routing, hidden case creation, product labels, four-branch source and the
    separate five-branch source. No controls that mutate business data were used.
- The rejected Master form never persisted its entered values. They existed only in React memory;
  the required web restart could not preserve them. Proposed H2 now requires a reload-safe draft
  transfer to avoid future recapture and forbids collapsing multiple branches into one field.

**Gate status remains unchanged:** IG-008 A/B/C PASS and IG-009 H1 PASS. Amendment 022 and IG-010
remain PROPOSED/NOT RATIFIED. No Gmail call, discovery, sync, attachment download, manifest change,
Master record, Commercial Intake, case, link or decision was created.

## Alta authorized-route closure — 2026-10-12

- The ten files in this bounded block are complete:
  `netpay_gmail_classification.py`, its focused test, Gmail workspace and test, Inbox workspace and
  test, Alta design, Amendment 022, IG-010 and this checkpoint. The wider working tree still
  contains the previously authorized Gmail/H1 implementation and evidence.
- The Inbox-only runtime now presents **Registrar ingreso comercial**, hides **Nuevo caso Netpay**,
  and explains that Commercial Intake is provisional and does not create Master, branch or case
  records. The creation form uses only `/netpay/inbox/contacts`.
- Candidate selection is stored in the URL as an opaque candidate ID and restored after reload.
  Form errors preserve the local Commercial Intake draft and show a visible alert. No draft is
  persisted until the operator explicitly submits it.
- Isolated backend proof for the existing Commercial Intake contract passed: create, identical
  replay, query/readback, tenant isolation and downstream lifecycle (`1 passed`). This used only
  synthetic test data and the disposable test database.
- Focused UI suites passed `19/19`, including pilot permission routing, no Master client call from
  the intake form, safe-error draft preservation and candidate reload. Classifier remains `6/6`;
  Ruff remains PASS.
- Runtime verification examined Vite process PID 29, the `/app` mounts and transformed HTTP
  modules. A first Edge attempt after the later selection changes correctly failed because Vite
  again served a stale transform. Restarted only `web`, proved both current module markers over
  HTTP, then reran the read-only Edge scenario: `1/1 PASS`.
- The final 5173 scenario showed product and five individual branch facts, reloaded the selected
  candidate from its URL, opened the correct Commercial Intake form, confirmed the explanatory
  boundary, and observed zero `/netpay/master` requests. It did not submit the form.
- Final Vite build: PASS, 109 modules. `git diff --check`: PASS (line-ending notices only).
- New proposal hashes after adding product correction, five separate branches, mixed product,
  cross-thread human review and reload-safe draft requirements:
  - Design: `dc225686f5150e379363ffd4ca6e4207f138dad94609b0eb03456cec72d71a72`;
  - Amendment 022: `c72a52438e099854dcc6c350f31fc6ac0ad87bed4d2ac18635e64e18a37519e9`;
  - IG-010: `75d120805325761faaa682c1c8e81acac6eaf65ddf6ddb3754ecff8732b99ee7`.

**Operational limit:** the current contract can manually create a standalone intake with one
`product_interest` value and a free-text summary. It cannot yet preserve a candidate trace,
represent mixed TPV/e-commerce as a closed value, store five proposed branches as separate
structured rows, correct those observations with append-only human provenance, or confirm the
relationship between the separate four-branch and five-branch messages. Those capabilities remain
only in the unratified H2 proposal.

**Gate status remains unchanged:** IG-008 A/B/C PASS and IG-009 H1 PASS. Amendment 022/IG-010 and
all H2/P2 work remain PROPOSED/closed. No productive Gmail, Master, Commercial Intake, case, link,
decision or manifest mutation occurred.
## 2026-10-12 — alta request presentation, local attachments and dossier proposal

- No Gmail request, synchronization, manifest change or attachment download/content access was
  performed. The work used the two persisted onboarding sources only.
- Local attachment inventory: the initial Lipablo source has one PDF metadata row; the five-branch
  reply has ten metadata rows (nine PDF, one PPTX). The UI now displays filename, MIME type, byte
  size and source subject. Filename-based document types are explicitly marked as unverified
  suggestions and never as valid or complete documents.
- `netpay_checklist_templates` readback returned zero rows. The existing checklist shape is
  versioned and case-bound, but the pilot has no approved template content/version to reuse for a
  pre-case dossier. Amendment 022/IG-010 now carry that gap and keep attachment-content reading in
  a separate closed subgate.
- UI presentation now separates `Solicitud recibida` from `Siguiente acción`; both the readback and
  correction action use responsive multiline textareas. Correction, follow-up and final review are
  normal document sections; the final review no longer uses a sticky overlay. Priority and other
  candidate values were not changed.
- Through ratified `IC-NETPAY-CMD-037`, one append-only `operator_reported` follow-up was recorded
  for candidate `8559d6b7-01e6-4dcf-98c2-fe508919b938`: Lipablo is reported as the legal entity,
  Alfredo Cole as its representative, and both as the same client for this request. The note has no
  event date and explicitly does not confirm or presume legal authority. Readback ID:
  `9d2bef30-c8db-4379-a21c-0813febeec9c`. Candidate remains `normal` / `pending_link`, with no owner
  or human disposition; source fingerprint and ten attachment metadata rows remain present.
- Focused Vitest: `9 passed`. Vite production build passed inside the mounted `web` service. The
  first host build attempts were environmental (`npm.ps1` execution policy, then Windows EPERM on
  the mounted output directory); no product assertion failed.
- Port 5173 initially served the prior transformed module. Only `web` was restarted; HTTP readback
  of the transformed module then contained `Solicitud recibida` and the unverified-attachment UI.
  No browser interaction or business mutation accompanied this availability check.
- Proposed IDs CMD-041/042, QRY-022 and EVT-030 were repository-checked as free. Amendment 022 and
  IG-010 remain **PROPOSED / NOT RATIFIED**. Gates A/B/C and IG-009 H1 remain PASS in their prior
  bounded scope.
- Resume: review the updated proposed package and hashes. Do not implement the dossier or expand
  the Gmail pilot until ratification. `AUDIT_REPORT.md` remained untouched and unopened.
## 2026-10-13 — Amendment 022 ratification and H2-Q implementation checkpoint

- Canonical pre-ratification hashes were verified exactly: Design `cf3038b...615383`, Amendment 022
  `b511b2fa...13bd7`, IG-010 `5f4249a4...1c4893`. Ratification is recorded in all three documents.
- IDs CMD-038..042, QRY-021..022 and EVT-028..030 were free before allocation. H2-Q contracts
  CMD-038, QRY-021 and EVT-028 are registered; H2-I CMD-039/040 and EVT-029 are registered but remain
  conditional until H2-Q evidence passes. H2-D IDs remain unregistered and closed.
- Alembic had one head/current `20261011_50`. Existing revision `20261012_51` retains that parent;
  no duplicate revision was created.
- Isolated database `yarvis_h2q_test` completed upgrade-to-head, downgrade to `20261011_50`,
  re-upgrade and current=`20261012_51`. The pilot database was not used for the round-trip.
- H2-Q code now has tenant-scoped append-only revisions, per-field provenance/verification,
  separate product/branch values, receipts, safe event, readback and Commercial Intake preview.
  Focused behavior tests and 5173 availability remain pending. H2-Q is **NOT YET PASS**; H2-I is
  still closed. No Gmail call or pilot business mutation occurred.

## 2026-10-13 — H2-Q and H2-I evidence closure

- H2-Q synthetic PostgreSQL test passed: append-only structured revision, per-field provenance and
  verification, two distinct branches, mixed products, exact replay, changed-payload conflict,
  foreign-tenant 404, readback, preview and unchanged candidate decision/source fields.
- H1/H2-Q focused backend: `2 passed`; canonical contract suite: `8 passed`; Ruff: passed. Contract
  catalog contains 152 unique IDs with CMD-038..040, QRY-021 and EVT-028..029.
- H2-I in the same isolated test created exactly one synthetic Commercial Intake and trace;
  idempotent replay returned the same result and retained two branch drafts. It created no Master or
  case and did not dispose the candidate. No Lipablo/Gong Cha qualification or intake was created.
- Frontend suite: `10 passed`, including overlay review and the mandatory preview before the confirm
  action. Vite build passed. After API/web restart, OpenAPI on 8000 exposed qualification, preview
  and promotion routes; the transformed module served by 5173 exposed overlay and preview controls.
- Pilot readback after migration showed zero qualifications, zero promotion traces and zero
  Commercial Intake rows. Migration 51 is forward-applied; existing Gmail sources/H1 notes and
  decisions were preserved. H2-Q **PASS** and H2-I **PASS**. H2-D, attachment content/OCR and P2
  remain closed. Next operator action is to select the real candidate, review the overlay, save it,
  inspect the generated intake preview and decide whether to confirm creation.

## 2026-10-13 — global navigation simplification

- The global header now exposes `Operación Netpay` (`/netpay-inbox`), `Solicitudes Gmail`
  (`/netpay-inbox/gmail`) and `Datos Netpay` (`/netpay-data`) as its three primary destinations.
  Every prior global destination remains available under the single keyboard-operable `Más` menu;
  Mission Control moved from `/` to `/mission-control` without removing its functionality.
- `/` redirects to `/netpay-inbox`, and `NavLink` marks the active primary or secondary route. The
  change is in the shared `Layout`, so it applies to every screen that uses the global header.
- Focused Vitest for the global app and Gmail workspace: `16/16 PASS`. Vite production build:
  `PASS` (109 modules). These checks preceded the runtime verification and remained valid because
  the only later application action was restarting `web`; subsequent edits affected only the E2E.
- The first HTTP read showed the prior Vite transform. Only `web` was restarted. Readback of
  `http://127.0.0.1:5173/src/App.tsx` then returned HTTP 200 with the three routes, `global-nav-more`,
  `/mission-control` and the root redirect.
- The integrated browser was unavailable, so the required real-browser check used Playwright CLI
  with installed Microsoft Edge (`D1_BROWSER_CHANNEL=msedge`) against the actual port 5173 runtime:
  `npm.cmd exec playwright test e2e/global-navigation.spec.ts -- --workers=1` with
  `D1_BROWSER_BASE_URL=http://127.0.0.1:5173`. Final result: `1/1 PASS` in 3.4 seconds.
- The Edge scenario proved the initial redirect, all three visible primary links, Gmail access in
  one click, active styling, keyboard opening of `Más`, Mission Control at its preserved route, and
  both menu and document width within the viewport. It performed navigation and inspection only.
  No Gmail request, synchronization, creation, edit, acceptance, link, permission or business-data
  mutation occurred.
- Initial URL for the pilot is `http://127.0.0.1:5173/`; a normal reload now lands on Operación
  Netpay. Gates A/B/C, H1, H2-Q and H2-I remain PASS in their prior bounded scopes. H2-D,
  attachment content/OCR and P2 remain closed.

## 2026-10-13 — promoted Commercial Intake readback and decision UI

- Read-only pilot-database readback found exactly one candidate-to-intake promotion trace. It uses
  qualification sequence 4 (`operator_reported`), preserves both reviewed products (`tpv` and
  `ecommerce`) and five separate branch drafts. The resulting Commercial Intake is `new`.
- Promotion did not decide the candidate: it remains `pending_link`, mutable, without `owner_type`,
  `owner_id`, `reviewed_at` or terminal disposition. Its stored next action remains unchanged.
  This distinction is now explicit in the UI as calculated `Paso del flujo` versus
  `Siguiente acción guardada por el operador`.
- The existing H2-Q preview query now reads back its same-tenant promotion trace and Commercial
  Intake when present. No canonical contract ID, permission, terminal state or command semantics
  changed. The UI restores the latest qualification, shows the existing intake with a link to its
  detail, and offers a local-only `Seleccionar este ingreso como destino` action. Acceptance or
  linking still requires a separate explicit operator action.
- Qualification and candidate-edit controls are grouped under `Revisar y corregir datos`;
  `Revisión humana` is now `Decidir sobre la solicitud`. `Seguimiento humano` remains an independent
  append-only chronology.
- Focused backend H2-Q/H2-I test: `1 passed`. Focused Gmail workspace Vitest: `11 passed`. Ruff:
  PASS. Vite build: PASS (109 modules). The runtime module and OpenAPI route both returned HTTP 200
  after restarting only `api` and `web`.
- Real runtime verification used Playwright CLI with installed Microsoft Edge on port 5173 and the
  provisioned pilot subject supplied through `D1_BROWSER_SUBJECT`. The read-only/local-selection
  scenario passed `1/1` in 8.3 seconds. It observed no POST, PUT, PATCH or DELETE request.
- Post-browser SQL readback remained `trace_count=1`, `intake_count=1`, candidate `pending_link`,
  no owner, no review timestamp, and mutable. No Gmail call, synchronization, new intake,
  acceptance, link or other business mutation occurred.
- Gates A/B/C, H1, H2-Q and H2-I remain PASS within their existing scope. H2-D, attachment
  content/OCR and P2 remain closed.

## 2026-10-14 — terminal acceptance readback and presentation evidence

- Read-only PostgreSQL readback confirmed the operator decision: candidate state `accepted`,
  `owner_type=commercial_intake`, non-null `reviewed_at` and `immutable=true`. The owner ID equals
  the Commercial Intake ID stored by the existing promotion trace.
- Cardinality remained stable: one promoted intake, one candidate-to-intake trace, one promotion
  event and one candidate-review event. Qualification sequence 4 still contains two products and
  five distinct branches; the append-only H1 chronology still contains one note.
- The UI now renders a terminal `Resultado registrado` panel with result, accepted destination,
  decision date and a link to the Commercial Intake detail. Acceptance, rejection, duplicate,
  link, candidate correction and additional intake preparation controls are disabled where they
  conflict with the immutable disposition. No terminal state or contract behavior changed.
- Destination presentation uses the readable record name, a bounded summary and a collapsible full
  detail. Wrapping and width constraints prevent the destination from expanding the page
  horizontally.
- Focused Gmail workspace Vitest: `12/12 PASS`. Vite/TypeScript build: PASS (109 modules). Only
  `web` was restarted. HTTP readback of the transformed module on port 5173 returned 200 with the
  terminal-result, immutable-state and destination-detail markers.
- Real Microsoft Edge verification against `http://127.0.0.1:5173` passed `1/1` in 12.5 seconds.
  It verified accepted state and date, exact destination link, all incompatible decision buttons
  disabled, readable/collapsible destination, viewport width, and persistence after a full reload.
  The request observer recorded zero POST, PUT, PATCH or DELETE calls.
- Post-E2E SQL readback reproduced the same state and all counts above. No Gmail request,
  synchronization, acceptance replay, link, rejection, edit or other business mutation occurred.
  Gates A/B/C, H1, H2-Q and H2-I remain PASS. H2-D, attachment content/OCR and P2 remain closed.

## 2026-10-14 — H2-D catalog approval and migration checkpoint

- The exact approved catalog bytes were verified before registration: SHA-256
  `4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b` matched. Guillermo De
  Hoyos is recorded as the named operational owner for this pilot; the record explicitly does not
  claim corporate Netpay approval. Catalog v1.0.0 is effective from 2026-10-14 for persona física
  and persona moral, TPV/e-commerce/mixed with physical locations. E-commerce without a physical
  establishment remains excluded.
- H2-I was already PASS. Fresh repository search found CMD-041, CMD-042, QRY-022 and EVT-030 free
  outside the ratified proposal, and they are now registered for the H2-D implementation.
- The real promotion trace was read only before implementation: the terminal accepted candidate
  still points to one Commercial Intake, with products `tpv` and `ecommerce` and five distinct
  branch drafts. No dossier was created and no candidate/source/H1/decision value changed.
- Alembic had the single head/current `20261012_51`. Existing migration `20261014_52` keeps that
  parent and is now the sole head. An isolated `yarvis_h2d_test` database completed full upgrade,
  downgrade to `20261012_51`, re-upgrade and current=`20261014_52`. The pilot database has not yet
  received migration 52.
- Backend implementation is in progress: immutable dossier snapshot, metadata-only shared evidence
  references, append-only requirement reviews, derived blockers/completeness and tenant-scoped
  endpoints exist but tests and UI are still pending. H2-D is **NOT PASS**. Attachment content/OCR,
  Drive and P2 remain closed.

**Resume:** finish backend conformance, then apply only the forward migration to the pilot, finish
the confirmation/readback UI, run frontend/build and verify the non-mutating pre-creation view on
the actual 5173 runtime. Do not create the real dossier during verification.

## 2026-10-14 — H2-D conformance closure

- Catalog SHA-256 remained `4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b`.
  Its approved canonical JSON bytes were not changed.
- The isolated `yarvis_h2d_test` database completed full upgrade, downgrade to `20261012_51`,
  re-upgrade and `current=20261014_52`. The pilot received only the forward upgrade from
  `20261012_51` to the sole head `20261014_52`.
- Backend H2-D conformance passed (`1 passed`); the combined affected Gmail/canonical-contract
  selection passed (`3 passed`). Ruff and compileall passed. The test proves preview, immutable
  catalog snapshot, replay/conflict, isolation before replay, all six states, append-only storage,
  history/readback, 60-day rules, holder correspondence, four photos per branch, shared metadata
  evidence, reusable manager contact references, blockers/completeness and preservation of source,
  H1 notes and terminal candidate decision.
- The Gmail workspace suite passed `13/13`; Compose Vite build passed with 109 modules. Microsoft
  Edge on the actual 5173 runtime passed `1/1` after a full reload and observed zero business
  mutation requests. The real preview showed catalog v1.0.0, two products, five branches and 24
  pending requirements. The create button remained disabled without explicit confirmation.
- Final readback remained `dossiers=0`, `reviews=0`, `evidence=0`; the real candidate stayed
  accepted/immutable and associated to the same one promotion trace. Four qualification overlays,
  one H1 note, two products and five branches remain intact.
- Evidence: `docs/engineering/evidence/netpay-h2d-conformance-20261014.txt`.

**Gate:** H2-D **PASS** within the approved physical-location catalog. Attachment content/OCR,
Drive and P2 remain closed. No Gmail call, synchronization, download, real dossier creation or
document validation occurred.

**Next action:** open the accepted candidate in `/netpay-inbox/gmail`, review the H2-D preview,
expand its requirements, then use the explicit confirmation checkbox and `Crear expediente de alta`
only when ready to create the real dossier.
