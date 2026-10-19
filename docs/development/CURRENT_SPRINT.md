# Current Sprint

## Consolidated Netpay closure — 2026-10-19

| Field | Current value |
| --- | --- |
| Versioned foundation | D1 is already versioned at `b6bc5930ae8b608ff55aa9849e995cb7639966d7`. |
| Closed accumulated package | D2, H1, H2-Q, H2-I, H2-D and navigation are technically closed as one coherent tree under Amendments 020–022 and IG-008–IG-010. |
| Latest gate | IG-010; H2-D technical conformance is closed. |
| Operational effect | None. Validation used synthetic data only and created no operational dossier. |
| Closed scope | D3, D2-Lite, P2, attachment content/OCR, Drive, automation, pilot expansion and outbound communications. |
| Future requirement | Netpay Commerce Attention Portfolio remains unapproved and unimplemented. |
| Next architectural decision | Decide whether to authorize moderate, risk-proportional Netpay simplification as a separate successor package. |

Current evidence is recorded in
[`netpay-d2-h2-consolidated-closure-20261019.txt`](../engineering/evidence/netpay-d2-h2-consolidated-closure-20261019.txt).
This record is ordinary engineering conformance evidence; it is not regulatory
evidence and does not claim the assurance level used for Energy Tracer.

## Documentary reconciliation — 2026-10-15

This reconciliation records existing authority and historical evidence only. It
supersedes current-state readings of the historical sections below; it does not
ratify a new scope, certify the current runtime, authorize publication or perform
an operational action.

| Evidence layer | Reconciled state |
| --- | --- |
| Verified branch | `feat/netpay-gmail-intake-sentinel` |
| Versioned HEAD | `b6bc5930ae8b608ff55aa9849e995cb7639966d7`: synthetic/local Gmail D1 source slice closed. |
| Ratification parent | `95b7aaabcbedd8ebca724ad39d5af524213f46b9`: Amendment 019 / IG-007 ratification already exists. |
| Local uncommitted work | D2/productive adapter, H1, H2 and navigation changes coexist. Their later authority/evidence files are local, not part of HEAD. |
| Remote HEAD / upstream | Remote `UNKNOWN`: read-only query failed on 2026-10-15. No upstream is configured; no integration was attempted. |
| Last documented gate | IG-010 H2-D PASS, recorded on 2026-10-14 under Amendment 022; this is an existing historical result, not a new PASS. |
| H2-Q / H2-I | Amendment 022 and IG-010 declare historical PASS. Specific closure traceability is **TO BE VERIFIED**; combined H1/H2-Q/H2-D results do not establish separate H2-Q/H2-I proofs. |
| Current work package | Existing local pre-case onboarding dossier for the approved physical-location catalog; no successor implementation package is opened here. |
| Next allowed action in this execution | Documentary reconciliation only. Before later changes, reverify the tree and resolve evidence traceability and scope attribution. |

### Existing authority and historical results

- [D1 evidence](../engineering/evidence/netpay-gmail-d1-conformance-20261008.txt)
  supports source capture/manual sync, isolation, deduplication, cursor behavior
  and readback only. Candidate classification and human acceptance are D2 work.
- [Amendment 020](../engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_020.md) and
  [IG-008](../engineering/IG-008_NETPAY_GMAIL_PRODUCTIVE_PILOT_AND_D2_AUTHORIZATION.md)
  are the existing local D2/restricted-pilot authority. Historical closures are
  [Gate A, 2026-10-09](../engineering/evidence/netpay-gmail-gate-a-conformance-20261009.txt),
  [Gate B acceptance, 2026-10-10](../engineering/evidence/netpay-gmail-gate-b-preflight-20261009.txt),
  and [Gate C closure, 2026-10-11](../engineering/evidence/netpay-gmail-gate-c-pilot-20261010.txt).
  The last records ten unique sources and ten unique candidates; these counts
  have not been re-read from the pilot in this execution.
- [Amendment 021](../engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_021.md),
  [IG-009](../engineering/IG-009_NETPAY_CANDIDATE_HUMAN_FOLLOW_UP_AUTHORIZATION.md)
  and [H1 evidence](../engineering/evidence/netpay-candidate-human-follow-up-h1-20261011.txt)
  record the append-only human-follow-up closure without expanding Gmail scope.
- [Amendment 022](../engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_022.md),
  [IG-010](../engineering/IG-010_NETPAY_ALTA_AND_SECOND_PILOT_BATCH_AUTHORIZATION.md),
  [catalog approval](../engineering/NETPAY_H2D_DOCUMENT_CATALOG_V1_APPROVAL.md)
  and [H2-D evidence](../engineering/evidence/netpay-h2d-conformance-20261014.txt)
  record the dossier closure. Approval is pilot operational authority, not
  corporate Netpay approval. **H2-D PASS does not mean an operational dossier
  was created:** the recorded readback has zero dossiers, reviews and evidence
  references. Current counts are **TO BE VERIFIED**.

### Pending verification and unchanged limits

