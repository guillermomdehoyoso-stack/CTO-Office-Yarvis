# YARVIS
# WS-000 Workspace Conformance Review

## Document Control

- Work package: WS-000 — Development Workspace Bootstrap
- Review status: WS-000 validation passes; isolated-worktree validation pending
- Date: 2026-07-25
- Scope: current uncommitted Workspace API, Workspace Platform, workspace-shell,
  `ws000` definition, and their visible composition points.

## 1. Review Basis

This review evaluates the current WS-000 candidate implementation against the
ratified Application Architecture, Technical Blueprint, Governance Baseline V1,
and the current `CURRENT_STATE.md` / `CURRENT_SPRINT.md` records.

WS-000 is authorized outside the scoped EOS Foundation Documentation gate. That
authorization does not waive application isolation, projection safety, privacy,
or public-contract requirements.

## 2. Decision

**CONDITIONALLY READY FOR ISOLATED WS-000 VALIDATION.**

- BLOCKER: 0
- MAJOR: 0
- MINOR: 0

No WS-000 commit or clean baseline may be created until the WS-000-only patch
passes validation in an isolated worktree.

## 2.1 Recorded Human Decisions

The following decisions were approved by the repository user on 2026-07-25:

1. Every Workspace endpoint, including repository search, requires explicit
   authentication before it accesses or returns repository content. Granular
   authorization is deferred beyond the minimum needed to prevent unauthenticated
   exposure.
2. `WorkspaceShell` is a separate Workspace surface. It must not replace the
   current product UI.

## 3. Findings

### WS000-001 — Repository root resolves to the API subproject, not the repository

- Severity: BLOCKER
- Evidence:
  - `get_workspace_platform()` starts discovery from
    `apps/api/src/yarvis_api/services/workspace_platform.py`.
  - `locate_repository_root()` returns the first ancestor containing
    `pyproject.toml` and `src/yarvis_api`, which is `apps/api`.
  - Workspace artifacts require repository-root paths such as
    `docs/development/CURRENT_STATE.md` and
    `docs/engineering/GOVERNANCE_BASELINE_V1.md`.
- Impact:
  - The platform scans `apps/api`, not `C:/Python Projects/CTO Office`.
  - Current sprint, gate, and baseline projections become `UNKNOWN` rather than
    repository-derived facts.
  - WS-000 fails its purpose: a repository-driven Development Workspace.
- Required correction:
  - Make repository-root resolution explicit and test it from the actual
    repository root. It must not stop at a nested application project merely
    because it contains a Python project marker.
- Corrective implementation:
  - Repository markers (`AGENTS.md` and `docs`) are now searched across all
    ancestors before nested Python project markers are considered.
  - The composition root builds the WorkspacePlatform with that resolved root.
- Closure status: implementation corrected; backend test execution is pending
  because no local Python interpreter or Docker daemon is available.

### WS000-002 — Workspace API exposes repository content without an explicit access boundary

- Severity: BLOCKER
- Evidence:
  - `/api/v1/search` calls `LightweightSearchStrategy`.
  - The strategy reads `.py`, `.ts`, `.tsx`, `.json`, `.yml`, `.yaml`, `.md`,
    and `.txt` files and returns content snippets.
  - The Workspace routes have no explicit authentication or authorization
    dependency.
- Impact:
  - A repository workspace may disclose implementation, configuration, or
    sensitive textual material through an unauthenticated HTTP endpoint.
  - This conflicts with the Technical Blueprint privacy requirement that
    responses disclose only permitted information.
- Required correction:
  - Define and enforce a Workspace access boundary before exposing repository
    content. Until that boundary exists, search must be restricted to a
    demonstrably safe allowlist and return only permitted metadata/snippets.
- Corrective implementation:
  - A router-level `require_workspace_access` dependency now denies every
    Workspace route unless the configured Workspace token is supplied.
  - The token is a typed secret setting. A missing configuration denies access.
  - The browser client accepts a session-only operator-provided token; no token
    is embedded in source or persisted in the repository.
- Closure status: implementation corrected; backend authentication test is
  present but cannot be executed until a Python/Docker test environment exists.

### WS000-003 — Process-global cached WorkspacePlatform violates composition isolation

- Severity: MAJOR
- Evidence:
  - `get_workspace_platform()` is decorated with `@lru_cache`.
  - Routes obtain that cached instance directly rather than through explicit
    application composition.
- Impact:
  - Workspace configuration and lifecycle are process-global rather than
    application-owned.
  - Test and multi-application isolation cannot be demonstrated.
