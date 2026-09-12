# Netpay Operational Data D1 — Synthetic Evidence

Status: ASSEMBLED — PENDING INDEPENDENT REVIEW AND ARCHITECTURE AUTHORITY ACCEPTANCE

## 1. Authority, scope and disposition

Guillermo de Hoyos, Architecture Authority, authorized evidence collection on local decision date 2026-09-11 and subsequently authorized the isolated Docker Compose project `netpay-d1-evidence-20260911`. Exceptions: None. Downstream authority: None. These acts authorize this evidence document and execution of existing synthetic suites, not fixes, implementation or conformance acceptance.

Current work package: D1 evidence consolidation as a prerequisite to D2-Lite. Current gate: independent review and express Architecture Authority acceptance remain pending. Next allowed action after this report is independent review. Repository state was verified before execution and must be verified again before any subsequent change.

Disposition: functional evidence assembled; quality gate NOT PASSED. Seven D1 tests, nine Master/Inbox regression tests and two frontend tests passed. Focused Pyright and TypeScript failed. No global D1 conformance is declared. An unconditional `D1 IMPLEMENTATION EVIDENCE VERIFIED FOR D2-LITE READ DEPENDENCY` declaration is not recommended on this record alone. D2-Lite implementation remains unauthorized.

## 2. Immutable baseline and sources

Local HEAD and origin/feat/operational-intake-spine were verified as `bcecbcb2a00a0449b943329ebbc27485bda6e1b8`. Initial index was empty; the sole untracked file was `AUDIT_REPORT.md`, which was not opened. This evidence path did not exist. No separately accepted terminal D1 conformance act was located in the inspected authorization, evidence and relevant Git history; implementation and passing tests are not substituted for that act.

| Source | Identity / significance |
| --- | --- |
| `docs/engineering/NETPAY_OPERATIONAL_DATA_D1_IMPLEMENTATION_AUTHORIZATION.md` | Authorization commit `8277bcccd9f0af013d7096ae76003fd8ebdb32a7`; AUTHORIZE D1 IMPLEMENTATION, decision date 2026-08-19; named authority Guillermo Mario De Hoyos Olivera |
| D1 implementation | `6bb2c412232f84b0df516dd5da60af354a3f3d85`; 16 files, 1441 insertions, 15 deletions; implementation evidence, not terminal acceptance |
| Later migration-test change | `62628067359688360e0830be8c85b4d83057d4a9`; restore the current initial head after the D1 round-trip |
| `docs/engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_016.md` | D1/D2 roadmap scope; this evidence does not amend it or close D2 |
| `docs/development/PROJECT_CONTEXT.md`, `CURRENT_STATE.md`, `CURRENT_SPRINT.md` | Engineering bootstrap and current gate context inspected |
| `apps/api/src/yarvis_api/api/routes/netpay_data.py` | Intake, matching, acceptance, rejection and readback implementation |
| `apps/api/src/yarvis_api/models/netpay_operational_data.py` and `schemas/netpay_operational_data.py` | Batches, rows, Facts and response definitions |
| `apps/api/tests/conftest.py`, `apps/api/migrations/env.py`, `apps/api/alembic.ini` | Destructive fixture scope and configuration precedence |
| `apps/api/tests/test_netpay_operational_data.py` | Seven current D1 tests executed at baseline |
| `apps/api/tests/test_netpay_master.py`, `test_netpay_inbox.py` | Nine relevant regression tests executed |
| `apps/web/src/components/netpay/NetpayDataWorkspace.test.tsx` | Two current component tests; mocked API, not browser/backend E2E |

Canonical SHA-256 means UTF-8 content with CRLF/CR normalized to LF.

| File | Canonical SHA-256 at baseline |
| --- | --- |
| D1 implementation authorization | `845CF5D0A1A74237826828B75EDF6AC1FB7EF4D2D295EEDB544FBE9669631B7F` |
| `apps/api/tests/test_netpay_operational_data.py` | `BD78A1DEEE8FF51C46ED0698A153A51AD206D111D6B8A7D9899092D159E23AE1` |
| `apps/api/migrations/versions/20260819_41_netpay_operational_data_d1.py` | `40617120C6EA1E5F76D5DFC154ABC115569AC5D91634A35D6DA0AD8E7767B124` |
| Accepted D2-Lite proposal | `D8A2B0280E757490F0018BD9EA10D342D81C81D3C8269EE736562DDF965302D2` |

