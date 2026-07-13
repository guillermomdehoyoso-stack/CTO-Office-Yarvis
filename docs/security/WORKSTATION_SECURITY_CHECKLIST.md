# Workstation Security Checklist (Manual Verification)

Status: Manual checklist. Not automatically verified by Yarvis.

Mark each control only after direct owner verification.

## Device and Boot Security

- [ ] BitLocker enabled on system drive.
- [ ] BitLocker recovery key backed up in a secure location.
- [ ] Secure Boot enabled.
- [ ] TPM enabled and healthy.

## Authentication and Session

- [ ] Windows Hello or strong passkey/PIN configured.
- [ ] Automatic screen lock timeout enabled.
- [ ] Separate non-admin daily account in use.
- [ ] Administrative account reserved for privileged tasks only.

## Endpoint Protection

- [ ] Microsoft Defender or equivalent antivirus active.
- [ ] Real-time protection enabled.
- [ ] Operating system updates current.
- [ ] Browser updates current.

## Development Surface

- [ ] VS Code extensions reviewed; remove unknown/unneeded extensions.
- [ ] Browser session hygiene reviewed (signed-in accounts/dev tokens).
- [ ] Local terminal history does not expose secrets.

## Identity and Account Security

- [ ] MFA/passkey enabled on GitHub account.
- [ ] MFA/passkey enabled on critical email account(s).
- [ ] Recovery methods verified and current.

## Physical Security

- [ ] Device is not left unattended unlocked.
- [ ] Physical access to workstation is controlled.
- [ ] External storage handling follows policy.

## Incident Preparedness

- [ ] Owner reviewed `docs/security/INCIDENT_RESPONSE_MINIMUM.md`.
- [ ] Emergency credential revocation paths known.
- [ ] Backup and restore scripts tested at least once.
