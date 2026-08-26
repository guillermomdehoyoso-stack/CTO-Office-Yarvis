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

## Founder Enrollment runner

`founder-enrollment-job.yaml` is a third, separate App Platform component. It
is neither part of `yarvis-pilot` nor `yarvis-pilot-migrate`; its
`deploy_on_push` setting is `false`, so a runtime deployment cannot start it.
It is an intentionally one-shot administrative runner: create or deploy this
component only under a ceremony authorization, wait for its single Job result,
then delete the component and its component-scoped encrypted secrets.

`yarvis-pilot` retains Founder Bootstrap disabled by default. The separate Job
has no committed enabled value: its single-run enablement is an encrypted,
component-scoped input that must be set only for the authorized Job execution.

The runner receives only `YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL`, a dedicated
least-privilege administrative PostgreSQL credential. It never receives
`YARVIS_DATABASE_URL` or `YARVIS_MIGRATOR_DATABASE_URL`. The signed
authorization, founder public key, key identifier, and the productive OIDC
configuration required for fail-closed startup are component-scoped encrypted
secrets. No private founder key is configured, copied, or stored by this
package.

The Job creates a mode-0600 authorization file in its ephemeral filesystem,
invokes exactly `python -m yarvis_api.founder_bootstrap_cli enroll
--authorization-file <temporary-file>`, unsets the authorization environment
variable, and removes the file on every shell exit path. Do not enable shell
tracing or copy Job logs outside the approved sanitized operational record.
App Platform's retry semantics and physical media erasure guarantees are not
determined by this repository; the component must be deleted after its result,
and the signed authorization and handoff remain independently single-use.

## Founder Organization selector

`founder-organization-selector-job.yaml` is a fourth, separate and one-shot
App Platform component. It runs only `python -m yarvis_api.founder_bootstrap_cli
select-organization`; it cannot enroll, create a BootstrapWindow, or select a
handoff. `deploy_on_push` is `false`.

Create it only under a dedicated ceremony authorization, supply only
`YARVIS_ENVIRONMENT`, `YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL`, and
`YARVIS_OIDC_ISSUER` as component-scoped values, run it once, capture only its
sanitized result, and delete the component and its administrative credential
immediately. The expected successful output is exactly
`founder_bootstrap_organization_id=<opaque-id>`. Zero or multiple active
Organizations fail closed with a stable code and no Organization name. It never
receives `YARVIS_DATABASE_URL`, `YARVIS_MIGRATOR_DATABASE_URL`, enrollment
authorization, founder keys, or runtime OIDC client credentials.

## First Organization runner

`founder-first-organization-job.yaml` is a separate one-shot component for
`IC-GOVERNANCE-CMD-006 CreateFirstOrganization`. It is not the runtime,
migrator, selector, or enrollment runner, and `deploy_on_push` is `false`.
Create it only after migration `20260823_47`, execute it once with its
component-scoped values, then delete the component and all temporary values.
It never receives `YARVIS_DATABASE_URL` or `YARVIS_MIGRATOR_DATABASE_URL`.

The authorization is written to a mode-0600 temporary file, unset from the
environment, and removed on every shell exit path. Successful CLI output is
only `founder_bootstrap_first_organization_created status=created` or
`status=replayed`.

The dedicated Founder administrative role needs `CONNECT` on the target
database; `USAGE` on schema `public`; `SELECT, INSERT` on
`public.organizations`, `public.first_organization_receipts`,
`public.authentication_security_audit`, and `public.domain_events`; and
`USAGE` on `public.domain_events_event_sequence_seq`. It needs no `UPDATE`,
`DELETE`, `CREATE`, rights on identity/Membership tables, or runtime/migrator
credentials. These are proposed grants only; their execution and exact role
name require separate human infrastructure authorization.

```sql
GRANT CONNECT ON DATABASE yarvis TO <founder_admin_role>;
GRANT USAGE ON SCHEMA public TO <founder_admin_role>;
GRANT SELECT, INSERT ON TABLE public.organizations,
  public.first_organization_receipts,
  public.authentication_security_audit,
  public.domain_events TO <founder_admin_role>;
GRANT USAGE ON SEQUENCE public.domain_events_event_sequence_seq TO <founder_admin_role>;
```
