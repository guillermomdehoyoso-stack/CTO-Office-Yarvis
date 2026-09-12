# Netpay Operational Data D1 — Synthetic Evidence

Status: ASSEMBLED — PENDING INDEPENDENT REVIEW AND ARCHITECTURE AUTHORITY ACCEPTANCE

## 1. Authority, scope and disposition

Guillermo de Hoyos, Architecture Authority, authorized evidence collection on local decision date 2026-09-11 and subsequently authorized the isolated Docker Compose project `netpay-d1-evidence-20260911`. Exceptions: None. Downstream authority: None. These acts authorize this evidence document and execution of existing synthetic suites, not fixes, implementation or conformance acceptance.

Current work package: D1 evidence consolidation as a prerequisite to D2-Lite. Current gate: independent review and express Architecture Authority acceptance remain pending. Next allowed action after this report is independent review. Repository state was verified before execution and must be verified again before any subsequent change.

Disposition: functional evidence assembled; quality gate NOT PASSED. Seven D1 tests, nine Master/Inbox regression tests and two frontend tests passed. Focused Pyright and TypeScript failed. No global D1 conformance is declared. An unconditional `D1 IMPLEMENTATION EVIDENCE VERIFIED FOR D2-LITE READ DEPENDENCY` declaration is not recommended on this record alone. D2-Lite implementation remains unauthorized.

Independent-review amendment: execution outcomes in this document are historical results reported by the collector, not runs reproduced by the independent reviewer. Code/configuration corroboration and retrospective limitations are distinguished below. The terminal review verdict is ACCEPT WITH AMENDMENTS; incorporation of its amendments does not establish their subsequent acceptance or an Architecture Authority act. The displayed Status is preserved pending those acts.

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

Retrospective verification boundary (F1, MAJOR documentary): the isolated composition described below is compatible with the repository. The checked-in Compose PostgreSQL service, fixture targets, Settings aliases, Alembic URL precedence and migration-test restoration logic corroborate the described configuration mechanisms. They do not prove the effective resources or destinations used in the historical run. The exact stdin override and resulting effective Compose configuration were not retained in this record. Effective destination checks, server identity, resource inspections and cleanup are collector-reported facts, not independently reproduced observations. Cleanup and effective resource identity remain retrospective limitations / TO BE VERIFIED; no missing logs, captures or evidence are invented. No contradictory evidence of shared or production resource access was found, but Git alone cannot demonstrate that such access or mutation did not occur.

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

Result classification: the seven D1 tests, nine Master/Inbox regressions, two frontend tests, frontend build, Ruff and format results below are historical results reported by the collector and coherent with the existing test sources and scripts. The independent reviewer did not reproduce them. PASS labels describe that historical report, not independent execution verification. `vite build` is not a TypeScript check. Ruff and format covered only the four FILES below, not the entire D1 implementation or its migration.

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
| `python -m pytest -q -p no:cacheprovider tests/test_netpay_operational_data.py` | 0 | 20.032 | PASS histórico reportado: 7 passed, 1 warning; pytest 17.70s |
| `python -m pytest -q -p no:cacheprovider tests/test_netpay_master.py tests/test_netpay_inbox.py` | 0 | 27.289 | PASS histórico reportado: 9 passed, 1 warning; pytest 24.93s |
| `python -m ruff check FILES` | 0 | 0.075 | PASS histórico reportado: All checks passed |
| `python -m ruff format --check FILES` | 0 | 0.076 | PASS histórico reportado: 4 files already formatted |
| `python -m pyright FILES` | 1 | 3.946 | FAIL: 7 errors, 0 warnings, 0 informations |
| `npm test -- src/components/netpay/NetpayDataWorkspace.test.tsx` | 0 | 2.177 | PASS histórico reportado: 2 tests, 1 file; Vitest 1.58s |
| TypeScript command below | 2 | 1.501 | FAIL: one TS2339 |
| `npm run build` | 0 | 1.887 | PASS histórico reportado: 109 modules; Vite 1.48s; no deployment |
| `git diff --check` | 0 | Not timed | PASS histórico reportado on host; no tracked source edits |

```text
npx --no-install tsc --noEmit --jsx react-jsx --module ESNext --moduleResolution bundler --target ES2022 --lib ES2022,DOM --types vite/client --allowSyntheticDefaultImports --skipLibCheck src/api/netpay.ts src/components/netpay/NetpayDataWorkspace.tsx
```

Pyright diagnostics:

