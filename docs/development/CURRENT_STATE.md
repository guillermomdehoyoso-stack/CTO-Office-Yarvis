# Current Engineering State

## IG-014 Governance role transition technical closure — 2026-10-29

Amendment 027, F-011 Governance Contract Amendment 002 and IG-014 are ratified.
The closed `netpay_inbox_portfolio_reader` role and the sole transition from
`netpay_inbox_operator` passed final local conformance on base
`99709fc1dacc852d783dc45e09bd5d5a6b3a902f`. The role grants exactly Inbox
read/manage plus Master and Portfolio read. It grants no Master mutation,
sensitive data or reconciliation access.

Revision `20261022_54` descends directly from `20261021_53`. Upgrade,
downgrade before any transition receipt and re-upgrade passed in disposable
PostgreSQL. The final candidate had one Alembic head; Ruff and 99 affected
Governance, authentication, bootstrap and authorization tests passed. The
operational Membership transition remains blocked and was not executed.

## IG-015 Core v2 and commission settlement technical closure — 2026-10-29

Amendment 028 and IG-015 are ratified. Gates A–F passed on the reconstructed
publication candidate based on Governance commit
`a743205055d683108ba3e4b7064012373bbd5956`. Gate F was rerun on 2026-10-30
against the exact hash-identified source and the same parser bytes validated by
Gates A–E. The earlier publication-access block remains historical evidence.
Core v2 now defines distributor commission as AP + AQ + AR and preserves AS as
combined distributor/Netpay benefit. Legacy v1 facts retain their original AS
definition and expose corrected commission as pending reprocessing when no
verified original is linked.

The settlement profile preserves signed Decimal movements, entity, optional
Store, original concept, earned period and file/sheet/row provenance. Read-only
reconciliation leaves concept comparability, missing Store and unmatched Store
visible and keeps reported payment net distinct from bank confirmation.

The migration graph has one head, `20261028_55`, descending from
`20261022_54`. Its round trip passed in disposable PostgreSQL. On the final
candidate, Ruff passed, 125 affected backend tests passed, 80 Vitest tests
passed, 3 affected Playwright journeys passed and a fresh Vite build transformed
110 modules.
Evidence is recorded in
[`netpay-commission-ig015-conformance-20261029.txt`](../engineering/evidence/netpay-commission-ig015-conformance-20261029.txt).

No real settlement file was imported during closure. Historical Gate F evidence
from 2026-10-29 read the authorized source without modifying it and identified it by SHA-256
`04ca3675a8075c119a4db503a71e9ddb3759df525dce66be534aea1d29eb7978`.
The final parser reproduced all controls twice and isolated PostgreSQL staging,
replay and concurrent acceptance passed again on 2026-10-30. This evidence does not confirm a bank
deposit or authorize operational import. Production data, deployment,
productive migration, OIDC, roles, identity rules, commit and push remain
outside the authorization.

## Commerce Attention Portfolio P2A/P2B technical closure — 2026-10-21

Amendment 025 and IG-012 are ratified. P2A source integrity and P2B read-only
monthly indicators are implemented and passed the required synthetic isolated
gate. The effective Alembic head is `20261021_53`.
The Portfolio exposes monthly sales, distributor commission and commission on
sales with Decimal/MXN provenance, explicit non-calculable causes and ratio-of-
sums coverage. No-use batches without a confirmed cutoff remain
`metadata_pending` and non-effective.

Evidence is recorded in
[`netpay-commerce-attention-p2a-p2b-conformance-20261021.txt`](../engineering/evidence/netpay-commerce-attention-p2a-p2b-conformance-20261021.txt).
This state is part of the single authorized closure payload. Repository commit
and publication are distinct from the technical PASS; deployment, productive
migration and source import remain unperformed. P3-P5, terminals, MID, D2-Lite,
export, communications, Gmail/OAuth and pilot access remain closed.

## Commerce Attention Portfolio P0/P1 closed — 2026-10-20

