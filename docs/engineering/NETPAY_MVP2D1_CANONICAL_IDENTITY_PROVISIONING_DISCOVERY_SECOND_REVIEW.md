# Second Adversarial Review — Netpay MVP-2D1 Canonical Identity Provisioning Discovery

**Review date:** 2026-08-18

**Decision:** **Complete**

## Scope and decision basis

This review assesses only:

- `NETPAY_MVP2D1_CANONICAL_IDENTITY_PROVISIONING_DISCOVERY.md`; and
- `NETPAY_MVP2D1_CANONICAL_IDENTITY_PROVISIONING_DISCOVERY_REVIEW.md`.

It verifies closure of MAJOR M-001 from the first review. It neither grants
authority nor changes the discovery's **Partial Path** classification. No
identity, issuer, subject, Principal, Membership, role, contract, catalog
entry, code, migration, database state, OAuth, Gmail, or runtime action is
created by this review.

## M-001 closure matrix

| Prior finding | Prior severity | Required correction | Evidence in discovery | Status |
| --- | --- | --- | --- | --- |
| M-001 — external-subject collision/impersonation was not explicit | MAJOR | State the risk and future design controls without implying present authority. | The `Global external_subject without issuer/provenance` row identifies cross-provider collision, incorrect binding, and impersonation. The `subject collision or impersonation` control section requires canonical `issuer + subject`, governed issuer allowlist, deterministic normalization, provenance verification, correct-namespace uniqueness, immutable/audited binding, fail-closed behavior, and no inference from email, name, headers, or unvalidated tokens. It expressly says the controls do not exist or authorize implementation. | Closed |
| M-001 — partial, non-reversible Person → Principal → Membership provisioning was not explicit | MAJOR | State the orphan/duplicate/inconsistent-chain risk and future recovery controls without authorizing implementation. | The `No atomic Person → Principal → Membership lifecycle` row identifies orphaned, duplicate, and inconsistent records without safe recovery. The `partial non-reversible provisioning` control section requires an explicit atomic boundary, idempotency key and durable receipt, auditable workflow state, verified chain before active Membership, governed compensation/quarantine, deterministic resumable reconciliation, authorized-command cleanup/revocation, and lifecycle audit events. It expressly says none authorize transactions, compensations, cleanup, commands, events, mutations, or implementation. | Closed |

## Verification

### A. `external_subject` collision or impersonation

All required elements are present and prospective only:

| Requirement | Result | Evidence |
| --- | --- | --- |
| Explicit risk | Pass | Risk table identifies collision, incorrect binding, and impersonation. |
| `issuer + subject` | Pass | Composite canonical identity namespace is a proposed design requirement. |
| Governed issuer allowlist | Pass | A governed issuer registry or allowlist is required. |
| Deterministic normalization | Pass | Listed explicitly. |
| Verifiable provenance | Pass | Verification before persistence is required. |
| Correct namespace and uniqueness | Pass | Uniqueness is required within the issuer namespace. |
| Immutable or audited binding change | Pass | Immutable binding or audited-command modification is required. |
| Fail-closed | Pass | Collision, unknown issuer, and insufficient evidence must fail closed. |
| No inference from weak attributes | Pass | Inference from email, name, headers, and unvalidated tokens is prohibited. |
| No present implementation or authority | Pass | The section expressly withholds issuer, subject, provider, schema, command, and runtime authorization. |

### B. Partial non-reversible provisioning

All required elements are present and prospective only:

| Requirement | Result | Evidence |
| --- | --- | --- |
| Explicit orphan/duplicate/inconsistent-chain risk | Pass | Risk table states all three outcomes and lack of safe recovery. |
| Proposed transactional boundary | Pass | Explicit transaction boundary for atomic local operations is required. |
| Idempotency key and persistent receipt | Pass | Idempotency key and durable receipt are required. |
| Auditable workflow | Pass | Auditable workflow state is required. |
| No active Membership before verified chain | Pass | Stated explicitly. |
| Governed compensation or quarantine | Pass | Required where atomic rollback is unavailable. |
| Deterministic, resumable reconciliation | Pass | Listed explicitly. |
| Authorized-command cleanup/revocation | Pass | Direct deletion is prohibited. |
| Prospective lifecycle events | Pass | Start, success, failure, compensation, and human-review events are required. |
| No present implementation or authority | Pass | The section expressly withholds transactions, compensation, cleanup, commands, events, mutation, and implementation. |

## Boundary confirmation

- **Partial Path remains supported.** The discovery distinguishes the bounded,
  existing Membership activation/revocation mechanism from the absent canonical
  Person-to-Principal lifecycle and absent complete productive path.
- **Amendment 014 remains design authority only.** It grants no provisioning,
  role, catalog, contract, implementation, OAuth, or Gmail authority.
- **No identity fact or allocation was created.** Neither reviewed document
  assigns a contract, issuer, subject, Person, Principal, Membership, or role.
- **No unsafe execution recommendation was introduced.** There is no direct
  SQL, production seed, or legacy-importer recommendation.
- **The next action remains reusable core governance/design.** It is a separate
  prospective Identity/Governance lifecycle decision, not Netpay-specific
  provisioning or implementation.

## Open findings

**Severity count:** BLOCKER 0; MAJOR 0; MINOR 0; EDITORIAL 0; OBSERVATION 0.

No open finding remains within this review scope. The known absence of a
complete canonical provisioning path remains a discovery result and future
governance/design concern, not an unresolved defect in the documentation.

## Next minimum permitted action

If separately authorized, prepare and review a prospective reusable
Identity/Governance lifecycle design. That future governance work must remain
separate from catalog allocation, implementation, data provisioning, OAuth,
and Gmail access.

## Explicit non-effects

This review does not modify the reviewed documents, code, contracts, catalog,
migrations, data, or configuration. It does not access PostgreSQL, Docker,
SQL, Gmail, or OAuth; it does not stage or modify
`apps/api/src/yarvis_api/api/authentication.py`; and it creates no commit or
push.