- `src/yarvis_api/api/routes/netpay_data.py:222:27`: reporting_period unknown on type NoUsageCampaignEntry.
- Same file `222:104`: campaign_period unknown on type StoreProfitabilityFact.
- `tests/test_netpay_operational_data.py:180:11`, `181:11`, `188:11`, `189:11`: append is not a known attribute of None.
- Same test file `272:33`: str or None cannot be passed to upgrade's str revision parameter.

TypeScript diagnostic: `src/components/netpay/NetpayDataWorkspace.tsx:50:251`, TS2339, organizationSelector does not exist on NetpayRuntime. A successful Vite build does not establish static type correctness.

Individual static-diagnostic attribution (F2, MEDIUM): Git identifies the change that introduced the causal code; this is not a reproduction using historical tool versions. All eight diagnostics predate evidence collection. Six are attributable to D1 commit `6bb2c412232f84b0df516dd5da60af354a3f3d85`; two arose from the later `62628067359688360e0830be8c85b4d83057d4a9` change.

| Diagnostic | Causal change | Disposition |
| --- | --- | --- |
| Pyright `netpay_data.py:222:27`: `reporting_period` unknown on `NoUsageCampaignEntry` | D1 `6bb2c412` | Model union is not sufficiently narrowed for the type checker. |
| Pyright `netpay_data.py:222:104`: `campaign_period` unknown on `StoreProfitabilityFact` | D1 `6bb2c412` | Same insufficient union narrowing. |
| Pyright `test_netpay_operational_data.py:180:11`: `append` on possible `None` | D1 `6bb2c412` | Establish that the worksheet is non-null. |
| Pyright `test_netpay_operational_data.py:181:11`: `append` on possible `None` | D1 `6bb2c412` | Establish that the worksheet is non-null. |
| Pyright `test_netpay_operational_data.py:188:11`: `append` on possible `None` | D1 `6bb2c412` | Establish that the worksheet is non-null. |
| Pyright `test_netpay_operational_data.py:189:11`: `append` on possible `None` | D1 `6bb2c412` | Establish that the worksheet is non-null. |
| Pyright `test_netpay_operational_data.py:272:33`: optional head passed to `upgrade` requiring `str` | Later `6262806` | Head restoration introduced this optional argument; equality between optional values does not establish a non-null head. |
| TS2339 `NetpayDataWorkspace.tsx:50:251`: `organizationSelector` absent from `NetpayRuntime` | Later `6262806` | That change removed the runtime property; the original D1 access was compatible with the then-existing type. |

All eight diagnostics keep the reported static gate open. By themselves they do not demonstrate snapshot corruption and must not be described indiscriminately as eight semantic blockers of QRY-018. The five test diagnostics are outside the reader's runtime surface; the two backend diagnostics do not themselves prove incorrect runtime model/column selection; TS2339 affects the integration component's static gate, not persisted Facts. Resolution requires a separately authorized change; no waiver is inferred.

All initial failed attempts are retained in this disposition: D1 collection exit 2 in 3.380s (one collection error), Master/Inbox collection exit 2 in 2.864s (two collection errors), both because `/app/AGENTS.md` was missing from the initial ephemeral copy. Original AGENTS.md and required docs/development and docs/engineering markers were then copied into the runner. Pyright initially exited 127 in 11.526s because libatomic.so.1 was absent; libatomic1, also present in the repository API Dockerfile, was installed only inside the runner. No test or code was changed to resolve either environment failure. Initial TypeScript invocation omitted `--types vite/client`, exited 2 in 1.663s with both ImportMeta.env and organizationSelector diagnostics; adding the existing Vite types to the invocation removed only the former. Final Pyright and TypeScript failures were not repaired. Pytest's warning was the AnyIO BlockingPortal alias deprecation.

Dependency preparation used pip with requirements-dev.txt and `npm ci --ignore-scripts --no-audit --no-fund`. Tests/build did not write to the repository. A post-suite administrative verification initially failed in the checking script (fixture extraction, then an implicit psycopg2 driver); using the installed psycopg driver succeeded. These checking-script failures did not execute additional suites or migrations and do not replace the recorded test results.

## 5. Functional coverage and limits

The seven executed D1 tests are `test_profitability_preview_accept_replay_and_tenant_isolation`, `test_no_usage_rfc_filter_is_ephemeral_and_fail_closed`, `test_xlsx_and_formula_rejection`, `test_invalid_files_headers_and_internal_duplicates_fail_closed`, `test_preview_is_staging_only_and_confirmation_requires_exact_token`, `test_rfc_is_filtered_before_staging_and_never_persisted_or_returned`, and `test_operational_data_migration_round_trip`.

