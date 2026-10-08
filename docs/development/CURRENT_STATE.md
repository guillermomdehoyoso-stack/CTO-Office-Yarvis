# Current Engineering State

## Gmail Intake governance overlay — 2026-10-08

This dated overlay records the ratified Amendment 019 and IG-007 position
without rewriting historical statements below. It supersedes only their
current-state, current-gate, current-work-package, and next-action readings.
Historical evidence remains immutable.

| Field | Reconciled current value |
| --- | --- |
| F-011 status | **Implemented / closed:** F-011 Stage I records F-011 COMPLETE — VALIDATED. IG-006 is retained as the historical authorization that opened the bounded work. |
| Implemented Netpay reality | The manual Netpay Radar remains implemented historical evidence. The tenant-scoped Netpay Master/Inbox vertical is implemented in later repository commits under the ratified Inbox boundary of `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`. |
| Gmail MVP-2D1 | Amendment 019 and IG-007 are **RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2**; synthetic/local D1 is implemented with Evidence Gate passed, D2 is conditional, and D3 is not authorized. |
| Gmail runtime | **D1 synthetic/local source slice implemented and evidenced:** no productive OAuth, credential, mailbox or real Gmail access. |
| Current engineering gate | D1 Evidence Gate is passed for the bounded source connector/manual sync. D2 remains conditional; productive OAuth, real Gmail access, scheduler/polling, Pub/Sub and D3 require separate gates. |
| Current work package | D1 evidence closure is complete; D2 candidate/human acceptance is the next separately gated package. D2-Lite remains a separate decision. |
| Next mandatory action | Review the D1 evidence and decide whether to authorize D2; do not implement D3 or access Gmail productively. |

**Precedence for this overlay:** ratified `IMPLEMENTATION_ROADMAP_AMENDMENT_019.md`
and `IG-007_NETPAY_GMAIL_INTAKE_IMPLEMENTATION_AUTHORIZATION.md` govern the
future Gmail D1/D2 authority and D3 exclusion; Amendments 012, 014, 015 and
018 remain the underlying Inbox, design and Commercial Intake boundaries.
Implementation/Git evidence confirms what exists but never grants authority.

**Last updated:** 2026-10-08 — Amendment 019 and IG-007 ratification

| Field | Current value |
| --- | --- |
| Current branch | Verify at session start. |
| Current HEAD | Verify at session start. |
| Current sprint | F-013 — Test and Conformance Foundation (closed). |
| Current engineering gate | IG-006 is active for F-011 Slices A–I under Amendment 002; E–G remain subject to the mandatory mapping, preflight, backfill and cutover gates. |
| Current work package | Workspace-scoped merchant request radar with persistent PostgreSQL records and React operator view. |
| Current blocker count | 0 known blockers. |
| Next mandatory action | Complete and validate F-011 A–D, then progress E–I only in Amendment 002 gate order; do not start a successor feature. |
| Current repository health | C06 is complete, the F-006/F-013 Canonical Runtime Baseline V1 reconciliation is validated, F-012 technical observability is closed, and F-013 Foundation conformance controls are closed. |

## Current runtime evidence

- C06B2A registration governance, C06B2B-1 authoritative queries, and C06B2B-2 immutability, rollback, and concurrency validation are complete.
- C06 migration lineage extends from `20260803_28` to `20260804_29`; upgrade, downgrade, and re-upgrade were validated against PostgreSQL.
- The technical closure evidence is recorded in [C06 Requirement Definition Catalog Closure](../engineering/C06_REQUIREMENT_DEFINITION_CLOSURE.md).

## Resolved Foundation debt

- **FOUNDATION-DEBT-001:** Closed by the accepted F-006/F-013 reconciliation. The canonical projection and its conformance evidence now validate the ratified 55-member Runtime Baseline V1. See the [Foundation Debt 001 Closure](../engineering/FOUNDATION_DEBT_001_CLOSURE.md).

## Current authoritative inputs

- Constitution and ratified architecture.
- [AR-005](../architecture/AR-005_REQUIREMENT_SEMANTIC_ARCHITECTURE_RATIFICATION.md) and [DR-002](../design/DR-002_REQUIREMENT_DEFINITION_SEMANTIC_MODEL.md).
- [IG-004](../engineering/IG-004_REQUIREMENT_DEFINITION_IMPLEMENTATION_AUTHORIZATION.md).
- [EP-001](../engineering/EP-001_ENGINEERING_GOVERNANCE_AND_DEVELOPMENT_PRACTICES.md).
- Ratified F-011 architecture: [F-011 Amendment 001](../engineering/F-011_IDENTITY_AUTHORITY_ENVELOPES_ARCHITECTURE_AMENDMENT_001.md),
  [ADR-014](../decisions/ADR-014_PRINCIPAL_MEMBERSHIP_ACTIVE_ORGANIZATION_AUTHORITY.md),
  and [Governance Contract Amendment 001](../engineering/F-011_GOVERNANCE_CONTRACT_AMENDMENT_001.md).

## Active authorized package

- The executive-priority [Netpay Operational Radar](../engineering/NETPAY_OPERATIONAL_RADAR.md)
  is the sole active implementation package. It is not a Foundation package.

- F-013 implemented deterministic Foundation conformance controls for explicit
  registry ownership, architectural import boundaries, F-012 observability
  isolation, and the synchronous Intake reference integration. Its closure
  evidence is recorded in
  [F-013 Test and Conformance Foundation Closure](../engineering/F-013_TEST_AND_CONFORMANCE_FOUNDATION_CLOSURE.md).

## Next allowed action

C07–C09 remain deferred and unauthorized. F-011 architecture and its two
Governance contract profiles and the implementation design are ratified/reviewed.
F-011 is In Progress for Slices A–I under active IG-006 as clarified by
Amendment 002. E–G may only migrate authority for the existing Radar after
their mapping/preflight gates are green; new Radar capabilities remain closed.
Amendment
003 is ratified solely as the Foundation completion-path correction; it does
not authorize F-016, F-017, F-015, or another feature. F-016 remains ineligible
until the prerequisite order is completed and a separate independent
implementation authorization is issued.
