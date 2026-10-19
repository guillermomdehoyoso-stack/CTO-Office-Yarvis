# IG-008 — Netpay Gmail restricted productive pilot and D2 authorization

## Status

**RATIFIED — GATES A/B/C PASS RECORDED — LOCAL UNCOMMITTED EVIDENCE**

This is the ratified implementation gate companion to
`IMPLEMENTATION_ROADMAP_AMENDMENT_020.md`. Gate A authorizes only offline
implementation and conformance using synthetic fixtures and fake Google HTTP
responses. B/C were closed at initial ratification; the subsequent closures
below supersede that initial phase status without expanding the pilot.

## Documentary reconciliation — 2026-10-15

- Gate A: historical PASS on 2026-10-09 in
  [offline conformance](evidence/netpay-gmail-gate-a-conformance-20261009.txt).
- Gate B: historical PASS in the 2026-10-10 acceptance section of
  [preflight/manifest evidence](evidence/netpay-gmail-gate-b-preflight-20261009.txt).
- Gate C: historical PASS in the 2026-10-11 controlled-retry closure of
  [restricted-pilot evidence](evidence/netpay-gmail-gate-c-pilot-20261010.txt).
  Earlier PENDING entries in the same record remain historical.

HEAD `b6bc5930ae8b608ff55aa9849e995cb7639966d7` contains D1;
this gate, the later evidence and D2 implementation are local and uncommitted.
The ten-source/ten-candidate result is historical, not a current pilot query.
No test was rerun, no new PASS declared and no operational action performed.
Current runtime, full-tree regression and the publication record requested in
section 7 remain **TO BE VERIFIED**. Remote HEAD is **UNKNOWN** after the
2026-10-15 read-only query failed; no integration was attempted.

The unchanged boundary is the approved ten-message pilot. This reconciliation
does not authorize another sync, OAuth, Gmail access, D3, D2-Lite, P2,
attachment content/OCR, Drive, Gmail mutation or publication.
Sections 4 and 9 retain the original sequential conditions; section 10 is the
initial ratification record, not the current phase summary.

## 1. Candidate package

| Field | Value |
| --- | --- |
| Branch | `feat/netpay-gmail-intake-sentinel` |
| Base | `b6bc5930ae8b608ff55aa9849e995cb7639966d7` |
| Owner | Netpay Merchant Operations |
| D1 prerequisite | Passed for synthetic/local source slice |
| Capability | Read-only productive Gmail adapter, restricted real pilot, D2 candidate analysis and human review UI |
| Organization | `59650e6f-ad62-40c3-8cb0-7710a122ce8b` |
| Initial window | Maximum 30 days |
| Provider scope | `https://www.googleapis.com/auth/gmail.readonly` only |
| Trigger | Manual human action only |
| D3 | Not authorized |

## 2. Entry conditions

Implementation may start only after:

1. Amendment 020 and this gate are explicitly ratified;
2. the worktree still descends from the stated base without unrelated tracked
   changes;
3. the actual Alembic graph is verified;
4. current canonical Principal, Membership and Organization evidence passes;
5. the D1 synthetic evidence remains accepted; and
6. the exact Authorized File Boundary in Amendment 020 §11 is accepted.

No Google access may occur during implementation Gate A.

## 3. Authorized implementation

After ratification, Gate A authorizes:

- the official Gmail read-only adapter and fake transport tests;
- local loopback OAuth with PKCE/state protection;
- the AES-256-GCM file secret-store adapter and opaque database references;
- D2 candidate persistence, deterministic classification and extraction;
- exact-ID correlation across threads;
- pending-link, contradiction, aging, priority, responsible and next-action
  suggestions;
- human review/link disposition through existing owner contracts;
- the minimum Gmail section inside `NetpayInboxWorkspace`; and
- the tests, migration and evidence needed to reach Gate B.

An external AI provider, automatic case creation, Master mutation and Gmail
mutation are not authorized.

## 4. Phased gate execution

### A. Offline implementation and conformance

Use only synthetic fixtures and fake Google HTTP responses. Complete all Gate A
criteria from Amendment 020 §12. Do not configure a client ID, secret, token,
mailbox or Google project in the runtime.

### B. Operator Google configuration

After Gate A is accepted, the operator performs these external actions:

1. inspect the existing Yarvis Google Cloud project and record only the
   non-secret facts required by Amendment 020 §4;
2. reuse it only if ownership, consent isolation and separate-client controls
   pass; otherwise create the dedicated `yarvis-netpay-intake` project;
3. enable Gmail API;
4. configure the consent audience for the authorized account only and record
   whether it is Internal or External Testing, including any required Workspace
   Admin trust and the applicable restricted-scope verification exception;