| Capability | Classification | Demonstrated scope / limitation |
| --- | --- | --- |
| Preview and staging | PASS histórico reportado | Synthetic preview is staged; no Facts before explicit confirmation |
| Batches and rows | PASS histórico reportado | Persisted synthetic batch/rows, validation and sanitized responses; not arbitrary dataset completeness |
| Facts | PASS histórico reportado | Acceptance produces the asserted profitability Fact; replay does not duplicate it |
| Tenant isolation | PASS histórico reportado | Covered cross-tenant paths and ephemeral filtering; not every possible join or future endpoint |
| Automatic matching | PASS histórico reportado | Synthetic exact Store Reference resolution; exhaustive ambiguity/concurrency not established |
| Manual matching | NOT COVERED | No dedicated mismatch validation test in the executed D1 suite |
| Upload idempotence | PASS histórico reportado | Tested duplicate upload behavior |
| Acceptance idempotence/replay | PASS histórico reportado | Same accepted result and single Fact in covered replay |
| Correct/incorrect token | PASS histórico reportado | Exact preview confirmation enforced |
| Rejection workflow | NOT COVERED | No dedicated reject-state transition test; input/formula rejection is a different property |
| Concurrent acceptance/rejection | NOT COVERED | No executed interleaving test |
| reporting_period | PASS histórico reportado | Synthetic normal period path; mixed/absent period ordering remains NOT COVERED |
| projected_action=unchanged | NOT COVERED | No dedicated multi-batch reconstruction assertion |
| Readback | PASS histórico reportado | Covered accepted result retrieval; lost-commit acknowledgment recovery NOT COVERED |
| Migration | PASS histórico reportado | D1 downgrade/upgrade and restoration to head 47 on isolated synthetic database |
| Frontend behavior | PASS histórico reportado | Two mocked component tests: upload/preview/accept/results and ephemeral field requirement; no real E2E |
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
| Missing rejection test | C for isolated sequential mutation coverage; A for source-state races | No global D1 conformance; rejection concurrency can change the state and provenance consumed by D2-Lite, so it is not disposed merely as outside the reader's invoked surface |
| Acceptance/rejection races | A | No deterministic race evidence; read-only consumption does not prove consistency of its source. Require separate evidence or an expressly reviewed containment decision before unconditional dependency acceptance |
| Missing accepted_at | B | Follow accepted proposal's deterministic load ordering; never label upload time as acceptance time |
| Missing supersedes_batch_id | B | Full snapshot selection/reconstruction must not depend on an absent supersession link |
| Float and currency | B | MXN derives from accepted business semantics; finite-value checks, null/coverage and precision must be explicit; no historical reinterpretation |
| no_use_indicator=None | C | No Uso remains excluded; None is not a derived lifecycle state |
| Unchanged reconstruction and invalid/mixed periods | A / B | Future deterministic reader tests and fail-closed behavior required; existing D1 tests do not demonstrate them |
| Focused Pyright failure | D | Seven diagnostics must be fixed or explicitly disposed under separate authority; evidence collection cannot waive them |
| Focused TypeScript failure | D | Existing runtime type mismatch requires separate correction/disposition; passing component tests/build does not close it |

This record supports only the named synthetic behaviors. It does not yet support unconditional D1 conformance or an unconditional D2-Lite read-dependency declaration. Minimum next act: independent review of this evidence and an express Authority disposition of failed quality checks and uncovered dependencies; authorize any required fixes/tests separately, then re-evaluate the bounded dependency. Do not repeat working implementation merely to manufacture closure documentation.

Independent-review dependency disposition: D1 completa: NO; dependencia D1 limitada suficiente para D2-Lite: NO TODAVÍA; implementación D2-Lite: NO AUTORIZADA; QRY-018 continúa candidato no registrado. A stable read snapshot can prevent a split response, but cannot correct an inconsistent ingestion history. Proposed read-side containment is not demonstrated containment; neither proposal acceptance nor this evidence amendment authorizes implementing QRY-018 to establish its own prerequisite afterward.

## 7. Evidence Gate and recovery

| Gate | Disposition |
| --- | --- |
| Isolated PostgreSQL and effective configuration | PASS histórico reportado before destructive suites |
| D1 suite and migration round-trip | PASS histórico reportado |
| Master/Inbox regressions | PASS histórico reportado |
| Frontend component tests and build | PASS histórico reportado |
| Ruff / formatting, four focused files | PASS histórico reportado; not whole-repository quality |
| Pyright / TypeScript | FAIL; no waiver inferred |
| Uncovered concurrency / reconstruction / E2E | NOT COVERED |
| Independent review | Terminal ACCEPT WITH AMENDMENTS recorded in §9; incorporated amendments pending review |
| Architecture Authority acceptance / conformance | NOT RECORDED |

