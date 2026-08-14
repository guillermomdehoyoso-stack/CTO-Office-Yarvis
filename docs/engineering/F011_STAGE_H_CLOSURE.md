# F-011 Stage H Closure

## Status

**H COMPLETE — VALIDATED**

## Scope and decision

Stage H retired the legacy `X-Yarvis-Workspace` input from new Radar
operations. Commit `01f3445` removes the required header from `POST
/radar/merchants` and `POST /radar/requests`, from generated OpenAPI, and from
the Operational Radar web client. A supplied legacy header is ignored and does
not affect authority, organization, idempotency, fingerprint, replay, or the
response.

Authority and tenancy remain derived exclusively through
`AuthorityResolutionService`: Principal, active PrincipalMembership,
Organization, and persisted permissions. `X-Yarvis-Organization-Selector`
remains the sole temporary Membership selector and was not changed.

## Persistence and compatibility

Migration `20260813_37` makes `workspace_id` nullable for `RadarMerchant`,
`RadarRequest`, and `RadarActivity`, while retaining the columns and their
existing values. New canonical Radar writes persist `workspace_id = NULL`.
The migration is linear and reversible: `20260813_36 -> 20260813_37 ->
20260813_36 -> 20260813_37` was validated.

Workspace Platform and Opportunity remain outside this change and were not
modified. No Workspace-to-Organization relationship was created, inferred, or
assumed.

## Historical disposition

The excluded Radar history remains immutable and invisible to canonical
authority:

| Workspace | Merchants | Requests | Activities | Checklist items | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| `manual-close-validation` | 1 | 1 | 9 | 6 | 11 |
| `netpay-demo` | 7 | 8 | 36 | 39 | 51 |

No historical record was backfilled, mapped, updated, deleted, recreated, or
used to infer authority. No historical Radar receipt or DomainEvent was
created.

## Validation

- H2 migration round-trip: 2 passed.
- H2 API consolidation: 26 passed, including headerless Radar creates,
  nullable persistence, ignored legacy header, receipt replay, conflict,
  authority, revocation, and cross-organization behavior.
- OperationalRadar web tests: 2 passed.
- `python -m compileall src`, Docker API build, `git diff --check`, PostgreSQL
  health, and Alembic head `20260813_37` passed.

## F-011 status and next step

- F: **COMPLETE — VALIDATED**
- G: **COMPLETE — VALIDATED NO-OP**
- H: **COMPLETE — VALIDATED**
- I: pending
- F-011: **IN PROGRESS**

The next step is Stage I: final acceptance and factual closure, without
implementing new functionality.
