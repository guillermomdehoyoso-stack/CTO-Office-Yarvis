# Founder bootstrap operational runbook

## Status and boundary

This runbook documents the founder-bootstrap ceremony as it was actually
executed against the live `yarvis-pilot` App Platform deployment on
2026-09-03/04: creating the first Organization, then enrolling the founder
Principal. It supersedes tribal knowledge with a reproducible procedure. It
does not create new authorization — `create-first-organization` and `enroll`
remain gated exactly as implemented in `founder_bootstrap_cli.py`,
`services/first_organization.py`, and `services/founder_bootstrap.py`.

See [ADR-015](../decisions/ADR-015_PRODUCTION_SECRETS_IAC_OWNERSHIP.md) for
the configuration-governance decision this runbook depends on.

## Prerequisites — configuration names

Before starting, confirm each of these App Platform environment variables is
set **and resolves to the cluster's VPC-private hostname**
(`private-<cluster-name>.<...>.db.ondigitalocean.com`), never the public
hostname or a raw public IP:

| Variable | Component | Purpose |
| --- | --- | --- |
| `YARVIS_DATABASE_URL` | `yarvis-pilot` (web service) | General app runtime DB access |
| `YARVIS_MIGRATOR_DATABASE_URL` | `yarvis-pilot-migrate` (`PRE_DEPLOY` job) | Runs `alembic upgrade head` |
| `YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL` | `yarvis-pilot` console / CLI | Used by `create-first-organization`, `select-handoff`, `select-organization` |
| `YARVIS_FOUNDER_BOOTSTRAP_ENABLED` | `yarvis-pilot` | Must be `true` |
| `YARVIS_FOUNDER_BOOTSTRAP_PUBLIC_KEY` | `yarvis-pilot` | Base64 raw Ed25519 public key (32 bytes decoded) |
| `YARVIS_FOUNDER_BOOTSTRAP_KEY_ID` | `yarvis-pilot` | Must match the `key_id` used when signing |
| `YARVIS_OIDC_ISSUER` | `yarvis-pilot` | Must be an HTTPS issuer; used by the handoff selector |

If any of these still contain a stale public host or an outdated `doadmin`
password after a rotation, every step below will fail with either
`psycopg.OperationalError: connection failed` (stale IP, connection refused
or reset) or `password authentication failed` (rotated credential, not yet
propagated to all three variables).

**Migration check before doing anything else:** confirm the database schema
is current. From the `yarvis-pilot` console:

```
PYTHONPATH=/app/src python -m alembic -c /app/alembic.ini current
```

The output must show the repository's current alembic head revision. If it
does not, trigger a plain "Deploy" (not just a rebuild) on the app so the
`PRE_DEPLOY` migration job re-runs; `alembic upgrade head` does not run
automatically on every deploy for this app (`deploy_on_push: false` on the
job template), and `Force rebuild and deploy` alone does not guarantee the
job re-executes against a corrected `YARVIS_MIGRATOR_DATABASE_URL` unless a
new deploy is explicitly triggered after the variable is fixed.

## The signing key

`create-first-organization` and `enroll` both require a JSON envelope
(`{"payload": {...}, "signature": "<base64>"}`) signed with an Ed25519
private key whose public counterpart is configured in
`YARVIS_FOUNDER_BOOTSTRAP_PUBLIC_KEY`. As of this session, no private key
existed anywhere retrievable — it had never been generated and saved. A new
keypair was generated from the `yarvis-pilot` console, the public half was
written into `YARVIS_FOUNDER_BOOTSTRAP_PUBLIC_KEY`, and the private half was
saved to a password manager as "Yarvis founder bootstrap Ed25519 private
key". **That private key is a durable production secret now.** It is
required for every future signed founder-bootstrap operation against this
key_id, not just this one ceremony. It must never be pasted into chat tools,
tickets, or any non-secret-manager surface.

App Platform console sessions are ephemeral: any redeploy replaces the pod
and wipes `/tmp`. Expect to re-materialize the key from the password manager
into `/tmp/founder_private.b64` after every redeploy triggered mid-ceremony.

## Step 1 — create the first Organization

From the `yarvis-pilot` console, materialize the private key and sign a
`create_first_organization` authorization (valid 5 minutes; the service
rejects a payload whose `expires_at - issued_at` exceeds 600 seconds):

```
echo '<PRIVATE_KEY_B64>' > /tmp/founder_private.b64
```

Sign and run `create-first-organization` immediately (the payload's ratified
field values — `legal_name`, `display_name`, `organization_type`, `status`
— are fixed in `services/first_organization.py` and must match exactly):

```
PYTHONPATH=/app/src python -m yarvis_api.founder_bootstrap_cli \
  create-first-organization --authorization-file /tmp/auth.json
```

Expected success output: `founder_bootstrap_first_organization_created status=created`.
Re-running with the same signed envelope is idempotent (`status=replayed`);
re-running with a fresh envelope after an Organization already exists fails
closed with `CONFLICT`.

## Step 2 — create a fresh OIDC handoff

`enroll` requires a `BootstrapVerifiedIdentity` ("handoff") record, which is
only created as a side effect of a real OIDC login attempt while
`bootstrap_enabled` is true (`api/routes/auth.py::callback`). It expires
**10 minutes** after creation.

1. Visit `https://<live-app-host>/auth/login` in a browser and complete
   Google sign-in with the founder's account.
2. The callback will correctly fail closed with
   `{"code":"AUTHORIZATION_DENIED", ..., "reason":"binding_not_found"}` —
   this is expected and confirms the handoff was recorded, not an error to
   chase.
3. Immediately (within the 10-minute window), from the console:

```
PYTHONPATH=/app/src python -m yarvis_api.founder_bootstrap_cli select-handoff
PYTHONPATH=/app/src python -m yarvis_api.founder_bootstrap_cli select-organization
```

Record both printed UUIDs (`founder_bootstrap_handoff_id`,
`founder_bootstrap_organization_id`).

## Step 3 — enroll the founder

Sign a second envelope, this time with `purpose: founder_bootstrap`,
`role: netpay_operations_operator`, and the two UUIDs from Step 2 (again, a
5-minute validity window):

```
PYTHONPATH=/app/src python -m yarvis_api.founder_bootstrap_cli \
  enroll --authorization-file /tmp/auth.json
```

### Known non-blocking defect

`founder_bootstrap_cli.py::main()` accesses `receipt.outcome` in the
`enroll` branch **after** the database session context manager has already
closed. Because `Session.commit()` expires ORM instance attributes by
default, this raises `sqlalchemy.orm.exc.DetachedInstanceError` on every
successful `enroll` call, even though the commit that matters already
succeeded before the session closed. **Do not treat this traceback as a
failed enrollment.** Verify success by repeating the OIDC login
(`/auth/login`) — a successful enrollment resolves normally instead of
returning `binding_not_found`. This should be filed and fixed
(the `receipt` should be re-read or its needed attribute captured before the
`with` block exits, or `expire_on_commit=False` should be set for this
session), but it does not require re-running the ceremony.

## Post-ceremony

- Rotate any credential that was displayed on screen during the session
  (e.g. `doadmin`), and update all three database connection-string
  variables together per ADR-015.
- Confirm founder access by loading an authenticated route
  (e.g. `/netpay-inbox`) and observing the resolved Organization name.


