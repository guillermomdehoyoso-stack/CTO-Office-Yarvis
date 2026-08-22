# DigitalOcean App Platform restricted pilot

This package is local preparation only. It neither creates a DigitalOcean app
nor configures Google Workspace OIDC, a database, secrets, DNS, or a callback.

## Runtime

`app.yaml` defines exactly one HTTP service, `yarvis-pilot`, built from the
repository Dockerfile. It listens on port 8080 and checks `/health`. It has one
instance and does not deploy on push. The runtime receives `YARVIS_DATABASE_URL`
and never receives `YARVIS_MIGRATOR_DATABASE_URL`.

Set the App Platform region only when an approved Managed PostgreSQL cluster
exists; the region must match that cluster. The App Platform service needs the
runtime PostgreSQL URL for `yarvis_app`, with TLS settings supplied by the
managed-database connection string.

## Migration

`migration-job.yaml` is deliberately separate from `app.yaml`. It receives only
`YARVIS_MIGRATOR_DATABASE_URL`, intended for `yarvis_migrator`, and executes
`alembic upgrade head`. It must be applied only under a separate human migration
authorization.

App Platform documents only deployment-time and scheduled jobs. Its documented
`PRE_DEPLOY` mode runs on each application deployment, so it is intentionally
not used by the runtime app. The documented spec exposes no explicit
no-retry setting for a job; platform retry behavior is therefore not determined
by this repository. No retry loop exists in this package.

## OIDC and secret boundary

All `__REQUIRES_*__` markers are intentional placeholders, not values to
deploy. Once App Platform assigns its managed `*.ondigitalocean.app` subdomain,
register that exact HTTPS callback with Google Workspace and use the same exact
origin for CORS and CSRF. Do not substitute an invented callback URL.

Create encrypted, component-scoped runtime values for the database URL, OIDC
client secret, and attempt-encryption key. Create the migrator URL only in the
separate migration component. `pilot.env.example` is a name-only inventory and
must not be used as a secret file.

No Cloud Storage or other persistent XLSX store is configured. D1 retains its
existing process-and-discard behavior.
