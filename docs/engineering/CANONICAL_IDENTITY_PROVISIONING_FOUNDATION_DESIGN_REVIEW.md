# Adversarial Review — Canonical Identity Provisioning Foundation Design

**Review date:** 2026-08-18

**Decision:** **Amendment Required**

## Scope and decision basis

This review examines only
`CANONICAL_IDENTITY_PROVISIONING_FOUNDATION_DESIGN.md` against the current
ratified F-011/ADR-014 authority boundary, the recorded canonical provisioning
discovery, and Amendment 014's non-authority limits. It is a documentation
review. It neither assigns a contract, issuer, subject, identity, Membership,
role, or implementation authority nor opens a provisioning, OAuth, Gmail, or
runtime gate.

## Summary

The design is correctly framed as horizontal Core Foundation work: it separates
Person, Principal, Identity Binding, Issuer Registry, and Membership; retains
the Modular Monolith First ownership split; excludes vertical-specific behavior;
preserves F-011's trusted envelope and `AuthorityChanged` boundary; and clearly
distinguishes Proposed, Assigned, Authorized, and Implemented. It also gives a
sound preliminary treatment of receipts, quarantine, tenant isolation,
no-self-assignment, and the future gate sequence.

It is not yet sufficiently determinate for design ratification. The findings
below concern necessary lifecycle, uniqueness, recovery, privacy, and
operability semantics. They do not imply any present implementation work.

## Verification matrix

| Axis | Result | Evidence |
| --- | --- | --- |
| Core / horizontal boundary | Pass | §§1–3 expressly exclude Netpay, Energía Fotónica, Marketing, Gmail, and vertical policy. |
| Person / Principal / Binding / Membership separation | Pass | §1 ownership table and §4 invariants distinguish profile, internal subject, external binding, and Organization authority. |
| Modular Monolith First compatibility | Pass | Ownership remains Identity/Governance/Core; no shared vertical authority is introduced. |
| No present authority | Pass | §2, §11, and §15 withhold contracts, IDs, code, migrations, provisioning, OAuth, and Gmail. |
| Semantic operations and governance sequence | Pass | §§6, 7, 11, and 15 provide semantic-only operations and hard-gated review → ratification → catalog → gate sequence. |
| Full ratification-ready identity, recovery, privacy, and operability semantics | Fail | M-001 through M-005. |

## Findings