Recovery was confined to the authorized test environment. After fixture teardown, the test database was absent. Before cleanup, each of the three containers' exact name, Compose project label, sole project network and mounts were verified; network and volume project labels were also verified. Only those three containers, `netpay-d1-evidence-20260911_default` and `netpay-d1-evidence-20260911_pgdata` were removed. Subsequent project-label listings for containers, networks and volumes were empty (`PROJECT_CLEANUP_VERIFIED=true`). Runner logs/caches/build output were ephemeral; this document retains commands, diagnostic details, timings and outcomes, not a signed raw-log archive.

No command targeted, inspected, mounted, queried, changed or removed `ctooffice-postgres-1`, `ctooffice_default` or `ctooffice_pgdata`. Their independent before/after state is not claimed, because inspecting them was prohibited. No production connections were made. No production rollback was needed. No source changes were reverted or repaired.

## 8. Documentary boundary and prohibitions

The only new repository artifact is this document. No tracked code, tests, migration, models, contracts, data or configuration changed. AUDIT_REPORT.md was not opened or included. Index remains empty; no staging, commit or push. D2-Lite proposal hash remains the baseline hash. Local and remote HEAD remain the baseline commit. UTF-8 without BOM, LF, Markdown structure and diff whitespace are checked on this artifact; its final canonical hash is supplied in the delivery message to avoid a self-referential hash.

Historical boundary clarification: the preceding paragraph records the collector's pre-publication state at `bcecbcb2a00a0449b943329ebbc27485bda6e1b8`. The amendments operate on published evidence commit `ea709de3c4b65b3ba477dbb10bec1918f788249f`, parent `bcecbcb2a00a0449b943329ebbc27485bda6e1b8`, whose reviewed canonical SHA-256 is `8C2ABE518328CF3C9D873B2EA3CEC2B98B97C9E499863C2F58868BA7320FE20B`. Only this document may change during amendment incorporation; no staging, commit or push is authorized by that work.

No D2-Lite implementation, contract assignment/registration/promotion, production, deployment, Merchant 360, Mixue, Boba Tree, Package B, Core/Salesforce, Gmail, secrets or real-data operation is authorized by this report. No roadmap gate is closed. No synthetic pass is business approval or historical-data certification.

## 9. Independent Review

### 9.1 Independent Review Disposition

The terminal independent review applies to the exact published commit and canonical hash identified in §8. This section incorporates its findings; it does not claim a further review of the amended text or Architecture Authority acceptance. Reviewer identity and review date are not supplied as documentary facts and are not invented. Mandatory dispositions accepted by Architecture Authority: [not recorded].

| Field | Disposition |
| --- | --- |
| Verdict | ACCEPT WITH AMENDMENTS |
| Critical findings | 0 |
| High findings | 0 |
| Major findings | F1, F3, F4, F5, F6, F7 |
| Medium findings | F2 |
| D1 conformance | NOT ESTABLISHED |
| D2-Lite dependency sufficiency | NOT ESTABLISHED |
| D2-Lite implementation authority | NONE |

### 9.2 Individual findings and required dispositions

| Finding | Severity | Evidence and disposition |
| --- | --- | --- |
| F1 — Retrospective verifiability | MAJOR documentary | Separate historical collector reports from source corroboration and facts not independently verifiable retrospectively, as specified in §§3–4. No exact override/effective Compose configuration or independent cleanup capture is retained. Preserve that limitation without inventing logs. |
| F2 — Open static gate | MEDIUM | The eight individual diagnostics and Git attribution are recorded in §4. The static gate remains failed; their runtime and reader implications differ and do not independently prove snapshot corruption. |
| F3 — Concurrent acceptance | MAJOR | `accept_dataset` reads batch status before locking rows; it neither locks the batch nor revalidates its status after waiting. Fact uniqueness can roll back duplicate inserts but does not establish command serialization. An entirely unchanged batch inserts no Facts to activate that protection. Deterministic concurrency evidence is missing; D1 conformance and bounded dependency sufficiency remain unestablished. |
| F4 — Concurrent rejection and accept/reject races | MAJOR | `reject_dataset` has no batch lock or compare-and-set status update. Acceptance and rejection may act on stale `needs_review` observations. A finally rejected batch may retain Facts, or acceptance may overwrite rejection. Rejection races therefore affect reader selection/provenance, not merely an out-of-surface mutation. |
| F5 — Unchanged reconstruction and eligible provenance | MAJOR | `projected_action=unchanged` is fixed during upload, not recalculated at acceptance; acceptance skips Fact creation for such rows. `_latest_fingerprint` does not restrict its source batch to accepted status. Full membership and eligible prior accepted Fact/source-row provenance are not demonstrated by replay of one accepted batch. D2-Lite dependency sufficiency remains unestablished. |
| F6 — Manual matching, Master changes and match/accept race | MAJOR | Manual resolution checks same-tenant active reference but does not prove equality to the originally reported Store ID. Master can change the identifier on the same UUID; matching can race with acceptance and change row/Fact association. Automatic normalization is not textual identity equality. Proposed conservative reader containment requires evidence, not assumed closure. |
| F7 — Periods, history, authority, replay and E2E | MAJOR | A batch may have `reporting_period=None` with individually valid mixed row periods, and acceptance does not require homogeneity. A single Fact count and replay do not prove multibatch historical preservation. The covered foreign GET and Inbox regressions do not establish D1 mutation rejection for revoked/foreign authority. Upload's existing-hash return precedes receipt checking, leaving conflicting key/payload behavior uncovered. Browser E2E required by Amendment 016 §7 is absent. |