All test counts, browser checks and migration results in those records are
historical; none was rerun for this documentary reconciliation. Current runtime,
exact correspondence of the entire local tree to those results, H2-Q/H2-I
specific evidence and navigation scope attribution remain **TO BE VERIFIED**.
No missing evidence is reconstructed from combined test counts.

The existing operator journey is preview, explicit human dossier creation and
review under the approved catalog. It is not executed or newly authorized by
this reconciliation. D3, D2-Lite, P2, attachment content/OCR, Drive, automatic
scheduling/polling, Gmail mutation and e-commerce without a physical
establishment remain excluded. No Gmail/OAuth or pilot-data operation is part
of this execution.

The original ratification-phase wording in Amendment 020, the pre-closure
catalog approval and earlier conditional statements are historical records;
they do not supersede the dated later closures. H2-Q/H2-I declarations remain
preserved, with their missing specific traceability explicitly unresolved.

## Historical governance overlay — 2026-10-11 (superseded current-state reading)

This overlay is the current sprint/status record. It preserves historical
material below and records the ratified Amendment 019 and IG-007 position.

| Field | Reconciled current value |
| --- | --- |
| Foundation / F-011 | **Implemented / closed:** F-011 Stage I accepted F-011 COMPLETE — VALIDATED. The earlier IG-006 scope remains historical authorization evidence. |
| Netpay Inbox and Radar | **Implemented:** the manual Radar is historical implemented evidence; the tenant-scoped Master/Inbox vertical is implemented under the ratified `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` Inbox boundary. |
| Gmail MVP-2D1 | Amendment 019 and IG-007 are **RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2**; D3 is not authorized. |
| Current authorization | Amendment 022 and IG-010 are ratified; H2-Q, H2-I and H2-D PASS. IG-008 A/B/C and IG-009 H1 remain PASS. |
| Current work package | Approved-catalog onboarding dossier, append-only review history, completeness and blockers are evidenced. |
| Next allowed action | Review and explicitly create the real dossier from its preview; keep attachment content/OCR, Drive, P2, D3 and D2-Lite closed. |

Amendment 020 and IG-008 are ratified. Gate A offline implementation and
conformance passed on 2026-10-09. Gate B passed on 2026-10-10 with one ready
connection and an approved immutable 10-message HMAC manifest. Gate C passed on
2026-10-11 with bounded ingestion, human review, fresh-session readback and a
controlled retry. D3, D2-Lite, scheduling and automation remain unauthorized.

## Identity

**Current work package:** Netpay Operational Radar — executive-priority manual operational vertical.
**Current authorization:** F-011 Identity and Authority Envelopes Slices A–I
under active IG-006 as clarified by Amendment 002. F-011 is In Progress;
F-016 and F-017 remain unstarted. E–G are limited to the existing Radar
identity/authority migration and require their mapping and preflight gates.

**Work package:** F-013 — Test and Conformance Foundation (closed)
**Authorization:** Technical Blueprint, Architectural Decision Trace, F-013 design, and EP-001.

## Goal

The active goal is the usable, synchronous and workspace-scoped Netpay Radar:
merchant registration, manual pasted-text requests, checklists, PENDIENTE ON/OFF,
filters and append-only operational history. See
[Netpay Operational Radar](../engineering/NETPAY_OPERATIONAL_RADAR.md).

Deliver deterministic Foundation conformance controls for explicit registry
ownership, architectural import boundaries, F-012 observability isolation, and
the synchronous Intake reference integration without adding runtime capability.

## Closure status

F-013 is closed: implementation, final validation, and focused review are
approved. This is not a Foundation closure and does not initiate or authorize
F-011, F-016, or successors. The closure evidence is recorded in
[F-013 Test and Conformance Foundation Closure](../engineering/F-013_TEST_AND_CONFORMANCE_FOUNDATION_CLOSURE.md).

## Completed scope

- Deterministic tests for canonical registry ownership and sealed composition.
- Architectural import controls for F-012 observability isolation.
- Synchronous Intake trace integration controls that reject deferred runtime
  dependencies.
- Quality-authority coverage verification for the architecture-conformance
  suite.

## Validation evidence

- Inventory: 475 tests; integral result: 475 passed, 0 failed, 0 skipped,
  0 xfail, and 0 omitted.
- F-013 focused conformance suite: 5 passed; affected architecture, registry,
  canonical-contract, and F-012 suites: 51 passed.
- Ruff and Pyright on the F-013 suite passed; Pyright reported 0 errors and
  0 warnings.
- Docker API build, `python -m compileall src`, Alembic head/current
  `20260805_30`, and `git diff --check` passed; the latter reported LF-to-CRLF
  warnings only.

## Explicitly deferred

F-016, F-017, F-010, F-014, F-015, C07–C09, workers,
queues, Event Dispatch, Notification Dispatch, Data Governance retention, and
all new business capabilities remain unauthorized. IG-006 authorizes no new
Radar capability, only the existing Radar authority migration bounded by
Amendment 002.

## Next package

No successor package is initiated. F-011 is In Progress for Slices A–I under
IG-006 and Amendment 002. E–G require approved real mappings and preflight
before backfill or cutover; H and I retain their sequential evidence gates.
Amendment 003 remains a
dependency-graph correction only and does not independently authorize F-016.
