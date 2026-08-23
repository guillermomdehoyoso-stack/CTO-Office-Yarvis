# AUTH-CONTRACT-001 — Productive Identity and Session Contracts

## Status

**RATIFIED — CANONICAL CONTRACT AUTHORITY — PLANNED, NOT IMPLEMENTED**

**Date:** 2026-08-20

**Authority:** Human Architecture Authority, expressly granted for AUTH-CONTRACT-001

**Architectural basis:** `IMPLEMENTATION_ROADMAP_AMENDMENT_017.md`, ratified at commit `3e1b07f7f7d5dc4590c05f613adbe9f6c0cf3a15`

**Scope:** Canonical semantic allocation only. No code, runtime registration, migration, configuration, provider, secret, identity, Membership, bootstrap execution, deployment, or AUTH-PROD-001 authority.

## 1. Gate decision and catalog evidence

`AUTH_CONTRACT_GATE: PASS`.

Amendment 017 requires a separate canonical allocation step, and the human AUTH-CONTRACT-001 instruction expressly authorizes that step. The effective documentary catalog was searched completely before allocation. Identity used only CMD/QRY/EVT `001`; Governance used QRY `001–002` and EVT `001`; no Session or Auth context existed. The IDs assigned below were therefore demonstrated free in the documentary catalog. Runtime projection remains a separate implementation artifact and is intentionally unchanged.

The pre-existing catalog/projection discrepancy is outside this gate: the documentary Tier 1 catalog declared 116 contracts but its rows represented 122 individual IDs, while `canonical_contracts()` and its immutable Runtime Baseline V1 test contained 99. AUTH-CONTRACT-001 corrects only the derived documentary total required by this gate; it does not reconcile the historical/runtime debt. After this allocation the documentary catalog represents 138 contracts; the runtime projection remains 99 until separately authorized.

## 2. Boundary classification

| Operation | Classification | Decision |
| --- | --- | --- |
| OIDC login redirect, callback HTTP, code exchange, discovery/JWKS, PKCE, JWT signature, issuer/audience/state/nonce validation | HTTP/OIDC TECHNICAL MECHANISM | No canonical contract; governed later by security policy and application bindings. |
| Cookie creation/deletion, CSRF mechanism, token refresh/disposal | SECURITY POLICY / HTTP/OIDC TECHNICAL MECHANISM | No canonical contract and no domain payload. |
| Bind External Identity | CANONICAL COMMAND | `IC-IDENTITY-CMD-002`. |
| Link Principal to Person | CANONICAL COMMAND | `IC-IDENTITY-CMD-003`. |
| Resolve Principal | CANONICAL QUERY | `IC-IDENTITY-QRY-002`; existing QRY-001 retains Party/reference semantics. |
| Grant / Revoke Membership | CANONICAL COMMAND | `IC-GOVERNANCE-CMD-001/002`. |
| Resolve Effective Membership | CANONICAL QUERY | `IC-GOVERNANCE-QRY-003`. |
| Evaluate Effective Authority | CANONICAL QUERY | Reuse `IC-GOVERNANCE-QRY-001 EvaluateAuthority` profile 1.1.0. |
| Start / Revoke Productive Session | CANONICAL COMMAND | `IC-IDENTITY-CMD-004/005`; HTTP login/logout are bindings only. |
| Get Current Session | CANONICAL QUERY | `IC-IDENTITY-QRY-003`. |
| Execute Bootstrap Enrollment | APPLICATION OPERATION | Orchestrates separately authorized Identity and Governance commands; grants no authority itself. |
| Close Bootstrap Window | CANONICAL COMMAND | `IC-GOVERNANCE-CMD-003`; terminal security-governance state. |
| Get Bootstrap Eligibility | CANONICAL QUERY | `IC-GOVERNANCE-QRY-004`; policy-bound, minimal decision only. |
| List Active Sessions for Administrative Review | AUDIT PROJECTION | Derived from canonical session state; no separate Tier 1 contract in this minimum allocation. |
| Login success/denial, logout completion, bootstrap enrollment outcome | AUDIT PROJECTION | Security audit records, not domain Events; no new canonical IDs. |

## 3. Common mandatory profile

Every allocated Command is version `1.0.0`, lifecycle `Ratified`, operational status `Planned`, and non-dispatchable until AUTH-PROD-001. It requires a trusted actor and authority basis, correlation ID, explicit idempotency key, canonical request fingerprint, and purpose-bound input. Its receipt namespace is `(owning context, authority scope or organization where applicable, contract ID, idempotency key)`. Equivalent replay returns the original safe outcome without another transition or Event; incompatible reuse fails `idempotency_conflict`.