P0/P1 of **Cartera operativa reportada** is implemented and technically closed
under Amendment 024 and IG-011. QRY-023/QRY-024 provide tenant-scoped read-only
list/detail, minimized data, masked RFC, deterministic filters/sort/pagination,
and a separately protected reconciliation queue. The effective permissions are
`netpay.portfolio.read`, `.sensitive.read`, and `.reconciliation.read`.

Closure evidence is recorded in
[`netpay-commerce-attention-p0-p1-conformance-20261020.txt`](../engineering/evidence/netpay-commerce-attention-p0-p1-conformance-20261020.txt).
Validation used synthetic data only and imported no productive data. D1 remains
not incorporated; MID and terminals have no authorized source. P2 is proposed
but unauthorized; P3 colors and P4/P5 remain closed. Portfolio preferences are
transient only and reset on full reload.

## Commerce Attention Portfolio P0/P1 authorization — 2026-10-19

[Amendment 024](../engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_024.md), the
[lean Portfolio design](../engineering/NETPAY_COMMERCE_ATTENTION_PORTFOLIO_DESIGN.md),
its [data/privacy matrix](../engineering/NETPAY_COMMERCE_ATTENTION_PORTFOLIO_DATA_PRIVACY_MATRIX.md)
and [IG-011](../engineering/IG-011_NETPAY_COMMERCE_ATTENTION_PORTFOLIO_P0_P1_AUTHORIZATION.md)
are **RATIFIED**. IG-011 opens implementation authority only for P0/P1 of
**Cartera operativa reportada**. Implementation has not started.

`IC-NETPAY-QRY-023` `ListCommerceAttentionPortfolio` and
`IC-NETPAY-QRY-024` `GetCommerceAttentionDetail` are registered as
RATIFIED/PLANNED. The authorized future implementation introduces separate
`netpay.portfolio.read`, `netpay.portfolio.sensitive.read` and
`netpay.portfolio.reconciliation.read` permissions because existing Master and
Inbox scopes are not exact least-disclosure substitutes. The permission catalog
has not yet been changed.

Netpay Master is the authoritative P0/P1 universe; unlinked Candidate,
CommercialIntakeItem and Dossier records remain in a separately authorized
reconciliation queue. Store ID is not MID, contact is labelled Contacto
registrado, and neutral badges indicate availability rather than health.

P2/D1 use, P3 colors, P4 expanded contacts/follow-up, P5 advanced experience
and preferences, terminals, D3, D2-Lite, export, communications and every
mutation remain closed.
## Risk-proportionate assurance ratified — 2026-10-19

[ADR-021](../decisions/ADR-021_RISK_PROPORTIONATE_ASSURANCE_FOR_YARVIS_MODULES.md)
and [Amendment 023](../engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_023.md)
ratify proportional assurance profiles for future Yarvis work: A regulated
evidence, B security-sensitive work, C business operations and D experience
and analysis. Packages may combine profiles, and the strongest applicable
control remains binding for each affected surface.

The policy defines when an Amendment, IG or ADR is required and permits a
reversible light change to proceed with explicit criteria, review and affected
tests when it introduces no entity, migration, permission, sensitive-data
category, external integration, material transition or effect outside the
existing owner. Existing contracts remain unchanged; future contracts shall
represent real boundaries rather than individual table interactions.

The published D2/H1/H2-Q/H2-I/H2-D/navigation block remains closed at
`8461818026d7a8de7c2571a8db6ea69294e35583`. This section records the
design-sequencing decision made by Amendment 023; the ratified successor above,
Amendment 024 and IG-011, now authorizes only P0/P1 implementation under B/C/D.
D3, D2-Lite, P2/D1, Gmail, OAuth, pilot access and communications remain
closed.

## Consolidated Netpay closure — 2026-10-19

The accumulated D2, H1, H2-Q, H2-I, H2-D and navigation implementation is
technically closed under Amendments 020–022 and IG-008–IG-010. D1 remains the
previously versioned source boundary at
`b6bc5930ae8b608ff55aa9849e995cb7639966d7`; this closure adds the later local
packages as one coherent change set. The current closure evidence is
[`netpay-d2-h2-consolidated-closure-20261019.txt`](../engineering/evidence/netpay-d2-h2-consolidated-closure-20261019.txt).