- Required correction:
  - Compose the WorkspacePlatform per application or use an explicit immutable
    application-owned dependency. Do not use a process-global cache as the
    authority.
- Corrective implementation:
  - The global cached provider was removed. ApplicationState now owns one
    WorkspacePlatform created by the composition root for each application.
- Closure status: implementation corrected; two-application isolation test is
  present but cannot be executed in the available environment.

### WS000-004 — Existing product UI is replaced without a compatibility decision

- Severity: MAJOR
- Evidence:
  - `apps/web/src/App.tsx` replaces the existing routes and product surfaces
    with `WorkspaceShell`.
- Impact:
  - Current Mission Control, Cases, Conversation, NetPay Intake, Recovery Queue,
    Organizations, and People routes are removed from the primary UI surface.
  - The WS-000 objective does not establish an approved product-surface
    retirement or replacement decision.
- Required correction:
  - Preserve the existing application experience or record an explicit,
    reviewed migration decision that authorizes replacement. A Development
    Workspace should initially be introduced as a distinct surface.
- Corrective implementation:
  - Existing application routes are restored. Workspace is now available at
    `/workspace/*`, and internal Workspace navigation is relative to that
    separate surface.
- Closure status: resolved. Full frontend regression passed: 9 files, 21 tests.

### WS000-005 — Workspace tests do not cover the repository-root or privacy contract

- Severity: MINOR
- Evidence:
  - `test_workspace_api.py` checks endpoint availability and selected response
    fields, but does not assert root resolution, access control, safe search
    output, isolation, or no-mutation behavior.
- Required correction:
  - Add focused tests for the resolved repository root, artifact state
    projection, authorization behavior, safe search redaction/allowlisting,
    per-application isolation, and query non-mutation.
- Corrective implementation:
  - Focused tests now cover unauthenticated rejection, root resolution,
    repository-state projection, two-application isolation, and authenticated
    endpoint behavior.
- Closure status: partial. The tests are present; backend execution is blocked
  by the unavailable Python/Docker runtime.

### WS000-006 — Generated Python caches are present inside an untracked Workspace directory

- Severity: MINOR
- Evidence:
  - `apps/api/src/yarvis_api/services/workspace/__pycache__/` contains compiled
    Python files and is included under the untracked directory status.
- Required correction:
  - Exclude generated caches from integration and verify repository ignore
    coverage. Do not include them in a source or documentation baseline.
- Closure status: resolved. The existing root `.gitignore` excludes
  `__pycache__/`; generated caches are not eligible for staging.

## 4. Scope Confirmation

The following remain appropriate WS-000 candidate responsibilities after the
findings are addressed:

- repository-derived, read-only development projections;
- an explicit Workspace registry and `ws000` definition;
- safe Workspace dashboard, timeline, repository-health, and document-reference
  views;
- a distinct frontend Workspace surface;
- testable, non-authoritative client behavior.

WS-000 must not absorb Inbox implementation, canonical domain mutation,
unauthorized repository inspection, global service ownership, or product UI
retirement without a separate decision.

## 5. Required Remediation Sequence

1. Start a Python 3.12 environment or Docker Desktop.
2. Run the focused backend Workspace and architecture tests.
3. Run the applicable backend quality checks.
4. Run the frontend production build in a writable output location.
5. Re-review WS-000. Only a review with `BLOCKER = 0` and `MAJOR = 0` may
   authorize a WS-000 integration baseline.

## 5.1 Hunk Separation Record

`apps/api/src/yarvis_api/bootstrap.py` still contains unrelated WS-001 candidate
hunks for deterministic authentication and typed application errors. The WS-000
candidate hunks are limited to:

- `Path` and WorkspacePlatform imports;
- the `workspace_platform` typed ApplicationState field;
- `workspace_api` import and router registration; and
- per-application WorkspacePlatform construction and state assignment.

No index changes were made. If WS-000 later becomes integration-ready, only
those Workspace composition hunks may be staged; authentication and application
error hunks remain outside the WS-000 commit.

## 5.2 Validation Evidence

- Environment precheck on 2026-07-25:
  - repository: `C:/Python Projects/CTO Office`;
  - branch: `main`;
  - HEAD: `c11ec2806019ce1f6bc29c17e0acd5fce68277c6`;
  - staged changes: none;
  - Docker Desktop: unavailable (Docker Engine named pipe does not exist);
  - Python 3.12: unavailable (`python` and `py` are not on PATH);
  - Node: `v24.18.0`; npm: `11.16.0`; Vite: `6.4.3`.