Every Query is side-effect free, evaluates current canonical state, conceals foreign-tenant targets, and returns controlled status/enums plus opaque references only. Queries never accept client-declared authority as truth.

Events are emitted atomically with the owning local transition, once per successful receipt. They contain contract/version, safe opaque aggregate references, allowlisted transition, accountable actor reference, authority basis reference, correlation/causation, occurred/recorded timestamps, and outcome. They exclude email, display name, raw subject, raw claims, tokens, authorization codes, PKCE verifier, nonce, state, cookies, secrets, provider responses, free-text exceptions, and unrelated PII.

Retention classes are symbolic pending AUTH-POLICY-001: `identity_authority_audit`, `session_security_audit`, and `bootstrap_security_audit`. No duration, purge, legal hold, or storage behavior is authorized here.

Common semantic errors are `gate_closed`, `authority_denied`, `not_found` (including concealed foreign scope), `ambiguous`, `invalid_state`, `invalid_provenance`, `unknown_issuer`, `binding_collision`, `idempotency_conflict`, and `policy_denied`. Provider exceptions are never contract errors.

## 4. Identity contracts

| ID / name | Intent, actor and preconditions | Minimal input / output and transition | Events, invariants, consumers and recovery |
| --- | --- | --- | --- |
| `IC-IDENTITY-CMD-002 BindExternalIdentity` | Authorized Identity executor after independent approval; issuer allowlisted, provenance verified, active Principal resolved, no collision. | Principal reference, issuer reference, normalized subject representation, normalization version, provenance receipt and key; returns opaque binding/status; creates one verified active binding. | EVT-002. Unique `issuer + normalized_subject`; no email/name/header/unvalidated-token inference; immutable binding or future dedicated audited rotation. Failure creates no active binding. |
| `IC-IDENTITY-CMD-003 LinkPrincipalToPerson` | Authorized Identity executor after human review; human Principal, exactly one canonical Person, no conflicting link. | Principal/Person references, approval/evidence receipts and key; returns safe association status; establishes the single productive human link. | EVT-003. Person is not credential or Membership proof. No silent relink, merge or split; correction requires a future governed command. |
| `IC-IDENTITY-CMD-004 StartProductiveSession` | Identity session executor after technical OIDC validation, Principal resolution, effective Membership resolution and authority evaluation. | Resolved Principal, active Organization/Membership references, authentication-source class, policy version and key; returns opaque session and controlled expiries; `none → active`. | EVT-004. Tokens/claims never enter contract. Cannot create Identity/Membership/role. Local failure rolls back; callback remains technical. |
| `IC-IDENTITY-CMD-005 RevokeProductiveSession` | Session owner, authorized administrator, logout operation or mandatory authority-loss control. | Opaque session, allowlisted reason, authority basis and key; returns `revoked` or idempotent prior result; `active → revoked` terminal. | EVT-005. Expired/revoked never restore. Retry cannot duplicate event; failure remains deny-by-default. |
| `IC-IDENTITY-QRY-002 ResolvePrincipal` | Trusted authentication boundary; active verified binding required. | Issuer reference, normalized subject representation and normalization version; returns exactly one opaque active Principal/binding status or controlled denial. | Unknown issuer, collision, legacy `external_subject`, disabled Principal, ambiguity or absence fails closed. No Event. |
| `IC-IDENTITY-QRY-003 GetCurrentSession` | Authenticated application boundary or scoped administrator. | Opaque session/current request context; returns authenticated status, policy-permitted display label, active Organization label/reference, minimal capabilities and expiry class. | Expired/revoked/authority-changed denies. No token, raw subject, role matrix or cross-tenant data. |
| `IC-IDENTITY-EVT-002 ExternalIdentityBound` | Identity assertion of CMD-002 success. | Safe binding/Principal/issuer references, normalization version and provenance receipt reference. | Restricted resolution/audit consumers; no raw subject or evidence payload. |
| `IC-IDENTITY-EVT-003 PrincipalLinkedToPerson` | Identity assertion of CMD-003 success. | Safe Principal/Person association references and approval receipt. | Authority-resolution/audit consumers; does not assert Membership or employment. |
| `IC-IDENTITY-EVT-004 ProductiveSessionStarted` | Identity assertion of CMD-004 success. | Opaque session, Principal/Organization references, policy version and safe expiry timestamps. | Session administration/security audit; consumption grants no authority. |
| `IC-IDENTITY-EVT-005 ProductiveSessionRevoked` | Identity assertion of CMD-005 success. | Opaque session reference, allowlisted reason and revocation time. | Authorization invalidation/security audit; terminal and replay-safe. |