F4's code-derived interleavings are risks requiring reproduction, not newly executed failures: rejection can read `needs_review`, acceptance can commit, and rejection can then persist `rejected`; acceptance can likewise read `needs_review`, rejection can commit, and acceptance can continue to `accepted`. Different-key concurrent rejections can repeat events; same-key rejection has no local uniqueness-conflict handling. Combined with `_latest_fingerprint` lacking accepted-source filtering, rejected-source Facts could inform a later unchanged classification. Tests must establish the actual outcomes and safe disposition.

F5 requires all selected-batch rows to remain in the report universe, including entirely unchanged and mixed snapshots. Reconstruction must validate equivalent eligible Facts and their source rows; it must not take an arbitrary latest historical value, copy staging metrics as accepted Facts, silently union snapshots or convert absent Stores/null metrics to zero. A stable database snapshot does not repair a previously inconsistent source history.

F6 requires explicit evidence for mismatch, inactive references, collisions, Master correction and concurrent matching. Preserve the reported Store ID and suppress unproven Master attribution. Neither an active same-tenant UUID nor normalized automatic matching establishes exact reported/current identifier equality for the portfolio.

F7 also retains the numeric and temporal boundaries in §6: missing acceptance/supersession columns cannot be invented; MXN is the accepted business meaning, not a stored currency field; Float precision, non-finite values, nulls and coverage require explicit handling. No Uso remains excluded from D2-Lite, without substituting that exclusion for complete D1 evidence.

### 9.3 Minimum recommended remediation — separate authority required

The following is recommended future work only, not authorization to edit code, tests, migrations, configuration, contracts or infrastructure:

1. Resolve the eight static diagnostics and rerun the affected checks, preserving their individual attribution and without claiming that a Vite build is type validation.
2. Run deterministic tests with independent sessions and barriers for accept/accept, accept/reject in both orders, reject/reject and match/accept. Cover equal and distinct idempotency keys where applicable, batches with inserts and entirely unchanged batches. Verify durable batch status, rows, Facts, events, receipts and subsequent replay.
3. Prove entirely unchanged and mixed snapshots, intervening value changes, rejected or ineligible source batches, contradictory provenance and Stores absent from a later report. Verify membership, metrics, coverage and source identities; do not repair history through the reader.
4. Cover mixed/invalid periods and invalidation, incoherent matching, inactive references, collisions and Master changes, including consistency of selection, summary and page during concurrent changes.
5. Demonstrate multibatch preservation of prior Fact values and provenance; D1 route rejection for revoked authority and incorrect tenant; conflicting replay keys/payloads; and recovery from uncertain acceptance outcomes.
6. Supply the synthetic browser E2E required for complete D1 conformance under Amendment 016 §7. Existing mocked frontend tests do not fulfill it.

### 9.4 Terminal dependency matrix

| Alternative | Disposition |
| --- | --- |
| D1 completa | NO |
| dependencia D1 limitada suficiente para D2-Lite | NO TODAVÍA |
| implementación D2-Lite | NO AUTORIZADA |
| QRY-018 | continúa candidato no registrado |

ACCEPT WITH AMENDMENTS accepts the bounded evidence record subject to the stated documentary amendments; it does not itself establish D1 conformance, accept dependency sufficiency, authorize corrections or D2-Lite, register QRY-018, grant release/production authority or close any gate. Incorporation now stops for review of the amendments; the future Architecture Authority act below remains unrecorded.

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
