# IG-007 — Netpay Gmail Intake implementation authorization

## Status

**RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2**

This is the companion gate for
`IMPLEMENTATION_ROADMAP_AMENDMENT_019.md`. It is governance documentation
only in this execution. The ratified future gate may authorize the bounded
synthetic/local D1 package and D2 after its Evidence Gate; this execution
performs no code, migration, OAuth, credential, Gmail access, backfill,
synchronization, scheduler, Pub/Sub or deployment. **GMAIL INTAKE D3 — NOT
AUTHORIZED.**

## 1. Candidate package

| Field | Value |
| --- | --- |
| Branch | `feat/netpay-gmail-intake-sentinel` |
| Base | `f71780d161502fef0709759118b381d583d6afd2` |
| Capability | Netpay Gmail Intake, D1 source/manual sync and D2 candidate/human acceptance |
| Owner | Netpay Merchant Operations |
| Design authority | Amendments 014, 018 and ratified 019 |
| Contract allocation | Existing planned `CMD-016..018`, `QRY-007..008`, `EVT-007/008/010`; ratified next-free D1/D2 IDs in Amendment 019 |
| Current status | D1 next active package; D2 conditional on D1 Evidence Gate; runtime not implemented |

## 2. Preconditions before any implementation

No phase may start until all applicable evidence is accepted:

1. Amendment 019 is ratified by the Architecture Authority.
2. The canonical contract procedure has registered the exact IDs and metadata;
   registration does not make unimplemented IDs dispatchable.
3. Canonical Organization, Principal and Membership evidence is current and
   no Gmail role is inferred from a human name or email address.
4. Privacy/retention design accepts the body, excerpt, header and attachment
   boundaries; no legal hold or purge mechanism is implied here.
5. Secrets governance accepts an encrypted credential reference and revocation
   lifecycle.
6. The fake/local Evidence Gate is approved with the exact Amendment 019
   allowlist and synthetic fixtures.
7. Productive OAuth, Google project/consent, and real-pilot gates remain closed
   until separately accepted.

## 3. Phase authorization

### Phase D1 — source connector and manual sync

The future gate may authorize only a fake/local provider first, followed by a
separately approved productive Gmail adapter. It may include explicit mailbox
binding, `gmail.readonly`, manual synchronization, a maximum 30-day initial
backfill, source-item dedupe, cursor-after-commit, bounded sanitized content,
safe status/readback and negative mutation tests.

It may not create candidates, Commercial Intake items, NetpayServiceCases,
Master records or external actions. It may not start polling, a scheduler,
worker, queue, Pub/Sub, webhook or Gmail `watch`.

### Phase D2 — candidate extraction and human acceptance

After D1 synthetic evidence, the future gate may authorize the candidate model,
deterministic classification, optional fake/versioned AI suggestion, aging,
priority, suggested responsible, next action, pending/overdue read models,
human review, acceptance/rejection/duplicate/link commands, non-sent reply
drafts, and the existing `/netpay/inbox` presentation.

Only the authorized human path may call existing Commercial Intake or Inbox
owner contracts. Automatic case creation, Master mutation and Gmail mutation
remain prohibited.

### D3 and later — not authorized

Scheduler runtime, automatic polling, worker/lease infrastructure, Pub/Sub,
webhooks, Gmail `watch`, attachment downloads, autonomous follow-up, email
send/reply, Cloud Run and real pilot are deferred to separate gates.

### Migration lineage

No migration revision is reserved by IG-007. The reviewed repository has four
current Alembic heads: `20260712_04`, `20260802_25`, `20260802_26` and
`20260823_47`. Any future persistence work must resolve the actual heads at
implementation time, use one valid `down_revision` (or an explicit merge
revision for multiple heads), and prove `upgrade -> downgrade -> upgrade`.
The provisional `20261009_48` identifier and `20260823_47` parent are not
ratified by this gate.

## 4. Evidence Gate for the future package

The implementation review must verify the complete Amendment 019 checklist,
including tenant isolation, exact 30-day bound, label fail-closed behavior,
message/thread replay, partial failure, classification determinism and AI
separation, aging/priority/owner/next-action ordering, concurrent human
acceptance, owner idempotency, readback/reload, migration round-trip, frontend
typecheck/build, static checks and browser E2E using only synthetic fixtures.

The evidence must prove that no email was sent or modified and that no case or
Commercial Intake item was created automatically.

## 5. Rollback

Rollback disables the fake/local source and candidate routes, preserves safe
synthetic evidence, reverts only the future migration within its approved
lineage, and leaves existing Inbox/Commercial Intake/Case behavior unchanged.
Productive OAuth disconnect/revocation is a separate operational act and is not
performed by this draft.

## 6. Decision requested

`RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2`: the future
bounded mandate is open for synthetic/local D1, with D2 conditional on the D1
Evidence Gate. Ratification is not Gmail access, OAuth consent, credential
creation, productive implementation or D3 authorization. D2-Lite remains a
separate decision.
