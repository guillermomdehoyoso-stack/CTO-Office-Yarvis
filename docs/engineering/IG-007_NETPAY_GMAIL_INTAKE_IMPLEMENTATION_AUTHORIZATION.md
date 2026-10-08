# IG-007 — Netpay Gmail Intake implementation authorization

## Status

**RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2**

This is the companion gate for
`IMPLEMENTATION_ROADMAP_AMENDMENT_019.md`. The bounded synthetic/local D1
source slice is implemented and evidenced in this branch. Productive OAuth,
credential access, real Gmail access, scheduler, Pub/Sub and deployment remain
outside the execution. **GMAIL INTAKE D3 — NOT AUTHORIZED.**

## 1. Candidate package

| Field | Value |
| --- | --- |
| Branch | `feat/netpay-gmail-intake-sentinel` |
| Base | `f71780d161502fef0709759118b381d583d6afd2` |
| Capability | Netpay Gmail Intake, D1 source/manual sync and D2 candidate/human acceptance |
| Owner | Netpay Merchant Operations |
| Design authority | Amendments 014, 018 and ratified 019 |
| Contract allocation | Existing planned `CMD-016..018`, `QRY-007..008`, `EVT-007/008/010`; ratified next-free D1/D2 IDs in Amendment 019 |
| Current status | D1 source slice implemented; Evidence Gate passed for synthetic/local D1; D2 conditional |

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

The implemented D1 gate authorizes only a fake/local provider first. A
separately approved productive Gmail adapter may follow. D1 includes explicit mailbox
binding, `gmail.readonly`, manual synchronization, a maximum 30-day initial
backfill, source-item dedupe, cursor-after-commit, bounded sanitized content,
safe status/readback and negative mutation tests.

The implemented slice does not create candidates, Commercial Intake items, NetpayServiceCases,
Master records or external actions. It may not start polling, a scheduler,
worker, queue, Pub/Sub, webhook or Gmail `watch`.

### Phase D2 — candidate extraction and human acceptance

After the accepted D1 synthetic evidence, a separate D2 decision may authorize the candidate model,
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

## 4. Evidence Gate for the D1 package

The D1 review verified the D1 source checklist,
including tenant isolation, exact 30-day bound, label fail-closed behavior,
message/thread replay, partial failure, classification determinism and AI
separation, aging/priority/owner/next-action ordering, concurrent human
acceptance, owner idempotency, readback/reload, migration round-trip, frontend
typecheck/build, static checks and browser E2E using only synthetic fixtures.

The evidence must prove that no email was sent or modified and that no case or
Commercial Intake item was created automatically. The reproducible record is
`docs/engineering/evidence/netpay-gmail-d1-conformance-20261008.txt`.

## 5. Rollback

Rollback disables the fake/local source and candidate routes, preserves safe
synthetic evidence, reverts only the future migration within its approved
lineage, and leaves existing Inbox/Commercial Intake/Case behavior unchanged.
Productive OAuth disconnect/revocation is a separate operational act and is not
performed by this draft.

## 6. Decision requested

`RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2`: the synthetic/local
D1 source slice is implemented and its Evidence Gate is passed. D2 remains
conditional and is not implemented. Ratification is not Gmail access, OAuth
consent, credential creation, productive implementation or D3 authorization.
D2-Lite remains a separate decision.