## 3. Isolated execution environment

Docker Desktop Linux engine responded; server version 29.6.1. The real repository `docker-compose.yml` supplied PostgreSQL. Compose used `--env-file NUL -p netpay-d1-evidence-20260911 -f docker-compose.yml`. No repository configuration file was created or modified. Resolved configuration was checked before creation: project-specific network and volume, no external volume/network, no PostgreSQL host port, no shared bind mount, no production env file. No resources with this project label existed initially.

| Resource | Sanitized identity |
| --- | --- |
| PostgreSQL | `netpay-d1-evidence-20260911-postgres-1` |
| Network | `netpay-d1-evidence-20260911_default` |
| Volume | `netpay-d1-evidence-20260911_pgdata` |
| API runner | `netpay-d1-evidence-20260911-api-runner` |
| Web runner | `netpay-d1-evidence-20260911-web-runner` |
| Application/test/migration database | `yarvis_test` |
| Internal database host and port | `postgres`, 5432, on the project-only network |

PostgreSQL creation used `docker compose --env-file NUL -p netpay-d1-evidence-20260911 -f docker-compose.yml up -d postgres`. Runners used the same Compose project with an in-memory stdin override: API `python:3.12-slim`, web `node:20-alpine`, no build, sole read-only `/source` source mount, overridden test-only environment, no dependencies started by the runners. Each runner's actual network and read-only mount were inspected. Sources were copied to ephemeral `/app`; dependencies, caches and build outputs stayed in the runners.

Test credentials were obtained from the repository's synthetic fixture, not a production secret. No credentials or connection URLs are reproduced here. `DATABASE_URL`, `YARVIS_DATABASE_URL`, `YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL`, `YARVIS_MIGRATOR_DATABASE_URL` and `database_url` were pinned to the same isolated test destination. `Settings` environment aliases, secret indirection and Alembic precedence were inspected. No secret indirection or env file could override the destination. Alembic's configured URL / migrator environment / Settings resolution was verified against the same test target; its checked-in ini supplied no conflicting URL.

The fixture's TEST_URL and ADMIN_URL were separately checked: the application database was `yarvis_test`; the administrative connection used `postgres` on the very same isolated server exclusively for creating/dropping `yarvis_test`. Effective Settings, fixture and migration targets agreed. Real server-address comparison confirmed administrative and application connections reached that isolated server. Before destructive tests, checks reported `DATABASE_URL_IS_ISOLATED=true`, `YARVIS_DATABASE_URL_IS_ISOLATED=true`, `EFFECTIVE_SETTINGS_DATABASE_IS_TEST=true`, `ADMIN_AND_APP_SERVER_MATCH=true`, `PRODUCTION_REFERENCE_PRESENT=false`, `ISOLATION_VERIFIED=true`.

The database initially had no Alembic table: initial environment revision EMPTY. Fixture setup migrated to the unique script head `20260823_47`. The migration test captured that head, downgraded to `20260819_40`, upgraded to D1 `20260819_41`, asserted that revision, and restored/asserted the captured head in finally. Its PASS proves that round-trip on this synthetic database, not preservation of arbitrary production data. The session fixture subsequently dropped `yarvis_test`. A final isolated administrative query returned `TEST_DATABASES_AFTER_TEARDOWN=0` and PostgreSQL version `16.14 (Debian 16.14-1.pgdg13+1)`.

## 4. Commands, versions and results

Backend commands ran from ephemeral `/app` (copy of apps/api). Frontend commands ran from ephemeral `/app` in the web runner. Durations below are measured subprocess wall seconds; pytest also reports its own duration. No suite source was edited.

Versions: Python 3.12.13; pytest 8.4.1; Ruff 0.12.11; Pyright 1.1.403; SQLAlchemy 2.0.41; psycopg 3.2.9; Alembic 1.16.4; frontend Node 20.20.2; npm 10.8.2; Vitest 3.2.7; TypeScript 5.9.3; Vite 6.4.3. Pyright's separate nodeenv installed Node 26.8.2. These are observed environment versions, not a claim of image-digest reproducibility.

For the three focused Python quality commands, FILES is exactly:

```text
src/yarvis_api/api/routes/netpay_data.py
src/yarvis_api/models/netpay_operational_data.py
src/yarvis_api/schemas/netpay_operational_data.py
tests/test_netpay_operational_data.py
```

| Command | Exit | Seconds | Result |
| --- | --- | --- | --- |
| `python -m pytest -q -p no:cacheprovider tests/test_netpay_operational_data.py` | 0 | 20.032 | PASS ejecutado: 7 passed, 1 warning; pytest 17.70s |
| `python -m pytest -q -p no:cacheprovider tests/test_netpay_master.py tests/test_netpay_inbox.py` | 0 | 27.289 | PASS ejecutado: 9 passed, 1 warning; pytest 24.93s |
| `python -m ruff check FILES` | 0 | 0.075 | PASS ejecutado: All checks passed |
| `python -m ruff format --check FILES` | 0 | 0.076 | PASS ejecutado: 4 files already formatted |
| `python -m pyright FILES` | 1 | 3.946 | FAIL: 7 errors, 0 warnings, 0 informations |
| `npm test -- src/components/netpay/NetpayDataWorkspace.test.tsx` | 0 | 2.177 | PASS ejecutado: 2 tests, 1 file; Vitest 1.58s |
| TypeScript command below | 2 | 1.501 | FAIL: one TS2339 |
| `npm run build` | 0 | 1.887 | PASS ejecutado: 109 modules; Vite 1.48s; no deployment |
| `git diff --check` | 0 | Not timed | PASS ejecutado on host; no tracked source edits |

```text
npx --no-install tsc --noEmit --jsx react-jsx --module ESNext --moduleResolution bundler --target ES2022 --lib ES2022,DOM --types vite/client --allowSyntheticDefaultImports --skipLibCheck src/api/netpay.ts src/components/netpay/NetpayDataWorkspace.tsx
```

Pyright diagnostics:

- `src/yarvis_api/api/routes/netpay_data.py:222:27`: reporting_period unknown on type NoUsageCampaignEntry.
- Same file `222:104`: campaign_period unknown on type StoreProfitabilityFact.
- `tests/test_netpay_operational_data.py:180:11`, `181:11`, `188:11`, `189:11`: append is not a known attribute of None.
- Same test file `272:33`: str or None cannot be passed to upgrade's str revision parameter.

TypeScript diagnostic: `src/components/netpay/NetpayDataWorkspace.tsx:50:251`, TS2339, organizationSelector does not exist on NetpayRuntime. A successful Vite build does not establish static type correctness.

All initial failed attempts are retained in this disposition: D1 collection exit 2 in 3.380s (one collection error), Master/Inbox collection exit 2 in 2.864s (two collection errors), both because `/app/AGENTS.md` was missing from the initial ephemeral copy. Original AGENTS.md and required docs/development and docs/engineering markers were then copied into the runner. Pyright initially exited 127 in 11.526s because libatomic.so.1 was absent; libatomic1, also present in the repository API Dockerfile, was installed only inside the runner. No test or code was changed to resolve either environment failure. Initial TypeScript invocation omitted `--types vite/client`, exited 2 in 1.663s with both ImportMeta.env and organizationSelector diagnostics; adding the existing Vite types to the invocation removed only the former. Final Pyright and TypeScript failures were not repaired. Pytest's warning was the AnyIO BlockingPortal alias deprecation.

Dependency preparation used pip with requirements-dev.txt and `npm ci --ignore-scripts --no-audit --no-fund`. Tests/build did not write to the repository. A post-suite administrative verification initially failed in the checking script (fixture extraction, then an implicit psycopg2 driver); using the installed psycopg driver succeeded. These checking-script failures did not execute additional suites or migrations and do not replace the recorded test results.

## 5. Functional coverage and limits

The seven executed D1 tests are `test_profitability_preview_accept_replay_and_tenant_isolation`, `test_no_usage_rfc_filter_is_ephemeral_and_fail_closed`, `test_xlsx_and_formula_rejection`, `test_invalid_files_headers_and_internal_duplicates_fail_closed`, `test_preview_is_staging_only_and_confirmation_requires_exact_token`, `test_rfc_is_filtered_before_staging_and_never_persisted_or_returned`, and `test_operational_data_migration_round_trip`.

