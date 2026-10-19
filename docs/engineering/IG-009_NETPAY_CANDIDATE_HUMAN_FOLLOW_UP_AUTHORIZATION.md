# IG-009 — Netpay Candidate Human Follow-up Implementation Authorization

**Status: RATIFIED — H1 PASS — IMPLEMENTED AND EVIDENCED**

**Ratified 2026-10-11 against proposal SHA-256:**
`021b1ed8545f57374c9b9cf85dd5eace8537630d239d37509b654416a15eebd5`.

## 1. Candidate package

| Field | Proposed value |
| --- | --- |
| Amendment | Proposed Amendment 021 |
| Design | `NETPAY_CANDIDATE_HUMAN_FOLLOW_UP_DESIGN.md` |
| Branch | `feat/netpay-gmail-intake-sentinel` |
| Verified base at preparation | `b6bc5930ae8b608ff55aa9849e995cb7639966d7` |
| Owner | Netpay Merchant Operations |
| Existing gate state | IG-008 A/B/C PASS |
| Gmail boundary | Existing approved ten-message pilot only; no provider call in this package |

## 2. Entry conditions

Implementation may begin only after:

1. Amendment 021 and IG-009 are separately and explicitly ratified by canonical
   document hash;
2. worktree/base and unrelated changes are reviewed;
3. the canonical contract catalog confirms CMD-037, QRY-020 and EVT-027 remain
   free and registers only the accepted contracts;
4. the current Alembic graph is recomputed; and
5. the implementation plan contains no Gmail, owner creation/linking, D3 or
   D2-Lite work.

## 3. Authorized implementation after ratification

Only the model/migration, command, query, safe Event, minimum chronology UI and
tests defined in the design are authorized. Use existing Inbox read/manage
permissions. Do not introduce a new role, background execution or external
integration.

## 4. Evidence gate H1

Gate H1 passes only with:

- actual pre/post Alembic heads and upgrade/downgrade/upgrade proof;
- synthetic unlinked-candidate meeting/call/agreement/pending examples;
- null and supplied event-date coverage;
- same-key replay and changed-payload conflict proof;
- same-Organization and cross-Organization command/query proof;
- one row/one Event fresh-session readback;
- immutable source, candidate extraction, owner and disposition comparison;
- Event/log scan proving no note or Gmail content leakage;
- component tests and a real-browser create/reload chronology scenario;
- relevant backend regression, frontend build and static checks; and
- a safe evidence file containing counts and synthetic identifiers only.

No real client note is required for H1. Synthetic fixtures should model the
shape of the Rock N' Wok follow-up without copying real content or identifiers.

## 5. Stop conditions

Stop without migration or implementation expansion if identifiers collide, the
Alembic graph differs from the documented value without reconciliation,
authority cannot be resolved, a cross-tenant observation occurs, note text
would enter Events/logs, source or decisions would mutate, or an owner/Gmail/
automation dependency appears.

## 6. Required closure record

Record accepted document hashes, base/branch, contracts registered, migration
parent and heads, exact commands, test counts/durations, browser/readback
results, negative mutation/leakage checks, modified/new files, diff/status and
the explicit continued exclusion of Gmail expansion, D3 and D2-Lite.

## 7. Proposed authorization statement

`RATIFY IG-009 — NETPAY CANDIDATE HUMAN FOLLOW-UP H1 IMPLEMENTATION AUTHORIZED UNDER AMENDMENT 021. IG-008 GATES A/B/C REMAIN PASS. GMAIL PILOT SCOPE IS UNCHANGED. D3 AND D2-LITE REMAIN UNAUTHORIZED.`

Until that statement is accepted against canonical hashes, this gate remains
closed and no implementation is authorized.
