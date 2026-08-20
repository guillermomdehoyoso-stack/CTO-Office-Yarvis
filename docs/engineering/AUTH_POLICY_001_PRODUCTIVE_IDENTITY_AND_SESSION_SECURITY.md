# AUTH-POLICY-001 — Productive Identity and Session Security

## Status and authority

**APPROVED POLICY BASELINE — IMPLEMENTATION REQUIRES AUTH-PROD-001**

**Date:** 2026-08-20

**Authority:** Human Architecture Authority, expressly granted for AUTH-POLICY-001

**Architectural authority:** `IMPLEMENTATION_ROADMAP_AMENDMENT_017.md`, ratified at commit `3e1b07f7f7d5dc4590c05f613adbe9f6c0cf3a15`

**Contract authority:** `AUTH_CONTRACT_001_PRODUCTIVE_IDENTITY_AND_SESSION_CONTRACTS.md`, commit `7f05bb863c52e854e7f5826657045f25d02a57bc`

This document is normative policy only. It does not authorize code, runtime registration, migrations, configuration, secrets, providers, identities, Memberships, sessions, bootstrap execution, deployment, DNS, D1 changes, or modification of `authentication.py`.

## 1. Scope, terminology and current-state findings

This policy governs a future provider-neutral productive authentication boundary using OIDC Authorization Code Flow, canonical Identity Binding, server-side sessions and F-011 authority resolution. It is core infrastructure, not Netpay-owned functionality.

The following terms are distinct:

- **Normative policy:** mandatory invariant or limit approved here.
- **Pilot initial value:** approved starting value that may become more restrictive through environment configuration without changing contract semantics.
- **Environment configuration:** non-secret deployment input validated at process startup.
- **Secret:** confidential value injected from a secret manager or equivalent; never source, documentation or frontend input.
- **Technical mechanism:** HTTP, OIDC, cryptographic, cookie or storage binding implementing policy without becoming a domain contract.

Read-only inspection found no conflict requiring an amendment. Current local/test implementation uses a deterministic header token and `VITE_YARVIS_AUTH_TOKEN`; CORS allows configured localhost origins with credentials and broad methods/headers. Existing Principal uses global `external_subject` without issuer, Membership uses `active`/terminal `revoked`, and Organization has an existing activity status evaluation. These are present-state facts, not productive-policy compliance. Productive implementation must fail closed until the new binding/session model is implemented and validated.

### 1.1 Contract-policy traceability

| Policy area | Governed or restricted contracts |
| --- | --- |
| External binding and Principal/Person chain | `IC-IDENTITY-CMD-002`, `IC-IDENTITY-CMD-003`, `IC-IDENTITY-QRY-002`, `IC-IDENTITY-EVT-002`, `IC-IDENTITY-EVT-003` |
| Productive session | `IC-IDENTITY-CMD-004`, `IC-IDENTITY-CMD-005`, `IC-IDENTITY-QRY-003`, `IC-IDENTITY-EVT-004`, `IC-IDENTITY-EVT-005` |
| Membership and effective authority | `IC-GOVERNANCE-CMD-001`, `IC-GOVERNANCE-CMD-002`, `IC-GOVERNANCE-QRY-003`, reused `IC-GOVERNANCE-QRY-001`, reused `IC-GOVERNANCE-EVT-001` |
| Bootstrap closure and eligibility | `IC-GOVERNANCE-CMD-003`, `IC-GOVERNANCE-QRY-004`, `IC-GOVERNANCE-EVT-002` |

All 16 AUTH-CONTRACT-001 assignments and both reused F-011 contracts are constrained here. No new contract is introduced.

## 2. Trust boundaries and threat model

