# Implementation Roadmap Amendment 017

## AUTH-PROD-001 — Productive Authentication and Canonical Operator

## Status

**RATIFIED — ARCHITECTURAL AUTHORITY ONLY**

This ratified amendment is architectural authority only. It does not authorize code,
catalog changes, migrations, OIDC configuration, Google resources, credentials,
production access, identity provisioning, deployment, or modification of
`apps/api/src/yarvis_api/api/authentication.py`.

## 1. Basis and bounded purpose

| Field | Value |
| --- | --- |
| Branch | `feat/operational-intake-spine` |
| Design base | `6bb2c412232f84b0df516dd5da60af354a3f3d85` |
| D1 authorization | `8277bcccd9f0af013d7096ae76003fd8ebdb32a7` |
| D1 implementation | `6bb2c412232f84b0df516dd5da60af354a3f3d85` |
| D1 migration head | `20260819_41` |

The proposed package removes three blockers for a later restricted Netpay
pilot: no productive identity provider, no proven canonical
`Person → Principal → Membership` chain for the operator, and use of
`VITE_YARVIS_AUTH_TOKEN` by the local/test frontend.

The package is core identity/governance infrastructure. It is not owned by
Netpay and must remain reusable by other Organizations and verticals. Netpay is
only the first bounded consumer through an explicitly active Membership in the
canonical Organization `Distribución Netpay`.

## 2. Relationship to existing authority

This proposal conforms prospectively to the Constitution, F-011 Identity and
Authority Envelopes, ADR-014, and the reviewed Canonical Identity Provisioning
Foundation design. It does not reinterpret their current non-authority clauses.

F-011 and ADR-014 currently exclude SSO/OAuth and external-identity runtime.
The provisioning foundation remains proposed design only. Human ratification
of this amendment is recorded in Section 13; a separate catalog step and a
separate implementation gate are still required.

## 3. Proposed OIDC boundary

The productive authentication protocol is standard OpenID Connect using
Authorization Code Flow and PKCE where applicable. The implementation must be
provider-neutral and initially interoperable with Google.

The backend, never the browser, must:

- discover or use explicitly configured allowlisted provider metadata;
- validate issuer, audience, signature, timestamps, authorization response
  state, and nonce;
- validate callback and post-login redirects against closed allowlists;
- exchange the authorization code without exposing provider tokens;
- discard or protect provider credentials according to an approved lifecycle;
- resolve the canonical authority chain; and
- return only a server-managed Yarvis session to the browser.

No ID token, access token, refresh token, authorization code, client secret,
raw claim set, or provider response may be sent to frontend code, HTML, source
maps, application events, health responses, or ordinary logs.

## 4. Proposed canonical identity model

Productive resolution is:

```text
OIDC issuer + subject
  → active Identity Binding
  → active Principal
  → exactly one canonical Person for a human Principal
  → active PrincipalMembership
  → Organization passing the existing activity evaluation
  → closed server-side role/capability matrix
  → evaluated authority envelope
```

Rules:

1. `issuer + normalized_subject` is the external identity key. Email is never
   a primary key, Membership proof, Organization authority, or role source.
2. A verified email may be used only as evidence in a separately authorized,
   allowlisted bootstrap workflow.
3. Unknown issuer, invalid provenance, ambiguous binding, disabled Principal,
   missing Person link, absent/revoked Membership, inactive Organization, or
   insufficient capability fails closed.
4. The client may request an Organization selector, but the server derives and
   validates `organization_id` from persisted Membership. D1 never trusts a
   frontend Organization value as authority.
5. Cross-tenant resources remain concealed using existing F-011 patterns.
6. Authentication never creates Membership or elevates a role automatically.

The future schema may add an issuer registry, identity bindings, sessions,
bootstrap receipts, and narrowly allowlisted audit records. It must not store
raw OIDC tokens or complete claim sets. Any migration must be new, reversible,
and based on `20260819_41`; ratified migrations remain immutable.

## 5. Proposed server-managed session

The minimum productive surface is:

- `GET /auth/login`;
- `GET /auth/callback`;
- `GET /auth/session`;
- `POST /auth/logout`.

A successful callback must rotate or regenerate the Yarvis session. Sessions
must have server-side revocation, absolute expiry, inactivity expiry, logout,
and fail-closed authority revalidation. The browser receives only an opaque
cookie with `HttpOnly`, `Secure`, and an explicitly ratified `SameSite` policy.

Every mutating request must use a server-validated CSRF control compatible with
the selected cookie policy. Logout, expired/revoked sessions, invalid CSRF,
invalid redirect, repeated callback, or changed authority must produce safe,
controlled errors without tokens, claims, PII, or provider exceptions.

The session read model may expose only:

- authenticated status;
- minimal display name;
- active Organization display label and opaque canonical reference; and
- the minimum capabilities needed to render allowed navigation.

## 6. Frontend secret removal

Productive frontend code must not consume `VITE_YARVIS_AUTH_TOKEN`, a provider
token, client secret, bearer credential, or equivalent build-time secret.
Authentication uses the backend session cookie and CSRF mechanism only.

A deterministic local/test helper may remain only when all of these hold:

