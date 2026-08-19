# Netpay MVP-2D1 — Canonical Identity Provisioning Discovery

**Inspection date:** 2026-08-18

**Classification:** **Partial Path**

## Scope, baseline, and non-effect

This static discovery examines the existing Person, Principal, Membership, and role mechanisms relevant to a future canonical identity chain. It is not a provisioning authorization and created no Person, Principal, external subject, Membership, role, contract, or runtime state.

Inspected sources include the Person/Principal/Organization models; F-011 authority, resolver, Governance and People routes; schemas; canonical-contract baseline; migration `20260806_32`; local/test provisioning and focused tests; F-011, IG-006, ADR-014, Stage I evidence; Amendments 012 and 014; the recorded Principal/Membership determinations; and pertinent Git history. No database, Docker, service, SQL, Gmail, OAuth, secret, or effective application configuration was accessed.

## Canonical flow found

```text
authenticated local/test subject
  → persisted Principal.external_subject lookup
  → active Principal
  → active PrincipalMembership for selected Organization
  → closed server role-to-permission map
  → immutable IdentityAuthorityEnvelope
```

The persisted resolver is authoritative for use-time authority, not for identity creation. `Person` is optional on `Principal` and is not credential material. An Organization is selected only from active Membership; headers, token claims, mailbox values, names, and workspaces do not grant authority or select a tenant.

## Operation matrix

| Operation | Existing mechanism | Contract / authority | Idempotency and audit | Status |
| --- | --- | --- | --- | --- |
| Create Person | `POST /people` creates a `Person`; uniqueness is limited to email persistence. The route is included in the application. | No inspected Principal-lifecycle contract or authority dependency protects this route. | No idempotency key, command receipt, or domain event found; duplicate email returns a validation failure. | Existing implementation, not an identified canonical governed provisioning path. |
| Create Principal and link Person | No normal command, handler, schema, or endpoint found. `Principal.person_id` is optional. | No allocated Identity command authorizes this lifecycle. | No receipt or audit event found. | Missing. |
| Establish external subject / issuer | `Principal.external_subject` is unique and the resolver performs exact lookup. The inspected model has no `issuer` field. The local/test adapter supplies an authenticated actor subject. | Architecture limits deterministic provider use to local/test. | Database uniqueness prevents duplicate subject rows; no canonical issuer validation or production identity-provisioning policy was found. | Partial; no production/general lifecycle mechanism. |
| Activate Membership | `POST /governance/memberships` calls `activate_membership`. It requires an active Principal and creates one membership for the envelope Organization. | Requires resolved `governance.membership.create`, granted by persisted `foundation_membership_operator`. QRY-001 and EVT-001 profiles are ratified; no stable Membership-mutation command ID is allocated. | Organization-plus-key command receipt and fingerprint replay/conflict behavior; atomic `AuthorityChanged` event. | Existing bounded implementation; authority is not supplied by Amendment 014. |
| Revoke Membership | `POST /governance/memberships/{membership_id}/revoke` terminally revokes same-Organization Membership. | Requires resolved `governance.membership.revoke`, also in `foundation_membership_operator`. | Same receipt/replay protection; `revoked_at` and `AuthorityChanged` event are recorded atomically. | Existing bounded implementation. |
| Assign role | Activation accepts one `role` string and persists it on the Membership. | Effective permissions are only from the closed `ROLE_PERMISSIONS` map. | Membership uniqueness and activation receipt apply, but the activation service does not itself reject an unknown role; later authority resolution denies unknown roles. | Partial control; role lifecycle/approval command is absent. |
| Local/test Netpay provision | `local_netpay_authority.py` can create/reuse a Principal and active Membership for one fixed Netpay operations role. | Explicitly local/test-only; it is not an API, canonical contract, or production route. | Transactional reuse/conflict behavior and focused tests; no F-011 `AuthorityChanged` event path found there. | Local/test evidence only. |

## Findings by required question

1. **Create Person:** a generic API route exists, but no inspected canonical contract, authority check, idempotency receipt, or provisioning audit makes it an authorized canonical identity-creation path.
2. **Create Principal / link Person:** no such standard command or endpoint exists. The only Principal creation found is the isolated local/test Netpay utility, which does not link a Person.
3. **`external_subject`:** it is a unique persisted resolver key. No issuer is modeled. The deterministic local/test adapter supplies a subject; no general validation, issuer registry, or non-local provisioning policy exists.
4. **Membership activation authority:** a currently resolvable actor with the persisted `foundation_membership_operator` role for the same Organization can invoke the bounded service. This does not solve bootstrap: it presupposes an already active, authorized Principal/Membership chain.
5. **Roles:** the closed server map is `apps/api/src/yarvis_api/application/authority.py`. It includes the F-011 membership operator and roles for Radar, Intake, Documents, Mission, Economics, Tasks, Process, Netpay Master, Netpay Inbox, and local Netpay operations. Proposed MVP-2D1 intake roles are not currently entries in that map or canonical allocations.
6. **Role cardinality:** one Membership stores exactly one `role`. A Principal can have Memberships in multiple Organizations, but `(principal_id, organization_id)` is unique; the model does not support a role set on one Membership.
7. **Idempotency:** Membership activate/revoke has a durable organization-scoped command receipt and functional fingerprint. Person creation has no equivalent; the local/test utility performs bounded lookup/reuse rather than canonical command-receipt replay.
8. **Events and audit:** Membership activation/revocation appends `AuthorityChanged` with trace IDs, transition and safe canonical IDs. The tests cover replay conflict, activation/revocation event sequence, immediate denial after revocation, and exclusion of token/email from payload. Person creation has timestamps only in the inspected path.
9. **Revocation:** it is terminal, sets `revoked_at`, records a receipt/event, and makes later authority resolution fail because only active Memberships resolve.
10. **Production authorization:** Membership endpoints are registered application routes, but the source material allocates only QRY-001 and EVT-001 profiles, not a canonical Membership-mutation command or Principal lifecycle contract. Principal creation is local/test only. This is not a complete productive provisioning path.
11. **Guillermo prerequisites:** obtain separately authorized canonical identity evidence; define/allocate an Identity-owned Person/Principal linkage and external-subject/issuer lifecycle; establish its authorization, audit, idempotency, tenant and role validation; then use a separately authorized canonical Membership allocation. No visible name, mailbox, prior Not Found result, or local/test subject can bridge these gaps.
12. **Amendment 014:** it ratifies design limits only. It creates no Principal, Membership, role, contract allocation, implementation gate, OAuth, Gmail, or bootstrap. Its ordered prerequisites remain canonical identity proof, separate catalog authority, independent implementation gate, security/privacy prerequisites, then a separate OAuth/pilot gate.
13. **Reuse boundary:** Person, Principal, Membership, Organization resolution and the role map are horizontal Identity/Governance mechanisms, not Netpay-owned concepts. A future lifecycle contract should remain reusable across verticals. The local/test Netpay utility is deliberately vertical and must not become the general mechanism.