| ID | Severity | Evidence and defect | Impact | Exact required correction | Affected gate |
| --- | --- | --- | --- | --- |
| M-001 | MAJOR | §5 defines isolated state diagrams, but does not define the mandatory cross-aggregate effect of binding suspension/revocation, Principal disablement, Person suppression/correction, or Organization deactivation. §4 says later authority is re-resolved, but does not state which pending/active workflow and Membership transitions must follow each upstream state change. Person merge/split is absent; §13 lists only historical correction semantics as open. | A revoked or compromised upstream identity could leave an apparently active downstream Membership/workflow, and merge/split could create duplicate or wrongly linked authority chains. | Add a normative transition/effect matrix covering Binding, Principal, Person, Organization, Membership, and Workflow. It must state immediate fail-closed authority behavior, terminal versus recoverable states, required quarantine, whether a new approved workflow is needed, and merge/split/duplicate rules that preserve immutable audit history and never transfer authority implicitly. | Design ratification; later catalog and implementation gates. |
| M-002 | MAJOR | §4 requires `issuer + subject` uniqueness, but §13 leaves both multi-binding cardinality and issuer normalization versioning open. §10 names migration options but does not define the compatibility rule when an issuer is compromised, normalization rules drift, or a legacy/previous normalization collides with current canonical form. | The proposed uniqueness invariant is not decidable in all valid lifecycle cases; a rebind, issuer compromise, or normalization change could enable identity takeover or inconsistent resolution. | Define the canonical cardinality policy or an explicit bounded decision rule for active bindings per Principal and issuer. Define immutable normalization-version capture on binding/receipt, version coexistence, collision resolution, issuer compromise/suspension effects, and a fail-closed migration/reverification path. Do not allocate issuers or execute a migration. | Design ratification; future issuer-policy, catalog, and implementation gates. |
| M-003 | MAJOR | §8 states a bounded transaction and receipt, but gives no concurrency policy for two valid requests racing on the same Person, Principal, `issuer + subject`, or Principal/Organization pair. It does not state the required serialization/uniqueness outcome or how a workflow reacts after a uniqueness conflict. | Idempotency protects a repeated key but not distinct concurrent keys; races can still create duplicate candidates, binding conflicts, orphan workflow state, or uncertain audit outcomes. | Add a concurrency and conflict matrix: authoritative uniqueness boundaries, transaction isolation/serialization expectation, loser outcome, receipt/workflow state, retry eligibility, event/outbox behavior, and deterministic reconciliation for each contested resource. Keep it implementation-neutral. | Design ratification; later implementation-validation gate. |
| M-004 | MAJOR | §9 prohibits raw claims/tokens in projections and §11 lists safe status fields, but the design does not define retention, legal-hold authority, access review, redaction lifecycle, or deletion/retention conflict handling for provenance evidence, receipts, workflow state, and immutable audit. | The design cannot demonstrate privacy minimization over time or determine behavior when deletion obligations conflict with audit/provenance preservation. Evidence access and insider misuse remain under-specified. | Add a prospective data-governance section: data classes; maximum retention or policy-owned retention reference; explicit future legal-hold authority/fields/review/expiry; purpose-limited evidence access; redaction/tombstone rules; immutable safe audit boundary; and fail-closed handling for unresolved retention/deletion conflicts. No hold, purge, storage, or implementation is authorized. | Design ratification; future privacy/security and implementation gates. |
| M-005 | MAJOR | §11 describes safe health/status fields but has no required alert conditions, stuck-workflow detection threshold, recovery/disaster scenarios, runbook obligations, or acceptance evidence for collision, quarantine, compensation, failed outbox, issuer compromise, and cross-tenant denial. §12 acceptance criteria are qualitative rather than testable for those paths. | A future implementation could satisfy happy-path state diagrams while operational failures remain undetected or unrecoverable, weakening fail-closed and audit controls. | Add prospective operational acceptance criteria and a health/alert/runbook matrix. Include controlled alerts for collision, quarantine age, compensation failure, stuck workflow, receipt conflict, outbox/audit failure, issuer suspension, account takeover signal, cross-tenant denial anomaly, and retention conflict; define safe status data, owner/escalation class, recovery/disaster evidence, and testable pass criteria. | Design ratification; future security/operability and implementation-validation gates. |
| N-001 | MINOR | §7 says bootstrap automatically expires and has review, but does not require a maximum duration, pre-expiry review point, recorded grant scope, or explicit restricted authority envelope for break-glass. | Future governance could interpret temporary/emergency access inconsistently, increasing insider-abuse and privilege-escalation risk. | Add design-level mandatory fields and constraints for a future bootstrap/break-glass grant: scoped purpose, authority basis, start/expiry, mandatory review, revocation triggers, restricted permissions, and post-use review. Leave duration values to future ratification if not yet decidable. | Design ratification; future governance-policy gate. |
| E-001 | EDITORIAL | §3 says `Principal.person_id` is optional, while §4 says a Principal-to-Person relationship is part of the canonical chain and §13 leaves the linkage policy open. The document needs one sentence clarifying that the proposed workflow can support an explicit policy choice without assuming the current optional field is sufficient. | Readers may mistake current persistence shape for ratified future cardinality. | Clarify the proposed Person–Principal cardinality and state that the current optional reference is evidence only, not the adopted future policy. | Design ratification. |

## Required threat coverage assessment

| Threat | Result | Basis |
| --- | --- | --- |
| Account takeover | Partial | Binding compromise is implied by rotation, but M-001/M-005 require concrete suspension, downstream effects, and alert/recovery evidence. |
| Replay | Pass | Scoped receipt, fingerprint, and conflicting replay rejection are stated. |
| Issuer compromise | Fail | M-002: no issuer compromise/suspension lifecycle or re-verification semantics. |
| Normalization drift | Fail | M-002: normalization is proposed but versioned coexistence/conflict semantics are absent. |
| Insider abuse | Partial | Separation of duties exists; N-001 and M-004 require grant/audit/evidence-access controls. |
| Enumeration | Partial | Foreign target concealment is stated; safe query/status error and rate/abuse boundary require inclusion in M-005 operational controls. |
| Race conditions | Fail | M-003. |
| Orphaned authority | Partial | Quarantine/compensation exists, but M-001 and M-003 need downstream and concurrent conflict semantics. |
| Cross-tenant binding | Pass with operational follow-through | Invariant and trusted-envelope controls are stated; anomaly detection is required by M-005. |
| Deletion/retention conflict | Fail | M-004. |

## Severity count

BLOCKER 0; MAJOR 5; MINOR 1; EDITORIAL 1; OBSERVATION 0.

## Decision and next permitted action

**Amendment Required.** Amend only the proposed Foundation design to address
M-001 through M-005, N-001, and E-001, retaining its Core-horizontal scope and
explicit non-authority. After that amendment, the minimum permitted action is a
second independent design review. No catalog allocation, implementation,
provisioning, OAuth, Gmail, database access, or role assignment is authorized.

## Explicit non-effects

This review modifies no reviewed file, contract, catalog, code, migration,
configuration, data, Principal, Person, Identity Binding, Membership, issuer,
subject, role, or permission. It performs no PostgreSQL, Docker, SQL, Gmail,
or OAuth action; it does not modify or stage
`apps/api/src/yarvis_api/api/authentication.py`; and it creates no commit or
push.
