# Security Baseline — Sprint 6.5

Status: Draft baseline for local development.

## 1. Scope

This baseline applies to the current local-first Yarvis environment in CTO Office:

- local repository;
- local Docker Compose services;
- local PostgreSQL development data;
- local frontend and API runtime.

It does not claim production-grade protection.

## 2. Protected Assets

- Source code and architectural documentation.
- Local Git history and tags.
- PostgreSQL data in the `pgdata` volume.
- Case, intake, evidence, checklist, alert, and event records.
- Local machine and developer session integrity.
- Environment variables and operational credentials.

## 3. Main Threats

- Accidental secret publication in Git.
- Unauthorized local or network access.
- Device loss/theft and session compromise.
- Database corruption or data loss.
- Insecure backups and untested recovery.
- Sensitive data leakage to third-party AI providers.
- Supply-chain compromise through dependencies/images.

## 4. Current Controls (Real, Present-State)

- No remote `origin` configured.
- Repository not published yet.
- `.gitignore` covers `.env`, dumps, backups, credentials, keys, and build artifacts.
- `.env.example` contains local example values and explicit warning comments.
- Docker published ports bound to localhost (`127.0.0.1`) for API, web, and PostgreSQL.
- PostgreSQL data persisted in Docker volume `pgdata`.
- Backup and restore scripts exist for PostgreSQL:
  - `scripts/backup_postgres.ps1`
  - `scripts/restore_postgres.ps1`
- Restore flow requires explicit human confirmation.

## 5. Controls Absent or Incomplete

- No authentication in API yet.
- No authorization/RBAC yet.
- No TLS termination.
- No centralized secret manager.
- No automated backup schedule yet.
- No continuous restore-test automation yet.
- No centralized secure logging platform.
- No formal data retention enforcement mechanism yet.
- No production monitoring/alerting stack yet.

## 6. Secrets Baseline

- No secrets must be committed to Git.
- `.env` files are ignored.
- `.env.example` is allowed and must remain non-sensitive.
- Credentials in local compose are development defaults only.
- Any real provider credential must remain local and outside tracked files.

## 7. Network Baseline

- Services are intended for local development only.
- API: localhost only.
- Frontend: localhost only.
- PostgreSQL: localhost only.
- Because authentication is absent, the stack must not be exposed to the public internet.

## 8. Database Baseline

- PostgreSQL is the source of truth for operational data.
- Volume persistence is enabled (`pgdata`).
- Volume persistence is not a backup.
- Backups must be stored in ignored local directories and verified by restore tests.

## 9. Backup Baseline

- Backups are generated with timestamped UTC filenames.
- Passwords are not hardcoded in scripts.
- Restore requires explicit confirmation.
- A backup is not considered valid until restoration has been tested successfully.

## 10. Workstation Baseline

Current status is unknown until manually verified by the owner:

- BitLocker
- Secure Boot
- TPM
- Windows Hello / passkey
- auto-lock timeout
- Defender/antivirus
- OS update status
- admin/user separation
- recovery key handling
- browser session hygiene
- physical access controls

## 11. GitHub Baseline (Pre-Push)

Before first push to a private repository:

- ensure secret scan of tree and history;
- confirm ignore rules for env, dumps, backups, keys;
- require MFA/passkey;
- enable secret scanning and Dependabot;
- configure branch protection and minimum-review workflow;
- verify least-privilege repo access.

## 12. Dependencies Baseline

- Keep dependency audits non-destructive first.
- Do not auto-apply upgrades/fixes in this sprint.
- Record findings and plan upgrades separately.

## 13. AI and Privacy Baseline

- AI processing policy is mandatory before external provider use.
- Restricted data must not be sent to external AI providers without explicit approved controls.
- Logging must avoid raw sensitive content and credentials.

## 14. Incident Baseline

Use `docs/security/INCIDENT_RESPONSE_MINIMUM.md` for immediate response:

1. contain;
2. revoke;
3. preserve evidence;
4. assess impact;
5. restore;
6. document;
7. prevent recurrence.

## 15. Minimum Criteria Before Any Deployment

All below must be true before deployment is allowed:

- authentication and authorization implemented;
- managed secrets strategy in place;
- TLS and secure ingress configured;
- backup automation and tested restore procedure;
- logging policy enforced with redaction;
- retention policy defined and applied;
- monitoring and alerting active;
- host hardening validated.

## 16. Sprint 6.5 Process Deviation Note

- During Sprint 6.5 execution, backup and restore were executed after a later instruction explicitly prohibited running them.
- No data loss or operational damage was observed.
- This was a process deviation, not a technical requirement.
- The workflow in `docs/engineering/ENGINEERING_WORKFLOW.md` prevents recurrence by enforcing authority precedence, Class C/D execution gates, and explicit prohibition handling.
