# F-011 Stage I Acceptance

## Status

**F-011 COMPLETE — VALIDATED**

## Accepted baseline

- Accepted HEAD: `78eb6b3c54ea3aa2c7b732bc948bb41bdc5c77e4`.
- Canonical API collection: 518 tests.
- Integral API result: 518 passed, 0 failed, 0 errors, 0 skipped, 0 xfailed,
  and 0 xpassed in 654.50 seconds.
- Durable Alembic head: `20260813_37`.

## Closure evidence

- F is **COMPLETE — VALIDATED**: canonical persisted authority, command
  receipts, command/event behavior, tenancy concealment, and the F-011
  regression suite are validated.
- G is **COMPLETE — VALIDATED NO-OP**: no cutover or backfill was eligible or
  performed for excluded historical Radar data.
- H is **COMPLETE — VALIDATED**: `X-Yarvis-Workspace` was retired from new
  Radar operations, OpenAPI, and the web client; new Radar records persist
  `workspace_id = NULL` under reversible migration `20260813_37`.
- `python -m compileall src`, the canonical Docker API build, PostgreSQL
  health, and `git diff --check` passed.

## Historical and governance invariants

The durable historical sets remain immutable and excluded:

| Workspace | Merchants | Requests | Activities | Checklist items | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| `manual-close-validation` | 1 | 1 | 9 | 6 | 11 |
| `netpay-demo` | 7 | 8 | 36 | 39 | 51 |

No retrospective Organization was assigned to these records, and no backfill,
receipt, event, provenance, or authority mapping was invented. Authority
continues to derive solely from persisted Principal, active
PrincipalMembership, Organization, and permissions resolved by
`AuthorityResolutionService`; headers and tokens do not grant authority or
select an Organization.

Amendments 003–010 remain ratified and frozen. The known
`authentication.py` worktree marker is EOL-only and is excluded from this
acceptance.

## Next stage

F-011 is complete. The next work, MVP Netpay “Alta de Sucursal”, requires a
separate mandate.