- Canonical backend command identified from `README.md`:
  `docker compose exec api sh -lc "pip install -q -r requirements-dev.txt && pytest -ra"`.
  It was not executable because Docker Desktop is unavailable. No backend tests
  were run; passed/failed/skipped counts are therefore `NOT EXECUTED`.
- Focused frontend Workspace command:
  `npm.cmd test -- --run src/main.test.tsx` — PASS (1 file, 3 tests).
- Full frontend regression command:
  `npm.cmd test -- --run --maxWorkers=1` — PASS (9 files, 21 tests, 0 failed).
- Full frontend regression with default parallel workers: not accepted as a
  product failure; it showed timeouts under concurrent load, while the serial
  rerun passed.
- Frontend production build command:
  `npm.cmd run build -- --outDir ws000-build-verification-2 --emptyOutDir=false`.
  It transformed all 100 modules and rendered chunks, then failed while trying
  to create `C:/Python Projects/CTO Office/apps/web/ws000-build-verification-2`
  with `EPERM: operation not permitted, mkdir`.
- Build lock diagnostic: `tasklist | findstr /I "node vite"` returned no active
  Node or Vite process. Existing `apps/web/dist/assets` was not modified.
  This is classified as an environment write restriction, not an architectural
  or product-build defect.
- `git diff --check`: PASS (line-ending warnings only; no whitespace error).

The remaining MAJOR is an execution-environment validation blocker, not an
unresolved product design finding.

### Validation Retry — 2026-07-25

- Precondition check:
  - repository: `C:/Python Projects/CTO Office` — PASS;
  - branch: `main` — PASS;
  - HEAD: `c11ec2806019ce1f6bc29c17e0acd5fce68277c6` — PASS;
  - staged changes: none — PASS;
  - Docker client: `29.6.1`; Docker Compose: `v5.2.0`.
- Docker Engine availability: FAIL. Both standard and elevated diagnostics fail
  to connect to `//./pipe/dockerDesktopLinuxEngine`; the named pipe does not
  exist.
- Consequence: the official backend services were not started and the canonical
  backend command was not executed. No backend result counts are available.
- Review status remains `BLOCKER=0`, `MAJOR=1`. No staging or commit is
  authorized until the Engine is available and the backend validation passes.

### Validation Retry 2 — 2026-07-25

- Repository, branch, expected HEAD, and empty Git index were reconfirmed.
- Docker Client `29.6.1` and Docker Compose `v5.2.0` are installed.
- Elevated diagnostic shows `desktop-linux` as the selected Docker Desktop
  context, but the required `dockerDesktopLinuxEngine` named pipe still does not
  exist.
- No active Docker Desktop process was reported by the local process check.
- Therefore `postgres` and `api` were not started, and the canonical backend
  suite was not executed. The environment MAJOR remains open; no staging or
  commit is authorized.

## 6. Deferred and Separate Work

- WS-001 Inbox candidate code remains preserved and must not be integrated in
  the WS-000 baseline.
- Proposed architecture documents remain outside the WS-000 implementation
  baseline and require their own review path.
- Line-ending normalization remains separate housekeeping.

## 5.3 Canonical Backend Validation â€” 2026-07-25

- Environment:
  - Docker context: `desktop-linux`;
  - Docker Desktop client/server: `29.6.1`;
  - Docker Compose: `v5.2.0`;
  - Python in the `api` container: `3.12.13`;
  - backend services started through the official Compose configuration:
    `postgres` (healthy) and `api` (running).
- Exact command executed:
  `docker compose exec api sh -lc "pip install -q -r requirements-dev.txt && pytest -ra"`.
- Result: FAIL (exit code `1`). Pytest collected `179` tests: `172` passed,
  `7` failed, `0` skipped, and `0` xfailed, in `96.15s`.
- Workspace-specific evidence in this initial full run:
  - authentication: PASS â€” the unauthenticated Workspace route test passed;
  - projection: PASS â€” Workspace registry/projection test passed;
  - application isolation: PASS â€” two-application Workspace platform isolation
    test passed;
  - repository-root resolution: FAIL â€” the original test's fixed-depth
    expectation raised `IndexError` before exercising the intended assertion.