| Boundary / threat | Required control and failure behavior |
| --- | --- |
| Browser ↔ Yarvis API: session theft, CSRF, XSS-assisted requests | Opaque `HttpOnly` cookie; server-side state; CSRF token on mutations; exact origin validation; no bearer/provider token in browser; fail closed. |
| Yarvis ↔ OIDC provider: spoofing, issuer/JWKS compromise, algorithm confusion | Exact issuer/audience; pinned allowlisted metadata policy; authorized JWKS; algorithm allowlist excluding `none`; bounded caching and forced disable capability; fail closed on drift or ambiguity. |
| Callback: replay, login CSRF, redirect abuse, code interception | Single-use state and nonce, PKCE S256, exact callback URI, bounded attempt, one-time code handling and closed post-login redirects. |
| External identity ↔ Principal: collision, account takeover, normalization drift | Unique `issuer + normalized_subject`; versioned deterministic normalization; provenance receipt; no email inference; collision/unknown issuer/legacy record fails closed. |
| Principal ↔ Membership ↔ Organization: privilege escalation, confused deputy, cross-tenant selection | Persisted active chain, backend-derived Organization, closed role/capabilities, `EvaluateAuthority`, target ownership and concealed foreign scope. |
| Session lifecycle: fixation, replay, stale authority, excess sessions | Rotation after login, ≥256-bit random ID, persisted one-way representation, idle/absolute expiry, maximum three sessions, immediate revocation and no reactivation. |
| Bootstrap: reuse, self-enrollment, permanent backdoor, partial provisioning | Disabled by default, external allowlist, one successful enrollment, 24-hour maximum, separate authorities/contracts, terminal close, receipts and audit. |
| Logs/audit/metrics: token, PII or existence disclosure | Closed event fields, sanitization, generic errors, purpose-bound access, controlled retention and verifiable purge/anonymization. |
| Insider/administrator abuse | Least privilege, separation of duties, authority-basis receipt, immutable audit, bounded bootstrap and reviewed administrative actions. |
| Rollback/restore: reactivation of revoked authority | Revoke/close before rollback; preserve audit; restore cannot reactivate revoked Membership, session, binding or bootstrap; post-restore reconciliation before reopening. |

## 3. OIDC, issuer and redirect policy

1. Productive authentication uses Authorization Code Flow with PKCE S256. The backend performs code exchange and token validation; the browser never receives provider tokens.
2. Issuer is an exact, governed allowlist entry. Discovery and JWKS URLs must derive from or match approved metadata. Audience/client ID is exact. Allowed signing algorithms are explicitly configured; `none`, symmetric downgrade and provider-supplied algorithm choice are rejected.
3. Signature, issuer, audience, timestamps, nonce and state are mandatory. State and nonce are cryptographically unpredictable, bound to one authentication attempt, single-use and never logged or persisted in reversible form beyond their maximum lifetime.
4. Authentication attempts expire after at most 10 minutes. Incomplete attempt material is deleted after at most 15 minutes.
5. Callback URI is an exact allowlisted URI. Post-login destinations are exact allowlisted absolute destinations or validated local relative paths. Scheme-relative URLs, userinfo, fragments used for credentials, wildcard hosts and open redirects are prohibited.
6. Email is not a canonical key. The only external identity key is the governed, normalized `issuer + subject`. Verified email may support bootstrap evidence only and never proves employment, Organization, Membership or role.
7. Successful authentication without an active complete canonical chain returns a generic denial and creates no Membership or authority.
8. Issuer disablement immediately prevents new login and new resolution through that issuer; it does not destructively reassign bindings. Recovery requires provenance reverification and human approval under a later operational procedure.

This section constrains `IC-IDENTITY-CMD-002`, `IC-IDENTITY-CMD-004`, `IC-IDENTITY-QRY-002` and `IC-IDENTITY-EVT-002/004`. Redirect, callback, PKCE, JWT and JWKS remain technical mechanisms.

## 4. Identity Binding, Membership and authority policy