IG-010 is the latest closed gate. The validation used isolated PostgreSQL and
synthetic fixtures only. It accessed no Gmail account, OAuth flow, secret,
productive pilot service or real data, and it created no operational dossier.
H2-D PASS therefore records technical conformance, not the existence of a real
Netpay onboarding file.

D3, D2-Lite, P2, attachment-content access/OCR, Drive, automatic scheduling,
external communications and pilot expansion remain closed. The proposed Netpay
Commerce Attention Portfolio is a future product requirement without design or
implementation authority. A moderate, risk-proportional simplification of the
Netpay architecture is the next architectural decision to consider; it has not
been authorized or implemented and does not alter this closure.

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

This dated overlay records the ratified Amendment 019 and IG-007 position
without rewriting historical statements below. It supersedes only their
current-state, current-gate, current-work-package, and next-action readings.
Historical evidence remains immutable.

| Field | Reconciled current value |
| --- | --- |
| F-011 status | **Implemented / closed:** F-011 Stage I records F-011 COMPLETE — VALIDATED. IG-006 is retained as the historical authorization that opened the bounded work. |
| Implemented Netpay reality | The manual Netpay Radar remains implemented historical evidence. The tenant-scoped Netpay Master/Inbox vertical is implemented in later repository commits under the ratified Inbox boundary of `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`. |
| Gmail MVP-2D1 | Amendment 019 and IG-007 are **RATIFIED — IMPLEMENTATION AUTHORITY FOR GMAIL INTAKE D1/D2**; synthetic/local D1 is implemented with Evidence Gate passed, D2 is conditional, and D3 is not authorized. |
| Gmail runtime | **Restricted productive pilot evidenced:** one read-only Google connection processed exactly the approved 10-message manifest; 10 sources and 10 candidates remain unique after the controlled retry. |
| Current engineering gate | IG-010 H2-D PASS under ratified Amendment 022. IG-008 A/B/C, IG-009 H1 and IG-010 H2-Q/H2-I remain PASS. |
| Current work package | Versioned pre-case onboarding dossier is implemented and evidenced for the approved physical-location catalog. |
| Next mandatory action | Operator may review the real preview and explicitly create its dossier. Attachment content/OCR, Drive, P2, D3 and D2-Lite remain closed. |

**Ratified successor package:** `IMPLEMENTATION_ROADMAP_AMENDMENT_020.md` and
`IG-008_NETPAY_GMAIL_PRODUCTIVE_PILOT_AND_D2_AUTHORIZATION.md`. Gate A offline
implementation and conformance passed on 2026-10-09. Gate B passed on 2026-10-10
after acceptance of the non-secret Google project reuse record and the approved
10-message HMAC manifest. Gate C passed on 2026-10-11 after bounded ingestion,
human review, fresh-session readback and controlled retry; D3 and D2-Lite remain closed.

**Current evidence:** Gate A is recorded in
`docs/engineering/evidence/netpay-gmail-gate-a-conformance-20261009.txt`; Gate B
is recorded in `docs/engineering/evidence/netpay-gmail-gate-b-preflight-20261009.txt`;
Gate C is recorded in `docs/engineering/evidence/netpay-gmail-gate-c-pilot-20261010.txt`.
The restricted manual intake is operational only within the ratified pilot boundary.

**Precedence for this overlay:** ratified `IMPLEMENTATION_ROADMAP_AMENDMENT_019.md`
and `IG-007_NETPAY_GMAIL_INTAKE_IMPLEMENTATION_AUTHORIZATION.md` govern the
future Gmail D1/D2 authority and D3 exclusion; Amendments 012, 014, 015 and
018 remain the underlying Inbox, design and Commercial Intake boundaries.
Implementation/Git evidence confirms what exists but never grants authority.

**Last updated:** 2026-10-09 — IG-008 Gate A offline conformance passed

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
