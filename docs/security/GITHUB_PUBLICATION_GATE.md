# GitHub Publication Gate (Private Repo)

Status: BLOCKED

This gate must be completed before first push, even to a private repository.

## Checklist

- [ ] Working tree reviewed and intentional.
- [ ] Git history scanned for secrets.
- [ ] No secrets detected in tracked files.
- [ ] `.env` ignored.
- [ ] Dumps ignored (`*.dump`, `*.sql`, `*.db`).
- [ ] Backups ignored (`backups/`).
- [ ] Credentials and key files ignored.
- [ ] Repository configured as private.
- [ ] MFA/passkey enabled for GitHub account(s).
- [ ] Secret scanning enabled.
- [ ] Dependabot enabled.
- [ ] Branch protection configured for `main`.
- [ ] Force push to `main` prohibited.
- [ ] Pull request review required before merge.
- [ ] Repository permissions reviewed with least privilege.
- [ ] Remote URL verified before first push.
- [ ] First push reviewed by human confirmation.
- [ ] Local tags reviewed (including architecture-review tag lineage).

## Result

BLOCKED until all checklist items are verified and explicitly approved.