## 5. Governance contracts

| ID / name | Intent, actor and preconditions | Minimal input / output and transition | Events, invariants, consumers and recovery |
| --- | --- | --- | --- |
| `IC-GOVERNANCE-CMD-001 GrantMembership` | Authorized Governance membership operator with independent approval where policy requires; active Principal, Organization passing activity evaluation, closed valid role and tenant scope. | Principal/Organization references, role key, approval/authority receipt and key; returns Membership/status; creates one active Membership. | Reuses EVT-001 with activation. Unique Principal/Organization; no self-grant/client role. Atomic rollback on failure. |
| `IC-GOVERNANCE-CMD-002 RevokeMembership` | Authorized Governance revoker in target Organization; active Membership and allowlisted reason. | Membership/Organization references, reason, authority basis and key; returns terminal `revoked`. | Reuses EVT-001 with revocation. No destructive delete, reactivation or duplicate event. |
| `IC-GOVERNANCE-CMD-003 CloseBootstrapWindow` | Separately authorized bootstrap administrator/revoker; approved policy/window exists. | Window reference, allowlisted reason, authority basis and key; returns terminal closed status; `open → closed`. | EVT-002. Expiry requires closure. Never reopens, grants identity or creates Membership; a new window needs separate authority. |
| `IC-GOVERNANCE-QRY-003 ResolveEffectiveMembership` | Trusted authority resolver; Principal comes from Identity and any client Organization value is selector only. | Principal and optional selector; returns one active Membership, server-derived Organization and closed capabilities, or controlled denial/ambiguity. | Missing/revoked Membership, failed Organization activity evaluation, foreign selector, unknown role or ambiguity fails closed. Feeds QRY-001, never replaces it. |
| `IC-GOVERNANCE-QRY-004 GetBootstrapEligibility` | Authorized bootstrap application/reviewer under ratified policy. | Window and safe evidence/allowlist receipt references; returns eligible/not eligible, controlled reason, expiry/review status. | Unknown policy, closed/expired window, insufficient evidence or authority fails closed. No PII or allowlist contents. |
| `IC-GOVERNANCE-EVT-002 BootstrapWindowClosed` | Governance assertion of CMD-003 success. | Window reference, allowlisted reason, actor/authority receipt and close time. | Security audit/bootstrap denial projection; no person, email, subject, credential, secret or role grant. |

## 6. Existing-contract reconciliation

- `IC-GOVERNANCE-QRY-001 EvaluateAuthority` profile `1.1.0` remains the final target authority decision. `ResolveEffectiveMembership` supplies persisted Membership/Organization/capabilities only.
- `IC-GOVERNANCE-EVT-001 AuthorityChanged` profile `1.1.0` remains the single Event for Membership activation and revocation. No synonymous MembershipGranted or MembershipRevoked Event is allocated.
- `IC-IDENTITY-CMD/QRY/EVT-001` retain Party/intake resolution semantics and are not reinterpreted as productive OIDC binding or Principal resolution.
- `IC-GOVERNANCE-QRY-002` remains delegation policy and is not used for Membership or bootstrap.
- Session revocation caused by authority change is a CMD-005 transition causally linked to EVT-001; consuming EVT-001 alone grants no mutation authority.

## 7. Session and bootstrap lifecycle

Productive session lifecycle is `none → active → expired | revoked`; `expired` and `revoked` deny use and cannot return to active. Logout is an application/HTTP operation requesting CMD-005. Authority loss fails closed immediately; a separately authorized CMD-005 records terminal revocation.

Bootstrap lifecycle is prospectively `closed → open → closed`, but this gate creates no window. Opening/configuring it remains policy and later bootstrap-authorization work; only terminal closure is allocated. Enrollment is an application workflow that calls assigned Identity and Governance commands with separate authority, receipts and audit. No Membership becomes active before the verified chain completes. Partial failure is quarantined and compensated only under future approved policy.

## 8A. Prospective supplement — AUTH-BOOTSTRAP-CONTRACT-002 (2026-08-22)