## Contract, authority, and execution distinction

`IC-GOVERNANCE-QRY-001 EvaluateAuthority` and `IC-GOVERNANCE-EVT-001 AuthorityChanged` have ratified F-011 profiles. The catalog and F-011 amendment do not allocate a stable command contract for Principal creation, Person-to-Principal linking, external-subject issuance, or Membership mutation. Existing endpoint code does not itself create that missing contract authority.

IG-006 and the accepted F-011 work are historical implementation/closure evidence for the bounded F-011 slice. They do not supply a new identity-provisioning mandate. Amendment 012 governs Inbox only and excludes Gmail. Amendment 014 remains Design Ratified only and expressly withholds all provisioning and implementation authority.

## Gaps and risks

| Gap | Risk | Required future disposition |
| --- | --- | --- |
| No canonical Person → Principal command | A generic Person record could be mistaken for authentication identity. | Identity-owned lifecycle design and separately allocated contract. |
| No issuer model or external-subject lifecycle | Subject provenance and reassignment rules are undefined. | Explicit issuer/subject authority and validation decision; do not infer from email. |
| Generic Person route lacks authority/audit/idempotency | Unauthorized or duplicate operational identity data if treated as provisioning. | Do not use as provisioning; govern separately before any reuse. |
| Membership endpoint accepts a role string without immediate map validation | An unusable unknown role can be persisted and later denied. | Explicit closed-role validation and approval boundary in any authorized future slice. |
| Existing membership operator presupposes a bootstrap actor | Circular bootstrap cannot be solved by a local/test helper. | Separate bootstrap authority with canonical evidence and audited seed/gate. |
| MVP-2D1 roles are proposals only | Treating them as existing roles would bypass catalog and gate governance. | Separate contract/role allocation after identity proof. |
| Global `external_subject` without issuer/provenance | A collision across identity providers, incorrect binding, or impersonation can be mistaken for a valid unique subject. | Future Identity design must establish issuer-plus-subject provenance and fail closed; no such control exists or is authorized now. |
| No atomic Person → Principal → Membership lifecycle | A failure between records can leave orphaned, duplicate, or inconsistent state without safe recovery. | Future provisioning design must define atomicity or governed recovery; no transaction, compensation, cleanup, command, or event is authorized now. |

### Proposed future design controls — subject collision or impersonation

The following are future design requirements only. They neither exist in the
current model nor authorize an issuer, subject, provider, schema, command, or
runtime implementation:

- a composite canonical identity namespace of `issuer + subject`;
- a governed issuer registry or allowlist;
- deterministic normalization rules;
- provenance verification before persistence;
- uniqueness within the correct issuer namespace;
- immutable binding, or binding modification only through an audited command;
- fail-closed handling for a collision, unknown issuer, or insufficient
  evidence; and
- prohibition on inferring a subject from email, name, headers, or unvalidated
  tokens.

### Proposed future design controls — partial non-reversible provisioning

The following are future design requirements only. They do not authorize
transactions, compensations, cleanup, commands, events, data mutation, or
implementation:

- an explicit transaction boundary for local operations that must be atomic;
- an idempotency key and durable receipt for retries;
- an auditable workflow state;
- no active Membership until the complete chain has been verified;
- governed compensation or quarantine when atomic rollback is unavailable;
- deterministic, resumable reconciliation;
- revocation or cleanup only through authorized commands, never direct
  deletion; and
- audit events for start, success, failure, compensation, and human review.

## Next minimum permitted action

Prepare a separate, prospective governance decision for the reusable Identity/Governance provisioning lifecycle: Person-to-Principal linkage, subject/issuer provenance, one-role Membership policy, role validation, idempotency, audit/event contract, and controlled bootstrap. It must be reviewed and separately authorized before any data mutation. This discovery does not authorize that decision, code, catalog change, provisioning, or Gmail work.

## Explicit non-effects

This discovery does not modify or authorize code, data, contracts, catalog entries, migrations, configuration, roles, Principal/Membership provisioning, OAuth, Gmail, Docker, SQL, or external access. It does not modify or stage `apps/api/src/yarvis_api/api/authentication.py`, and it creates no commit or push.