5. create one OAuth client with callback
   `http://127.0.0.1:8000/netpay/gmail/oauth/callback`;
6. make the exact scope
   `https://www.googleapis.com/auth/gmail.readonly` available;
7. place client ID and client secret in the named host secret files, never in
   chat, Git, Compose values or shell command arguments;
8. generate the AES-256-GCM token-store key directly into its host secret file;
9. start Yarvis with the exact non-secret configuration from Amendment 020 §5;
10. connect and validate the mailbox and exact label; and
11. approve the resulting 10-message HMAC manifest before content ingestion.

The operator must not provide any secret to an agent or repository file.

### C. Restricted pilot

Run one manual sync over the approved manifest. Review at least one candidate
in Yarvis, reload the application and perform a fresh database-session
readback. Repeat the same manual request to prove idempotency. Record only safe
evidence.

## 5. Acceptance criteria

The package passes only if:

1. connection status, last run and controlled errors are visible;
2. the first read is bounded to the approved 30-day/label/manifest boundary;
3. a retry does not duplicate source items, candidates, owner links or Events;
4. partial failure preserves the last accepted cursor;
5. tenant isolation and use-time authority are enforced before receipt replay;
6. real Gmail IDs/thread IDs remain traceable through protected source records;
7. D2 extracts ticket/case, request type, verifiable commerce/branch IDs,
   terminal/serial, carrier/tracking/reported state, pending data and next
   action when present;
8. cross-thread correlation uses verifiable identifiers and uncertain matches
   remain `pending_link`;
9. facts, inferences and contradictions remain separately reviewable;
10. a human disposition calls existing owner contracts at most once;
11. browser reload and database-session readback reproduce the accepted state;
12. no send, draft, modify, label, archive, delete, watch, scheduler, worker,
    Pub/Sub or webhook path exists;
13. no secret or real mailbox content appears in Git, logs, Events, fixtures,
    screenshots or evidence files; and
14. the required backend, frontend, browser, migration and static checks pass.

## 6. Stop conditions

Stop provider access immediately on revoked/expired credentials, mailbox or
label mismatch, Membership loss, Organization ambiguity, manifest mismatch,
cross-tenant observation, retention failure, unexpected scope, secret leakage
or any attempted Gmail mutation.

A failed Gate A keeps Google/OAuth closed. A failed Gate B prevents message
content access. A failed Gate C means the intake is not operational and no
continuation is authorized.

## 7. Evidence record

The closure record must contain:

- accepted amendment/gate commit hashes;
- actual Alembic heads and migration round-trip;
- exact non-secret configuration and project reuse disposition;
- dependency versions and reproducible commands;
- offline Gate A results;
- safe Gate B connection/manifest result;
- safe real-pilot counts and durations;
- one real source-to-candidate-to-review-to-readback trace using only local
  opaque IDs/HMACs;
- idempotent retry result;
- mutation-negative evidence;
- modified/new files, `git status --short` and diff stat; and
- explicit D3/D2-Lite exclusion.

## 8. Rollback

Disable the feature flag, revoke the Google grant, delete the encrypted token
through the store, preserve safe evidence and existing owner records, and
verify unrelated Inbox behavior. No destructive owner rollback is permitted.

## 9. Historical ratification decision

The exact approval decision is:

`RATIFIED — NETPAY GMAIL RESTRICTED PRODUCTIVE PILOT AND D2 AUTHORIZED`

The decision activates Gate A only. Google intervention starts after Gate A
evidence is accepted; content ingestion starts after Gate B and manifest
acceptance. D3, D2-Lite, scheduling, Pub/Sub and all Gmail mutation remain
unauthorized.

## 10. Initial ratification record — 2026-10-08

| Field | Accepted value |
| --- | --- |
| Decision | `RATIFIED — NETPAY GMAIL RESTRICTED PRODUCTIVE PILOT AND D2 AUTHORIZED` |
| Authority | User-confirmed Architecture Authority |
| Decision date | `2026-10-08 America/Mexico_City` |
| Accepted Amendment 020 SHA-256 | `3f407daf60f780ea8e12c836b631952d067a476f019d0fa47c2af138248a4936` |
| Accepted IG-008 SHA-256 | `e3810e4f5a0b02b5059b923be4356b78bc53b4e08028de668bc934931cf15b43` |
| Active phase | Gate A offline implementation and conformance |
| Closed phases | Gate B Google/OAuth/manifest and Gate C restricted real pilot |

The hashes were recomputed and matched before this ratification record was
written. This record changes the document bytes but preserves the hashes of the
accepted proposal versions.
