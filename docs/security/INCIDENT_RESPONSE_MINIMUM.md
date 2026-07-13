# Incident Response Minimum

Status: Minimum actionable procedure for current stage.

## 1. Scope

This playbook covers immediate response to incidents in local-first Yarvis development:

- exposed secret;
- lost or stolen device;
- compromised GitHub account;
- corrupted database;
- ransomware indicator;
- file sent by mistake to an AI provider;
- unauthorized access.

## 2. Standard Response Sequence

1. Contain
2. Revoke
3. Preserve evidence
4. Assess impact
5. Restore
6. Document
7. Prevent recurrence

## 3. Scenario Actions

### A. Secret Exposed

- Contain: stop propagation; remove access paths.
- Revoke: rotate affected credential(s).
- Preserve evidence: collect commit IDs/log references.
- Assess impact: where used, who had access, time window.
- Restore: reconfigure affected services with new credentials.
- Document: incident timeline and affected assets.
- Prevent recurrence: add detection and handling controls.

### B. Lost or Stolen Device

- Contain: revoke sessions/tokens and remote access.
- Revoke: invalidate credentials reachable from that device.
- Preserve evidence: timestamp, known location, account activity.
- Assess impact: local data exposure and account risk.
- Restore: move operations to trusted device.
- Document: incident report and actions taken.
- Prevent recurrence: improve device hardening and lock policy.

### C. Compromised GitHub Account

- Contain: lock account sessions immediately.
- Revoke: regenerate PATs/SSH keys and remove unknown keys.
- Preserve evidence: login events, suspicious actions, changed settings.
- Assess impact: repos, settings, secrets, collaborators.
- Restore: recover account and enforce stronger MFA/passkey.
- Document: incident scope and recovery proof.
- Prevent recurrence: least privilege, token hygiene, periodic review.

### D. Corrupted Database

- Contain: stop writes if corruption is active.
- Revoke: N/A unless compromise is suspected.
- Preserve evidence: logs, failing queries, timestamps.
- Assess impact: affected tables and data windows.
- Restore: restore from the latest valid backup into a safe target.
- Document: root-cause hypothesis and recovery steps.
- Prevent recurrence: backup/restore tests and integrity checks.

### E. Ransomware

- Contain: isolate host and disconnect external shares.
- Revoke: rotate credentials that may be exposed.
- Preserve evidence: encrypted file samples, notes, logs.
- Assess impact: systems/data affected and lateral movement risk.
- Restore: recover from known-good backups on clean environment.
- Document: incident chain and decision log.
- Prevent recurrence: patching, hardening, segmentation.

### F. File Sent by Error to AI Provider

- Contain: stop further uploads immediately.
- Revoke: disable affected provider keys if needed.
- Preserve evidence: what file/class, when, provider endpoint.
- Assess impact: data class and contractual/privacy implications.
- Restore: move process to compliant flow.
- Document: incident and notifications required.
- Prevent recurrence: policy gating and data-class checks.

### G. Unauthorized Access

- Contain: block access path and isolate affected endpoint.
- Revoke: reset credentials and sessions.
- Preserve evidence: access logs and timeline.
- Assess impact: data accessed/modified.
- Restore: recover integrity from validated state.
- Document: who, what, when, how.
- Prevent recurrence: tighten authz/authn and monitoring.

## 4. Evidence Minimum

Keep at least:

- timestamped timeline;
- affected systems/data classes;
- credential/session actions;
- restoration evidence;
- final corrective actions.