| Capability | Classification | Demonstrated scope / limitation |
| --- | --- | --- |
| Preview and staging | PASS ejecutado | Synthetic preview is staged; no Facts before explicit confirmation |
| Batches and rows | PASS ejecutado | Persisted synthetic batch/rows, validation and sanitized responses; not arbitrary dataset completeness |
| Facts | PASS ejecutado | Acceptance produces the asserted profitability Fact; replay does not duplicate it |
| Tenant isolation | PASS ejecutado | Covered cross-tenant paths and ephemeral filtering; not every possible join or future endpoint |
| Automatic matching | PASS ejecutado | Synthetic exact Store Reference resolution; exhaustive ambiguity/concurrency not established |
| Manual matching | NOT COVERED | No dedicated mismatch validation test in the executed D1 suite |
| Upload idempotence | PASS ejecutado | Tested duplicate upload behavior |
| Acceptance idempotence/replay | PASS ejecutado | Same accepted result and single Fact in covered replay |
| Correct/incorrect token | PASS ejecutado | Exact preview confirmation enforced |
| Rejection workflow | NOT COVERED | No dedicated reject-state transition test; input/formula rejection is a different property |
| Concurrent acceptance/rejection | NOT COVERED | No executed interleaving test |
| reporting_period | PASS ejecutado | Synthetic normal period path; mixed/absent period ordering remains NOT COVERED |
| projected_action=unchanged | NOT COVERED | No dedicated multi-batch reconstruction assertion |
| Readback | PASS ejecutado | Covered accepted result retrieval; lost-commit acknowledgment recovery NOT COVERED |
| Migration | PASS ejecutado | D1 downgrade/upgrade and restoration to head 47 on isolated synthetic database |
| Frontend behavior | PASS ejecutado | Two mocked component tests: upload/preview/accept/results and ephemeral field requirement; no real E2E |
| Frontend static typing | FAIL | TS2339 remains |

No unexecuted test is labeled PASS histórico verificable. No full backend suite, browser E2E, stress test or production trial was executed. Passing fixtures demonstrate their assertions only.

## 6. D2-Lite dependency assessment

Read-only inspection of `netpay_data.py` establishes that acceptance appends projected Facts and skips unchanged rows, using row payloads/fingerprints and Store References. Accepted batch status exists durably. The current schema does not provide accepted_at or supersedes_batch_id. Volume uses Float and no currency column; the accepted D2-Lite business confirmation supplies MXN semantics without changing history. Manual matching can select an active same-Organization reference without asserting equality to the originally reported Store ID. Master correction can change the identifier on the same reference UUID. Those are material limitations for a portfolio reader.

| Dependency | Available evidence | D2-Lite implication |
| --- | --- | --- |
| Accepted batches/status | Model, acceptance and replay tests | Filter accepted status; existence of a batch alone is insufficient |
| reporting_period | Model and normal-path test | Validate period before selecting the maximum; missing/mixed data cannot be silently treated as a complete snapshot |
| Rows | Controlled payload and fingerprints persist | Required to retain the originally reported identifier and snapshot universe |
| Facts | Append-on-change projection tested for insert | Facts of the selected batch alone cannot represent unchanged rows |
| Fingerprints | Source and functional fingerprints in intake | Reconstruction must demonstrate matching historical provenance, not substitute current Master values |
| Store References | Tenant-scoped matching with mutable reference identity | Enforce Organization and originally reported identifier coherence |
| Tenant scoping | Covered isolation tests plus route inspection | Future joins require their own tenant-safe evidence |
| Idempotence for reading | Upload/replay passes | Does not prove snapshot consistency, unchanged reconstruction or uncertain-outcome resolution for D2-Lite |

A = blocks D2-Lite until resolved or independently accepted containment; B = candidate containment by the accepted fail-closed D2-Lite design, not implemented evidence; C = mutation outside D2-Lite's invoked surface; D = prior correction under separate authority required to pass the named gate.

