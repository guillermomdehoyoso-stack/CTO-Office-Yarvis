# F-011 Identity and Authority Envelopes Architecture Amendment 003

## Status

**RATIFIED — E/F ATOMIC TENANCY TRANSITION — NO ADDITIONAL RADAR CAPABILITY**

**Date:** 2026-08-06
**Authority:** Guillermo de Hoyos, Architecture Authority

## 1. Corrected Execution Conflict

E requires Radar reads filtered exclusively by canonical `organization_id`.
Legacy Radar commands create `RadarMerchant`, `RadarRequest` and
`RadarActivity` with only `workspace_id`; consequently E correctly hid their
new output and the affected Radar regression failed six times. E cannot preserve
the existing Radar journey while the minimum tenancy persistence in F is closed.

## 2. Narrow Atomic Authorization

E is authorized together with only the F slice required to make existing Radar
commands persist the server-resolved active Membership Organization. Commands
must ignore client organization, workspace, role, permissions, actor and
authority as authority inputs; enforce same-Organization related references;
and conceal foreign resources as `not found`. `X-Yarvis-Workspace` may remain
only as non-authoritative compatibility data and may not select or contradict
the canonical Organization.

This does not close F. All other F criteria remain independent and pending.
No G backfill, final cutover/constraints, H header removal, new Radar feature,
BACKLOG item, integration, automation or successor package is authorized.

## 3. Model and Historical Disposition

Nullable `organization_id` FK/index fields may be added to the three Radar
tables without default, backfill or NOT NULL enforcement. New canonical commands
must always populate them. Cross-Organization merchant/request/activity links
must be rejected transactionally.

| workspace_id | records | disposition |
| --- | ---: | --- |
| `manual-close-validation` | 11 | Retain unchanged, unlinked and invisible to canonical authority. |
| `netpay-demo` | 51 | Retain unchanged, unlinked and invisible to canonical authority. |

Neither row set may receive an Organization, Principal, Membership, mapping or
inferred authority. Future inclusion requires an explicit authoritative mapping,
approved preflight and separately authorized backfill/cutover.

## 4. Completion Gate

E is green only when canonical commands produce immediately readable records;
foreign reads and related references return concealed `404`; revoked Membership
fails on the next request; excluded rows remain intact/invisible; the affected
Radar regression is green; and migration round-trip, Docker, compile, Markdown
and diff checks pass.
