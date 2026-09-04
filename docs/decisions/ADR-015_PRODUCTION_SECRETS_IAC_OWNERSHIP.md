# ADR-015: Production secrets and connection strings must be IaC-driven, not console-edited

- Status: Accepted
- Decision authority: Guillermo, Architecture Authority
- Date: 2026-09-04
- Implementation authorization: `deploy/digitalocean/app.yaml`, `migration-job.yaml`,
  and the `founder-*-job.yaml` templates only — resolve placeholder values,
  enforce VPC-private database hosts, and align them with the live App
  Platform configuration. No other scope (no secrets-manager migration, no
  Terraform/Pulumi adoption, no changes outside `deploy/digitalocean/`) is
  authorized by this ADR.
- Accepted risk: template/live-config reconciliation is done by hand in this
  pass, not enforced by automated drift detection; a follow-on ADR may
  propose that separately.

## Context

The founder-bootstrap production ceremony (`create-first-organization`, migration
apply, `enroll`) was blocked for multiple sessions by connection failures that
turned out to have a single root cause repeated three times: `yarvis-pilot`'s
App Platform component set — the web service, the `yarvis-pilot-migrate`
`PRE_DEPLOY` job, and the founder-bootstrap CLI runtime — each resolve their
own database connection string from a separate environment variable
(`YARVIS_DATABASE_URL`, `YARVIS_MIGRATOR_DATABASE_URL`,
`YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL`). This separation is intentional and
already documented in `deploy/digitalocean/README.md` as a least-privilege
boundary — each runner should receive only the credential it needs.

However, `deploy/digitalocean/app.yaml` and `deploy/digitalocean/migration-job.yaml`
contain unresolved placeholder values (e.g.
`__REQUIRES_MIGRATOR_DATABASE_URL_FOR_YARVIS_MIGRATOR__`). The live App
Platform app was not actually deployed from these templates with resolved
values; its real environment variables were set and later hand-edited directly
in the DigitalOcean Cloud Control Panel over time. As a result:

- All three connection-string variables independently drifted to the
  cluster's public IP/port instead of its VPC-private hostname
  (`private-<cluster>.db.ondigitalocean.com`), which is unreachable from the
  App Platform runtime network path.
- Fixing one variable did not fix the others; each silent failure
  (`server closed the connection unexpectedly`, then a hard `ConnectionTimeout`
  once the public IP itself became stale after a cluster failover) had to be
  discovered independently, by trial and error, across ~2 hours of production
  debugging.
- A `doadmin` password rotation performed mid-session, correctly as a security
  hygiene step, again broke all three variables at once because none of them
  are derived from a single source of truth.
- No document instructed an operator to check all three variables together,
  or to prefer the VPC-private host as a hard requirement.

The underlying failure mode is that the checked-in deployment templates are
not the live configuration's source of truth. Console edits are silent,
untracked, and do not fan out to the other components that share the same
underlying secret.

## Decision

1. `deploy/digitalocean/app.yaml`, `migration-job.yaml`, and the
   `founder-*-job.yaml` templates are the intended source of truth for
   component-level environment variables and must not contain unresolved
   `__REQUIRES_..._` placeholders once an environment is live. Any value that
   cannot be committed in plaintext must be sourced from DigitalOcean's
   `SECRET` env scope and referenced, not filled in by hand later in the
   console with no corresponding template update.
2. Any connection string pointing at the `yarvis-pilot-db` cluster (or any
   future managed database) must use the cluster's **VPC-private hostname**,
   never its public hostname or IP. This applies to all current and future
   per-role database variables (`YARVIS_DATABASE_URL`,
   `YARVIS_MIGRATOR_DATABASE_URL`, `YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL`,
   and any added later).
3. Whenever the underlying database credential (e.g. `doadmin` password) is
   rotated, every environment variable that embeds it must be updated in the
   same change, and that change must be traceable (a deploy log, a commit, or
   an explicit checklist item) — not inferred after the fact from a
   production error.
4. A single operational runbook (see
   [FOUNDER_BOOTSTRAP_OPERATIONAL_RUNBOOK.md](../engineering/FOUNDER_BOOTSTRAP_OPERATIONAL_RUNBOOK.md))
   must enumerate every environment variable a given administrative ceremony
   depends on, so an operator does not have to rediscover them by reading
   tracebacks.

## Consequences

- Console edits to App Platform environment variables become a smell to
  flag in review, not a normal operating procedure; the template files must
  be updated to match, even after the fact.
- Introducing a new database-touching component or job requires explicitly
  documenting which connection-string variable it uses and confirming it
  resolves to the VPC-private host before first deploy, not after a failure.
- This does not mandate a specific secrets manager or Terraform/Pulumi
  adoption; it only requires that the repository's existing YAML templates
  stop drifting from the live configuration. Adopting a dedicated secrets
  manager remains a separately scoped decision.
- TD-004 in `YARVIS_ROADMAP_AND_TECHNICAL_DEBT.md` ("Authentication is
  deterministic and restricted to local/test environments") is superseded by
  this session's evidence: production OIDC login, founder bootstrap,
  `create-first-organization`, and `enroll` all executed successfully against
  the live environment. That debt entry should be closed or rewritten to
  reflect the actual remaining gap, which is configuration governance, not
  authentication capability.