| Gap | Disposition | Required treatment |
| --- | --- | --- |
| Manual matching discrepancy | B / C | Reader must preserve reported_store_id and fail closed on mismatch; do not infer legal identity from current Master |
| Missing rejection test | C | No global D1 conformance; document the uncovered mutation and obtain explicit review disposition |
| Acceptance/rejection races | A | No deterministic race evidence; read-only consumption does not prove consistency of its source. Require separate evidence or an expressly reviewed containment decision before unconditional dependency acceptance |
| Missing accepted_at | B | Follow accepted proposal's deterministic load ordering; never label upload time as acceptance time |
| Missing supersedes_batch_id | B | Full snapshot selection/reconstruction must not depend on an absent supersession link |
| Float and currency | B | MXN derives from accepted business semantics; finite-value checks, null/coverage and precision must be explicit; no historical reinterpretation |
| no_use_indicator=None | C | No Uso remains excluded; None is not a derived lifecycle state |
| Unchanged reconstruction and invalid/mixed periods | A / B | Future deterministic reader tests and fail-closed behavior required; existing D1 tests do not demonstrate them |
| Focused Pyright failure | D | Seven diagnostics must be fixed or explicitly disposed under separate authority; evidence collection cannot waive them |
| Focused TypeScript failure | D | Existing runtime type mismatch requires separate correction/disposition; passing component tests/build does not close it |

This record supports only the named synthetic behaviors. It does not yet support unconditional D1 conformance or an unconditional D2-Lite read-dependency declaration. Minimum next act: independent review of this evidence and an express Authority disposition of failed quality checks and uncovered dependencies; authorize any required fixes/tests separately, then re-evaluate the bounded dependency. Do not repeat working implementation merely to manufacture closure documentation.

## 7. Evidence Gate and recovery

| Gate | Disposition |
| --- | --- |
| Isolated PostgreSQL and effective configuration | PASS ejecutado before destructive suites |
| D1 suite and migration round-trip | PASS ejecutado |
| Master/Inbox regressions | PASS ejecutado |
| Frontend component tests and build | PASS ejecutado |
| Ruff / formatting, four focused files | PASS ejecutado; not whole-repository quality |
| Pyright / TypeScript | FAIL; no waiver inferred |
| Uncovered concurrency / reconstruction / E2E | NOT COVERED |
| Independent review | PENDING |
| Architecture Authority acceptance / conformance | NOT RECORDED |

Recovery was confined to the authorized test environment. After fixture teardown, the test database was absent. Before cleanup, each of the three containers' exact name, Compose project label, sole project network and mounts were verified; network and volume project labels were also verified. Only those three containers, `netpay-d1-evidence-20260911_default` and `netpay-d1-evidence-20260911_pgdata` were removed. Subsequent project-label listings for containers, networks and volumes were empty (`PROJECT_CLEANUP_VERIFIED=true`). Runner logs/caches/build output were ephemeral; this document retains commands, diagnostic details, timings and outcomes, not a signed raw-log archive.

No command targeted, inspected, mounted, queried, changed or removed `ctooffice-postgres-1`, `ctooffice_default` or `ctooffice_pgdata`. Their independent before/after state is not claimed, because inspecting them was prohibited. No production connections were made. No production rollback was needed. No source changes were reverted or repaired.

## 8. Documentary boundary and prohibitions

The only new repository artifact is this document. No tracked code, tests, migration, models, contracts, data or configuration changed. AUDIT_REPORT.md was not opened or included. Index remains empty; no staging, commit or push. D2-Lite proposal hash remains the baseline hash. Local and remote HEAD remain the baseline commit. UTF-8 without BOM, LF, Markdown structure and diff whitespace are checked on this artifact; its final canonical hash is supplied in the delivery message to avoid a self-referential hash.

No D2-Lite implementation, contract assignment/registration/promotion, production, deployment, Merchant 360, Mixue, Boba Tree, Package B, Core/Salesforce, Gmail, secrets or real-data operation is authorized by this report. No roadmap gate is closed. No synthetic pass is business approval or historical-data certification.

## 9. Independent Review

Pending. Reviewer: [not recorded]. Verdict: [not recorded]. Mandatory dispositions accepted: [not recorded]. No terminal ACCEPT or conformance is asserted by the evidence collector.

## 10. Future Architecture Authority Act

| Field | Value |
| --- | --- |
| Authority | [not recorded] |
| Decision | [not recorded] |
| Decision date | [not recorded] |
| Reviewed commit | [not recorded] |
| Reviewed canonical SHA-256 | [not recorded] |
| Independent review verdict | [not recorded] |
| Mandatory findings remaining | [not recorded] |
| Accepted evidence scope | [not recorded] |
| D1 conformance disposition | [not recorded] |
| D2-Lite dependency disposition | [not recorded] |
| Accepted exceptions | [not recorded] |
| Downstream authority | [not recorded] |