- Binding normalization is deterministic and versioned. Stored provenance identifies the verifier/policy and receipt, not raw claims, token, email code or link. No silent renormalization is permitted.
- Binding collision, issuer ambiguity, unknown issuer, unsupported normalization version, unverifiable provenance or legacy `external_subject` without an approved migration classification fails closed.
- A human Principal must resolve to exactly one reviewed canonical Person. Linking does not prove Membership. Person data is not credential material.
- Membership is explicit and unique per Principal/Organization. Grant and revocation require Governance authority, idempotency receipt and `AuthorityChanged`. Revocation is terminal.
- Effective Organization is derived by backend from active Membership. A client value is selector only; ambiguity or foreign scope is denied/concealed.
- `IC-GOVERNANCE-QRY-001 EvaluateAuthority` remains the final target-action decision. `IC-GOVERNANCE-QRY-003 ResolveEffectiveMembership` supplies persisted context but cannot authorize alone.
- D1 receives only the minimum existing capability set approved for its operator role. Authentication, email verification, bootstrap eligibility or frontend navigation never expands it.
- Membership/role/Organization authority change invalidates affected sessions immediately for authorization. Revocation commands and audit must follow without relying on eventual client behavior.

This section governs `IC-IDENTITY-CMD-002/003`, `IC-IDENTITY-QRY-002`, `IC-IDENTITY-EVT-002/003`, `IC-GOVERNANCE-CMD-001/002`, `IC-GOVERNANCE-QRY-001/003` and `IC-GOVERNANCE-EVT-001`.

## 5. Productive session policy

| Parameter | Pilot initial value / invariant |
| --- | --- |
| Storage | Server-side only. |
| Browser identifier | Cryptographically random, at least 256 bits of entropy. |
| Persistent representation | Hash or other one-way, non-reversible representation only. |
| Idle expiry | 30 minutes. |
| Absolute expiry | 8 hours from successful login. |
| Rotation | Mandatory after callback/login completion and after any future privilege-sensitive reauthentication. |
| Maximum active sessions | 3 per Principal; creating a fourth terminally revokes the oldest active session. |
| Logout | Immediate server-side revocation plus explicit cookie deletion. |
| Authority loss | Immediate denial and revocation of affected sessions. |
| Terminality | Expired or revoked sessions never reactivate. |
| Provider tokens | Do not persist access, ID or refresh tokens for the pilot. No offline access/refresh token request unless separately approved. |

Session activity time is updated only through an authenticated, policy-valid request and cannot exceed absolute expiry. Parallel creation/revocation must use constraints or locking so the three-session cap is deterministic. Errors reveal neither session existence nor identity existence.

This section governs `IC-IDENTITY-CMD-004/005`, `IC-IDENTITY-QRY-003` and `IC-IDENTITY-EVT-004/005`.

## 6. Cookie, CSRF, CORS and origin policy

The productive session cookie is opaque, contains no identity data, uses `HttpOnly=true`, `Secure=true`, `SameSite=Lax`, `Path=/`, and no `Domain` attribute unless a later topology review demonstrates necessity. Use a `__Host-` name when topology permits. Its maximum age cannot exceed session absolute expiry. It is explicitly expired on logout, revocation response where possible, and invalid-session handling. Cookie values are prohibited in URLs, logs, metrics, traces and Events.

Every mutating application operation, including logout, requires a backend-validated unpredictable CSRF token bound to the session and rotated with it. SameSite is defense-in-depth, never the sole defense. Applicable `Origin` and `Referer` values must match exact allowlists; missing values are handled by an explicit endpoint policy, never implicit acceptance. Missing/invalid CSRF fails closed without revealing session state. OIDC callback uses single-use state/nonce, not ordinary CSRF.

Production CORS uses exact HTTPS origins, credentials only for those origins, minimum methods and minimum headers. Wildcard origin with credentials is forbidden. The productive origin is external configuration. Localhost/loopback origins are allowed only in local/test. Productive cookies must not be sent to an unapproved origin.

These controls are security policies and technical bindings; they allocate no new contracts.

## 7. Rate limiting and enumeration resistance

| Surface | Pilot initial limit |
| --- | --- |
| Login initiation | 10 attempts per 10 minutes per privacy-preserving origin/context key. |
| Invalid callback | 20 attempts per 10 minutes per privacy-preserving origin key. |
| Bootstrap | 5 attempts per hour per governed window/origin context; exceeding the limit locks the window pending administrative review. |
| Session read/logout/revocation | Conservative endpoint-specific limits defined by implementation and verified not to impede emergency revocation. |