- WS-001 findings outside WS-000 scope:
  - five deterministic inbound intake tests fail with `DetachedInstanceError`
    after session closure and with unhandled `ApplicationError` paths;
  - the deterministic inbound migration round-trip fails because
    `intake_items` does not exist after upgrade to revision `20260716_09`.
  These failures belong to the uncommitted WS-001 Inbox stream and must not be
  corrected or staged as part of WS-000.
- Classification:
  - `WS000-007` (MAJOR): fixed-depth expected-root calculation in the original
    WS-000 test. It blocks WS-000 integration until revalidated.
  - `WS001-001` (MAJOR, outside WS-000): deterministic inbound service,
    authentication/error handling, and migration incompatibilities. They block
    the full backend regression but are excluded from WS-000 remediation.
- Closure result: `BLOCKER=0`, `MAJOR=1` for WS-000. No staging or commit is
  authorized. The prior Docker availability finding is closed; the current
  blocking condition is the executable test result.

## 5.4 Focused WS-000 Retry â€” 2026-07-25

- Exact command executed:
  `docker compose exec -T api sh -lc "pytest -ra tests/test_workspace_api.py"`.
- Result: FAIL (exit code `1`). `6` tests collected: `5` passed and `1` failed;
  `0` skipped and `0` xfailed, in `23.61s`.
- The fixture-based root-resolution test passes. It creates an explicit
  temporary repository root, provides that root to the public
  `WorkspacePlatform` constructor, and verifies both
  `locate_repository_root()` and the platform retain precisely that root. It
  does not depend on file-depth assumptions and is portable across host and
  container paths.
- Authentication, Workspace registry, application isolation, and authenticated
  core endpoint tests pass.
- The repository-state projection test fails because the `api` container's
  mounted filesystem exposes `/app` without the repository-level `AGENTS.md`
  and `docs/development/CURRENT_SPRINT.md`. Consequently its Workspace state
  reports `current_sprint = UNKNOWN` instead of the repository value.
- Classification: `WS000-008` â€” MAJOR. This is a WS-000 composition/runtime
  issue: the container cannot access the repository root that the Development
  Workspace is intended to project. It is not a test-only defect and cannot be
  resolved by weakening the assertion. The requested scope prohibits changing
  production composition during this correction, so the finding remains open.
- Gate result: `BLOCKER=0`, `MAJOR=1`. Per the controlled-close instructions,
  no full-suite rerun, isolated-worktree validation, staging, or commit was
  performed after this failure.

## Closing Statement

The approved scope decisions are reflected in the candidate implementation.
The primary tree remains intentionally unstaged because it contains separate
WS-001 candidate work and unratified documents. WS-000 now requires isolated
worktree validation before it may be integrated.

## 5.5 Explicit Governed Root Validation â€” 2026-07-25

- Approved correction implemented:
  - `YARVIS_WORKSPACE_REPOSITORY_ROOT` is a typed Settings value;
  - the API container receives `/workspace-repository` as a read-only corpus;
  - only `AGENTS.md`, `docs/development`, `docs/engineering`, and the required
    `apps/api/workspaces` manifest directory are mounted there;
  - Workspace validates canonical root identity, required contained markers,
    missing roots, filesystem roots, and marker symlinks that escape the root;
  - scanner output is restricted to the governed corpus, allowlisted paths and
    types, a size limit, and secret-like filenames are excluded.
- Focused command after installing repository-defined development dependencies:
  `docker compose exec -T api sh -lc "pytest -ra tests/test_workspace_api.py"`.
  Result: PASS, `9` passed, `0` failed, `0` skipped, `0` xfailed in `14.56s`.
- Focused evidence: authentication, explicit temporary-root injection, missing
  root rejection, required-marker validation, escaping marker-symlink rejection,
  sprint projection, application isolation, authenticated projections, and the
  real configured container corpus all passed.
- Canonical command:
  `docker compose exec -T api sh -lc "pip install -q -r requirements-dev.txt && pytest -ra"`.
  Result: `183` collected; `177` passed, `6` failed, `0` skipped, `0` xfailed
  in `97.26s`.
- All six remaining failures are WS-001-only: five deterministic inbound intake
  tests fail on detached ORM instances or unhandled application errors, and one
  deterministic inbound migration round-trip fails because `intake_items` is
  absent at revision `20260716_09`. No WS-000 test fails.
- WS000-008 is resolved by the explicit, minimal, read-only corpus composition.
  `BLOCKER=0`; `MAJOR=0` for WS-000 implementation evidence. A temporary
  worktree validation remains required before staging because the primary tree
  still mixes WS-001 candidates and unratified architecture documents.