This supplement records the later human ratification of the minimum missing bootstrap contracts. It does not alter the historical AUTH-CONTRACT-001 allocation or claim that any earlier gate created a window, identity, binding, Membership, session, configuration, or runtime capability. The additions are **Ratified / Planned** only; runtime registration and execution still require a separate implementation gate.

| ID / name | Owner, authority and preconditions | Receipt, transition and privacy |
| --- | --- | --- |
| `IC-IDENTITY-CMD-006 CreatePerson` | Identity owns creation of one reviewed human Person. A bootstrap executor needs an approved window, authority basis, correlation and human-review evidence. It cannot infer a Person from email, name, headers, tokens or unvalidated claims. | Identity-scoped receipt and fingerprint make equivalent replay safe; incompatible reuse is `idempotency_conflict`. Emits `IC-IDENTITY-EVT-006 PersonCreated` atomically. It creates no binding, Principal, Membership, role or authority. |
| `IC-IDENTITY-CMD-007 CreateHumanPrincipal` | Identity owns creation of one active human Principal for a reviewed Person. It requires the CMD-006 Person reference, approved window, authority basis and closed human-principal profile. | Identity-scoped receipt and fingerprint are required. Emits `IC-IDENTITY-EVT-007 HumanPrincipalCreated` atomically. It creates no external binding, Membership, role or authority. |
| `IC-GOVERNANCE-CMD-004 OpenBootstrapWindow` | Governance owns bounded bootstrap admission. It requires separately approved authority, allowlist-evidence reference, approved target Organization and closed role, accountable actor, and an expiry no greater than 24 hours. | Governance-scoped receipt makes opening idempotent. Emits `IC-GOVERNANCE-EVT-003 BootstrapWindowOpened` atomically. A window is `open` only until its first completed enrollment, manual/incident closure, lock, or expiry; it never reopens. |
| `IC-GOVERNANCE-CMD-005 ExecuteBootstrapEnrollment` | Governance owns terminal orchestration. It requires one open eligible window, a subject produced only by a previously validated OIDC authentication under the approved issuer, independent authority basis, and the approved Organization/role. It orchestrates CMD-006, CMD-007, CMD-003, CMD-002 and existing `IC-GOVERNANCE-CMD-001`. | One durable enrollment receipt/fingerprint permits only equivalent replay. It emits `IC-GOVERNANCE-EVT-004 BootstrapEnrollmentCompleted` and terminally closes the window atomically. Partial error is fail-closed: no active Membership may exist until the whole chain succeeds; quarantined partial state has no dispatchable authority and requires separate governed recovery. |

`issuer + normalized_subject` remains the only canonical external-identity key. Email may appear only as administrative allowlist evidence and is never a key for Person, Principal, binding, Membership or authority. CMD-005 may not accept or derive a subject from email, names, headers, tokens, code, state, nonce, PKCE verifier or unvalidated claims.

All new Commands require controlled audit fields: opaque aggregate and actor references, authority-basis/receipt reference, correlation/causation, allowlisted outcome and timestamps. All new Events exclude tokens, secrets, claims, email, names and raw subject. Audit failure fails the transition closed.

Existing `IC-GOVERNANCE-QRY-001 EvaluateAuthority` remains the final target authorization decision. Existing `IC-GOVERNANCE-QRY-003 ResolveEffectiveMembership` supplies persisted context only. Existing `IC-GOVERNANCE-EVT-001 AuthorityChanged` remains the sole Membership activation and revocation Event; CMD-005 must obtain it only through `IC-GOVERNANCE-CMD-001 GrantMembership` and allocates no synonymous Membership Event. `IC-GOVERNANCE-CMD-003 CloseBootstrapWindow` remains the terminal manual, expiry, incident or post-success closure mechanism.

## 8. Explicit non-effects and next gate

These contracts are assigned but not registered in runtime, dispatchable, authorized for execution, or implemented. This record does not modify `canonical_contracts.py`, contract tests, application modules, endpoints, `authentication.py`, D1, schemas, migrations, configuration, secrets, Google/OIDC resources, data, Person, Principal, binding, Membership, role, session, or bootstrap state.

The next required gate is `AUTH-POLICY-001 — Productive Identity, Session, Cookie, CSRF, Retention, Audit, Bootstrap and Rollback Policies`. Only after separately approving those policies may a new human gate consider AUTH-PROD-001 implementation and the prospective runtime projection update.