More restrictive environment values are permitted without changing contracts. Keys must not use or expose full email, raw subject, full IP or token. Responses and timing must not reveal whether an identity, email, Principal or Membership exists.

## 8. Bootstrap and administrative operation policy

Bootstrap is disabled by default. Enabling it requires a separately authorized administrative action, an external allowlist reference, approved target Organization/role authority, start/expiry timestamps, accountable actor and receipt. The window lasts at most 24 hours and accepts at most one successful enrollment. First success triggers terminal automatic closure; manual closure is always available. A closed/expired window cannot reopen or be reused; a new window requires new authorization and record.

Bootstrap verifies allowlisted evidence, then orchestrates the assigned Identity and Governance contracts. It cannot trust Organization, role or capabilities from the frontend; cannot hardcode Guillermo or any person; cannot infer subject from email/name; and cannot bypass separation of duties, tenant isolation, provenance, idempotency, audit or `EvaluateAuthority`. It may create or link records only through a later explicitly authorized execution of canonical commands. Partial workflow remains non-authoritative/quarantined; no Membership becomes active before the entire approved chain is verified.

Administrative actions require a current productive session, explicit administrative capability, authority basis and fresh CSRF. Bootstrap initialization may require a separately controlled out-of-band administrative procedure because no productive session may yet exist; AUTH-PROD-001 must specify and test that ceremony without embedding an evergreen credential.

This section governs `IC-GOVERNANCE-CMD-003`, `IC-GOVERNANCE-QRY-004`, `IC-GOVERNANCE-EVT-002` and constrains orchestration of all assigned Identity/Membership commands.

## 9. Audit, privacy and safe observability

Record a sanitized category and outcome for login initiation/result, binding creation/reuse, session start/revocation, logout, authority denial, bootstrap start/closure, enrollment success/failure, administrative change and OIDC validation failure. Required fields are event type, controlled outcome/reason, opaque actor/aggregate references where lawful, authority basis/receipt reference, correlation/causation, policy/contract version, occurred/recorded timestamps and environment.

Never record tokens, authorization codes, cookies, secrets, PKCE verifier, state, nonce, full claims, provider payload, RFC, full email unless separately justified, full IP when a truncated or rotating keyed representation suffices, free-text provider exception, password or credential. Health and metrics expose only controlled status/counters and no identifiers or PII. Audit access is purpose-bound, least-privilege and itself auditable.

Required audit persistence is part of a state-changing security operation's atomic/durable workflow. If its required audit record cannot be durably produced, binding, Membership, session-start, administrative and bootstrap mutations fail closed. A revocation must prioritize denial immediately and queue only the safe completion evidence through a durable mechanism approved by AUTH-PROD-001; audit outage must never preserve access.

## 10. Retention and disposal

| Data class | Maximum retention / action at expiry |
| --- | --- |
| Active session state | Until expiry/revocation plus a brief implementation-defined technical cleanup window, never usable during that window. |
| Incomplete OIDC attempt | 15 minutes maximum; cryptographic material destroyed. |
| Technical authentication logs | 30 days; delete or irreversibly anonymize. |
| Security and authority audit | 365 days; delete/anonymize only under approved audit policy while preserving required non-PII proof. |
| Bootstrap and Membership-change audit | 365 days. |
| Aggregate metrics without PII | General operational policy; cannot be reidentified. |
| Tokens/secrets/codes/verifiers | Not a documentary retention class; do not retain beyond strictly necessary in-memory protocol use. |

Every purge/anonymization process must be effective, idempotent, auditable and testable by readback. Legal hold, if later required, needs explicit canonical authority, scope, reason, actor, start, review and expiry; this policy creates no hold. A retention conflict or purge failure raises a controlled incident and blocks new bootstrap/administrative provisioning until remediated and reviewed; it cannot silently extend retention. Existing session reads may continue only when authority and security audit controls remain healthy.

