# AUTH-PROD-001 operational runbook

## Status and boundary

This runbook describes the implemented productive authentication capability. It
does not configure a provider, create secrets, open bootstrap, provision an
identity or Membership, deploy Yarvis, or authorize production traffic. Those
effects remain closed until `DEPLOY-PILOT-001` and its separate administrative
authorization.

## Configuration names

Production must resolve these names from an approved secret/configuration
manager; this repository contains no values:

- `YARVIS_AUTH_MODE`
- `YARVIS_OIDC_ISSUER`
- `YARVIS_OIDC_CLIENT_ID`
- `YARVIS_OIDC_CLIENT_SECRET`
- `YARVIS_OIDC_ATTEMPT_ENCRYPTION_KEY`
- `YARVIS_OIDC_REDIRECT_URI`
- `YARVIS_OIDC_POST_LOGIN_REDIRECT_ALLOWLIST`
- `YARVIS_OIDC_ALLOWED_ALGORITHMS`
- `YARVIS_SESSION_COOKIE_NAME`
- `YARVIS_SESSION_IDLE_SECONDS`
- `YARVIS_SESSION_ABSOLUTE_SECONDS`
- `YARVIS_SESSION_MAX_ACTIVE`
- `YARVIS_CSRF_ALLOWED_ORIGINS`
- `YARVIS_CORS_ORIGINS`
- `YARVIS_BOOTSTRAP_ENABLED`
- `YARVIS_BOOTSTRAP_WINDOW_SECONDS`
- `YARVIS_AUTH_RATE_LIMIT_BACKEND`
- `YARVIS_AUTH_DEPLOYMENT_REPLICAS`
- `YARVIS_AUTH_CLEANUP_SESSION_RETENTION_DAYS`

Production validation fails closed for incomplete OIDC configuration, insecure
issuer/callback URLs, local or wildcard CORS, a non-`__Host-` cookie, policy
duration drift, or a multi-replica topology without a shared rate-limit backend.
The current composition intentionally refuses the `shared` backend until
`DEPLOY-PILOT-001` supplies and wires approved shared infrastructure.

## Runtime behavior

`GET /auth/login` starts Authorization Code Flow with PKCE S256 and a one-use,
ten-minute attempt. The provider callback uses `form_post`, preventing the code
from entering the request URL. `POST /auth/callback` validates the configured
issuer, discovery endpoints, allowlisted algorithm, JWKS signature, audience,
timestamps, state and nonce; it requests only `openid` and stores no provider
token or claims payload.

Successful resolution requires an active `issuer + normalized_subject` binding,
an active human Principal linked to Person, exactly one effective active
Membership, an active Organization and a closed persisted role. It creates a
hashed server-side session and a session-bound CSRF token. D1 authority is always
evaluated by the backend. `GET /auth/session` returns only the Organization label,
minimal capabilities and expiry. `POST /auth/logout` is CSRF-protected,
idempotent and terminal.

The deterministic header adapter remains available only when environment is
`local` or `test` and auth mode is `deterministic`. Production startup requires
OIDC. No productive Vite bundle reads or embeds `VITE_YARVIS_AUTH_TOKEN`.

## Bootstrap and cleanup

Bootstrap is disabled by default and has no web endpoint. The application
service accepts only an externally authorized window and allowlist evidence,
never frontend Organization, role or capability values. It is one-success,
terminal, idempotent and bounded to the ratified 24-hour maximum. Creating or
opening a real window and executing its canonical commands requires a later
administrative authorization.

When that authorization is active, the non-HTTP administrative entry point is
`python -m yarvis_api.founder_bootstrap_cli enroll --authorization-file <secure-temporary-file>`.
The signed authorization is the sole command input: it carries the opaque
handoff reference and idempotency key, so the CLI accepts no separate subject,
email, Organization, role, handoff or identity identifiers. The file must stay
outside the repository and be removed through the approved operational process
after use. The command prints only a stable completion or error code.

Before authorization is signed, the production-only, read-only command
`python -m yarvis_api.founder_bootstrap_cli select-handoff` may return exactly
one eligible opaque handoff reference. It selects only a current, unconsumed,
issuer-matching handoff with explicit `founder_bootstrap` provenance and no
completed enrollment. It prints only `founder_bootstrap_handoff_id=<opaque-id>`
and fails closed on zero or multiple candidates. It neither creates nor opens a
BootstrapWindow, and it does not consume or reserve the handoff.

### Founder ceremony procedure

The following is a manual, separately authorized procedure. No component
executes these steps automatically, and this runbook does not itself authorize
any login, deployment, signing, enrollment, or identity creation.

1. Temporarily enable the bootstrap flow only under the applicable ceremony
   authorization so one verified OIDC identity handoff can be recorded.
2. Complete exactly one approved Google login through the normal productive
   flow.
3. Immediately return the runtime bootstrap flow to its disabled state before
   any selector component is created or run.
4. Create the separate, one-shot `yarvis-pilot-founder-select-handoff` Job and
   execute its sole command: `python -m yarvis_api.founder_bootstrap_cli
   select-handoff`.
5. Remove the selector Job immediately after its single execution. Its only
   successful output is the opaque `founder_bootstrap_handoff_id` reference.
6. An external, offline signer prepares the Founder authorization from that
   opaque reference; the signer, private key, signature, and authorization
   material never enter the selector, runtime, or repository.
7. Under the separately authorized enrollment ceremony, create and run the
   distinct `yarvis-pilot-founder-enroll` Job once.
8. Verify only stable, sanitized completion and health evidence; do not expose
   identity, OIDC, signature, or secret material.
9. Remove the enrollment Job, its temporary variables, and all temporary
   ceremony material through the approved operational process.

The runtime web service, Alembic migrator, handoff selector, offline signer,
and enrollment runner remain separate components with separate credentials and
purposes.

`ProductiveAuthCleanupService` is the idempotent command surface for expired
OIDC-attempt and terminal-session cleanup. AUTH-PROD-001 installs no scheduler.
`DEPLOY-PILOT-001` must supply scheduling, retention readback, monitoring and
incident procedures before restricted canary traffic.

## Deployment and rollback checks

Before a canary, verify migration head `20260820_42`, exact CORS/CSRF origins,
secure cookie attributes, provider metadata/JWKS reachability, shared rate
limiting when replicas exceed one, centralized sanitized audit, cleanup
scheduling, PostgreSQL backups and restore reconciliation. Confirm no token,
code, cookie, state, nonce, PKCE verifier, raw claims, RFC or unnecessary PII is
present in frontend assets, logs, events or metrics.

Rollback order is: stop new login, close bootstrap, revoke productive sessions,
preserve security audit, roll back application release, and reconcile canonical
Membership/binding/session state after restore. A restore must never reactivate
revoked authority automatically.