- it is impossible to enable in `production`;
- it uses explicit local/test configuration;
- it shares no productive secret path with frontend code;
- it cannot derive authority from client-declared roles or capabilities; and
- tests demonstrate production fail-closed behavior.

## 7. Proposed administrative bootstrap

Bootstrap is a future administrative workflow, not part of interactive login.
It must be explicit, idempotent, auditable, time-bounded, and closed after the
initial operator is established.

The authorized administrator would later:

1. configure an allowlisted OIDC issuer and client outside source control;
2. add a verified identity to an external administrative allowlist without
   hardcoding name, email, subject, UUID, or Organization ID;
3. create or resolve one canonical Person under human review;
4. create or bind one Principal through verified `issuer + subject`;
5. verify the target Organization is canonically `Distribución Netpay`;
6. create an active Membership through separate Governance authority;
7. assign only the existing role/capabilities required for D1;
8. verify productive login and D1 denial/allowance boundaries; and
9. expire or close the bootstrap mechanism and preserve its audit receipt.

No bootstrap, Person, Principal, Identity Binding, Membership, role, issuer,
allowlist entry, or credential is created by this amendment.

## 8. Proposed contracts; pending canonical assignment

The following semantic contracts are proposed without IDs, registration,
dispatchability, ownership allocation, or present authority:

### Commands

- Start OIDC Login;
- Complete OIDC Callback;
- Logout Productive Session;
- Revoke Productive Session;
- Register OIDC Issuer Policy;
- Bind Verified External Identity;
- Complete Allowlisted Operator Bootstrap.

### Queries

- Get Productive Session;
- Resolve External Identity Authority;
- List Active Sessions for Administrative Review;
- Get Bootstrap Status.

### Events

- Productive Login Succeeded;
- Productive Login Denied;
- Productive Session Revoked;
- Productive Logout Completed;
- External Identity Bound;
- Operator Bootstrap Completed or Failed.

Catalog authority must assign only demonstrated-free IDs in a later, separate
step. This amendment does not alter the canonical catalog.

## 9. Mandatory validation for a future implementation gate

The future gate must prove at least:

- valid login and safe callback;
- invalid issuer, audience, signature, state, nonce, redirect, and repeated
  callback fail closed;
- no Membership, revoked Membership, wrong Organization, and insufficient
  capability are denied;
- session absolute/inactivity expiry, revocation, logout, and CSRF enforcement;
- production cookies have all ratified flags;
- deterministic authentication is impossible in production;
- no tokens or secrets occur in frontend bundles, source maps, logs, errors,
  events, health, or API responses;
- D1 derives Organization from the evaluated session and preserves tenant
  isolation;
- D1 and existing authority regressions pass;
- any migration passes upgrade → downgrade → upgrade on an isolated database;
  and
- an administrative dry-run proves idempotent bootstrap without executing it
  against a real identity.

## 10. Mandatory sequence

No step authorizes a later step:

1. human ratification of Amendment 017 (completed 2026-08-20);
2. canonical contract allocation under separate authority;
3. approval of issuer policy, session policy, CSRF policy, cookie policy,
   retention, audit allowlists, bootstrap duration, and rollback;
4. independent AUTH-PROD-001 implementation gate with branch/base, migration,
   tests, and rollback boundaries;
5. security review and synthetic OIDC conformance evidence;
6. separate administrative bootstrap authorization for a real operator;
7. closure of bootstrap and evidence of canonical Membership/capabilities; and
8. `DEPLOY-PILOT-001` for infrastructure, HTTPS, isolated PostgreSQL,
   backups/restore, rate limiting, observability, immutable deployment, and a
   real canary.

## 11. Rollback and revocation

Before implementation, withdrawal has no runtime effect. A future runtime must
support: global issuer disablement, session revocation, bootstrap closure,
binding suspension without destructive reassignment, Membership revocation,
and fail-closed rollback to no productive login. Database rollback must never
restore revoked authority or delete audit evidence silently.

## 12. Explicit non-effects

This proposal does not:

- implement or configure OIDC, Google, OAuth consent, PKCE, sessions, cookies,
  CSRF, issuer discovery, redirect URIs, credentials, or secrets;
- modify code, frontend bundles, `authentication.py`, D1, the catalog,
  contracts, roles, configuration, or migrations;
- create or infer Person, Principal, Identity Binding, Membership, issuer,
  subject, Organization, capability, or role;
- authorize Gmail, Google APIs, WhatsApp, Store 360, Logistics, hosting, DNS,
  HTTPS, deployment, production PostgreSQL, or real data; or
- constitute AUTH-PROD-001 implementation authority or `DEPLOY-PILOT-001`.

No authority arises implicitly from an email, OIDC claim, client selector,
frontend capability, proposed contract name, this proposal, or the requesting
human's identity.

## 13. Human ratification record

| Field | Value |
| --- | --- |
| Decision | `RATIFIED — ARCHITECTURAL AUTHORITY ONLY` |
| Ratified by | Human Architecture Authority (user-confirmed) |
| Ratified at | 2026-08-20 America/Mexico_City |
| Effective commit | Documentary commit containing this ratification record; see Git history. |