## 11. Secrets and environment configuration

Secrets remain outside source, Git, frontend bundles, `VITE_*`, tests, logs, documentation and screenshots. They are injected through a managed secret service or equivalent approved mechanism, support rotation and least-privilege access, and are never returned through health/config endpoints.

Prospective configuration names, not values:

- `YARVIS_AUTH_MODE`
- `YARVIS_OIDC_ISSUER`
- `YARVIS_OIDC_CLIENT_ID`
- `YARVIS_OIDC_CLIENT_SECRET` (secret)
- `YARVIS_OIDC_REDIRECT_URI`
- `YARVIS_OIDC_POST_LOGIN_REDIRECT_ALLOWLIST`
- `YARVIS_OIDC_ALLOWED_ALGORITHMS`
- `YARVIS_SESSION_COOKIE_NAME`
- `YARVIS_SESSION_IDLE_SECONDS`
- `YARVIS_SESSION_ABSOLUTE_SECONDS`
- `YARVIS_SESSION_MAX_ACTIVE`
- `YARVIS_CSRF_ALLOWED_ORIGINS`
- `YARVIS_CORS_ORIGINS` (existing setting; productive validation must be strengthened)
- `YARVIS_BOOTSTRAP_ENABLED`
- `YARVIS_BOOTSTRAP_ALLOWLIST_REFERENCE` (reference, never raw allowlist content)
- `YARVIS_BOOTSTRAP_WINDOW_SECONDS`
- `YARVIS_AUTH_LOGIN_RATE_LIMIT`
- `YARVIS_AUTH_CALLBACK_RATE_LIMIT`
- `YARVIS_BOOTSTRAP_RATE_LIMIT`
- `YARVIS_AUTH_TECHNICAL_RETENTION_DAYS`
- `YARVIS_AUTHORITY_AUDIT_RETENTION_DAYS`

| Environment | Required behavior |
| --- | --- |
| Local | Deterministic helper may exist only under explicit local mode; productive cookies/OIDC/bootstrap disabled unless isolated synthetic conformance explicitly enables them. Loopback CORS allowed. |
| Test | Deterministic fixtures and synthetic OIDC adapter allowed; no real issuer, identity or secret. Policy failures and production rejection paths mandatory. |
| Production | Productive OIDC/session mode only; debug off; HTTPS; exact non-local origins; secure cookie; managed secrets; no deterministic fallback; startup fails on missing/unsafe configuration. |

`VITE_YARVIS_AUTH_TOKEN`, `VITE_YARVIS_SUBJECT`, `VITE_YARVIS_ORGANIZATION_SELECTOR` and `VITE_YARVIS_CAPABILITIES` are prohibited in productive authority resolution and must be absent from productive bundles. Local/test compatibility may remain only behind an environment-impossible production guard. Frontend Organization/capabilities never become authority.

## 12. Incident response, revocation and rollback

Incident triggers include exposed secret/token, unexpected issuer/JWKS, Membership bypass, cross-tenant access, confirmed CSRF, non-revocable session, credential in logs/frontend, reusable bootstrap, normalization collision/drift and loss of audit traceability.

Required response order:

1. disable new productive login and affected issuer;
2. close bootstrap;
3. deny and revoke affected/all sessions;
4. preserve sanitized audit and incident evidence;
5. rotate compromised secrets/keys and invalidate cached metadata where applicable;
6. assess Identity Binding, Membership and tenant impact without destructive reassignment;
7. restore the previously approved API/web artifact if needed;
8. restore database only through approved, tested backup procedure;
9. reconcile restored state against terminal revocations and closures;
10. verify security controls and receive human approval before reopening.

Rollback never enables deterministic authentication in production, never restores revoked authority, never deletes audit silently and never falls back to an unsafe provider. If no safe productive provider exists, the system remains closed. Emergency access requires a future separately governed break-glass procedure; none is created here.

## 13. Normative invariants

