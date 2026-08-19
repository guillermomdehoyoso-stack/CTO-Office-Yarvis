# Adversarial Review — Netpay MVP-2D1 Canonical Identity Provisioning Discovery

**Review date:** 2026-08-18

**Decision:** **Amendment Required**

## Basis

The discovery supports the classification **Partial Path**: it distinguishes an implemented bounded Membership activation/revocation mechanism from the absent Person-to-Principal lifecycle and from absent present authority under Amendment 014. However, its mandatory risk register does not explicitly cover two required risks, so the document needs a narrow documentary amendment before it can be treated as complete discovery evidence.

## Verification matrix

| Criterion | Result | Evidence / finding |
| --- | --- | --- |
| Existing Membership activation/revocation route | Pass | The operation matrix identifies the registered Governance endpoints and services. |
| Role authority, replay, event, terminal revocation | Pass | `foundation_membership_operator`, receipt/fingerprint replay, `AuthorityChanged`, `revoked_at`, and later-resolution denial are distinguished. |
| No complete Person → Principal path | Pass | The discovery identifies no normal command, handler, schema, or endpoint for Principal creation and Person linking. |
| `POST /people` is non-canonical | Pass | It records absence of provisioning contract, authority dependency, receipt idempotency, and domain audit event. |
| `external_subject` / issuer | Pass | It states uniqueness and persistence, with no issuer field or lifecycle. |
| One role per Membership | Pass | It identifies one stored role and the Principal/Organization uniqueness boundary. |
| Cross-Organization Membership separation | Pass | It distinguishes multiple Organization memberships from one membership per Principal/Organization pair and same-Organization activation/revocation. |
| Local/test Netpay utility | Pass | It is correctly bounded as local/test, vertical, non-contractual, and non-production. |
| Amendment 014 boundary | Pass | It accurately records design-only status and no authority for provisioning, roles, code, catalog, OAuth, or Gmail. |
| Reusable core design | Pass | The next design is correctly framed as horizontal Identity/Governance, not Netpay-owned. |
| No invented identity facts | Pass | No UUID, subject, issuer, role, person identity, or authority is inferred. |
| Unsafe recommendations | Pass | The discovery recommends neither direct SQL, production seeds, nor legacy-importer reuse. |
| Independent governance next action | Pass | The next action is a prospective governance/design decision, explicitly not implementation. |
| Complete mandatory risk coverage | **Fail** | See M-001. |

## Findings

| ID | Severity | Finding | Required correction |
| --- | --- | --- | --- |
| M-001 | MAJOR | The risk table refers to duplicate Person data, undefined subject provenance/reassignment, role elevation, lost audit, and vertical coupling. It does not explicitly state the risk of `external_subject` collision or impersonation, nor the risk that a partially completed Person → Principal → Membership provisioning sequence is non-reversible or leaves an orphaned/inconsistent chain. Both are mandatory review criteria and are material because subject uniqueness alone does not establish provenance, while the missing lifecycle has no atomic command/rollback boundary. | Add explicit, bounded risk rows for subject collision/impersonation and partial non-reversible provisioning, together with future design controls. Do not implement, assign, or invent any identity. |

**Severity count:** BLOCKER 0; MAJOR 1; MINOR 0; EDITORIAL 0; OBSERVATION 0.

## Conclusion

The substantive **Partial Path** classification is supported. The amendment required is limited to completing the already-requested risk analysis; it does not create a new provisioning requirement, authority, contract, catalog allocation, or implementation gate. Amendment 014 remains design authority only, and all provisioning, bootstrap, OAuth, Gmail, and execution boundaries remain closed.