1. Authentication is not authorization and never creates Membership.
2. Email is neither canonical identity nor Organization/role evidence.
3. `issuer + normalized_subject` is unique within the governed namespace and provenance policy.
4. No active session exists without an active verified binding, active Principal, required Person link, active Membership, Organization passing activity evaluation and successful authority evaluation.
5. Frontend values never establish Principal, Organization, role or capabilities.
6. Revoked/expired sessions and revoked Memberships never reactivate.
7. Foreign tenant state is concealed and never crosses projections, audit or errors.
8. Required security audit failure blocks new authority-bearing mutations.
9. Bootstrap is disabled by default, single-use, time-bounded and terminally closable.
10. No provider token, secret or raw claim enters canonical contracts, frontend, ordinary logs or Events.

## 14. AUTH-PROD-001 acceptance criteria

AUTH-PROD-001 may close only with reproducible evidence that:

- valid OIDC login uses Authorization Code + PKCE S256 and produces a rotated server-side session;
- invalid issuer, audience, signature, algorithm, timestamps, state, nonce, redirect, callback replay and expired attempt fail closed;
- binding uses unique versioned `issuer + normalized_subject`; collision, legacy ambiguity and unknown issuer fail closed;
- absent/disabled Principal, absent Person link, absent/revoked Membership, inactive Organization, ambiguous/foreign selector and insufficient capability deny without cross-tenant disclosure;
- `EvaluateAuthority` remains final and `AuthorityChanged` invalidates affected sessions;
- session ID has ≥256 bits entropy, only one-way representation persists, idle 30 minutes, absolute 8 hours, cap three and oldest-session revocation are deterministic under concurrency;
- logout, administrative revocation and authority loss deny immediately; expired/revoked sessions never reactivate;
- cookie flags, host/path policy, CSRF, Origin/Referer and exact CORS behavior pass positive and negative tests;
- provider tokens are neither persisted nor exposed; productive frontend contains no `VITE_YARVIS_AUTH_TOKEN` or client authority values;
- rate limits and generic responses resist enumeration;
- audit allowlist/redaction and each retention class pass leakage and expiry/readback tests;
- bootstrap is disabled by default, 24-hour maximum, one-success only, closes automatically/manually, rejects replay and cannot self-assign Organization/role;
- rollback drill disables login, closes bootstrap, revokes sessions, preserves audit and cannot restore revoked authority;
- migration after `20260819_41` passes upgrade → downgrade → upgrade on isolated data and rollback does not erase terminal security evidence;
- D1 and F-011 authority/tenant regressions pass; and
- runtime catalog projection is prospectively reconciled under the implementation gate without altering assigned semantics.

## 15. DEPLOY-PILOT-001 entry criteria

Deployment remains blocked until AUTH-PROD-001 is implemented and independently security-reviewed, plus:

- exact productive issuer/client/redirect/origin configuration is approved without exposing values;
- managed secret injection and rotation drill pass;
- HTTPS/TLS and secure ingress are verified end to end;
- isolated productive PostgreSQL, encrypted backups and tested restore are available;
- rate limiting, monitoring, alerts and sanitized centralized audit are operational;
- retention/purge and incident runbooks are exercised;
- dependency/image/security scans and host hardening pass;
- a synthetic OIDC canary proves login, denial, revocation and rollback;
- a separate administrative bootstrap authorization identifies accountable actors and approved canonical targets; and
- no real operator or Netpay data is used before the deployment/pilot authority explicitly permits it.

## 16. Explicit exclusions and next gate

This policy creates no contract, endpoint, handler, model, schema, migration, configuration value, secret, issuer, client, redirect, cookie, session, Person, Principal, Identity Binding, Membership, Organization assignment, role, bootstrap window, Google resource, deployment or production access. It does not modify D1 or authorize Gmail, OAuth API access, WhatsApp, DNS or push.

The next permitted step requires a new explicit human authorization: `AUTH-PROD-001 — Productive OIDC, Canonical Identity Binding and Server-side Sessions`.
