# ADR-017: Ratify Dispatch Handler Factory Composition

## Status

**ACCEPTED — RATIFIED ARCHITECTURAL DECISION — IMPLEMENTATION AUTHORIZATION AS BOUNDED BELOW**

**Date:** 2026-09-04
**Decision authority:** Guillermo de Hoyos, Architecture Authority
**Conformance authority:** Guillermo de Hoyos, Architecture Authority
**Conformance decision date:** 2026-09-05
**Authorized implementation package:** `ADR-017 authorized platform implementation package` only.
**Accepted exceptions:** None.
**Implementation status:** IMPLEMENTED — CONFORMANT — EVIDENCE GATE PASSED
**Implementation commit:** `1314ef27460ceed30c36770f015b330a1862775b`

## Proposal Identity and Evidence

**Ratified proposal:** `DISPATCH-DESIGN-AMENDMENT-003`
**Proposal file:**
`docs/engineering/DISPATCH_DESIGN_AMENDMENT_003_PROPOSAL.md`
**Verified canonical SHA-256 (UTF-8 without BOM; LF-normalized line endings):**
`1C6FA91A54FFD8D8E5BF5CA11711D4B93549FA08604CF9DDA65CCB131113B710`

**Governing and related sources:**

- `docs/engineering/DISPATCH_DESIGN_AMENDMENT_001.md`
- `docs/engineering/DISPATCH_DESIGN_AMENDMENT_002.md`
- `docs/decisions/ADR-016_DISPATCH_MECHANICS_PROBE.md`
- `docs/architecture/AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md`
- TD-009 in `docs/architecture/YARVIS_ROADMAP_AND_TECHNICAL_DEBT.md`

## Context

Amendments 001 and 002 establish synchronous owner-Command Dispatch, one
OperationScope / UnitOfWork / Session per accepted command, a restricted
`CommandUnitOfWork` facade, explicit handler commit or rollback intent, and
deterministic UnitOfWork cleanup.

ADR-016 proved those mechanics with the isolated
`IC-PLATFORM-CMD-DISPATCH-PROBE` static handler. It did not authorize
Repository construction, Session injection, a business handler,
`DocumentRegistryService` changes, or route migration.

TD-009 remains open because a future handler may need a Repository instance
bound to Dispatch's active UnitOfWork Session. The ratified proposal defines
a narrow factory-composition mechanism while preserving the exact public
handler shape:

```python
CommandHandler = Callable[[CommandEnvelope, CommandUnitOfWork], object | None]
```

`IC-DOCUMENT-CMD-004` / ArchiveDocument is not included. Its current
idempotency race resolves a unique-constraint collision by opening a second
UnitOfWork to read the winning receipt; that behavior requires a separate
future decision.

## Decision

This ADR ratifies `DISPATCH-DESIGN-AMENDMENT-003` at the identified SHA-256
and authorizes exactly the `ADR-017 authorized platform implementation
package`, subject to the Authorized File Boundary, Explicit Prohibitions, and
Evidence Gate below.

The authorized package may:

1. Define `HandlerFactory` using the ratified contract from an active
   SQLAlchemy Session to a two-argument `CommandHandler`.
2. Add optional `handler_factory` to `HandlerDefinition` after
   `handler_name`, preserving existing positional registrations.
3. Require exactly one synchronous callable among `handler` and
   `handler_factory`.
4. Resolve a registered factory only after `UnitOfWork.__enter__` succeeds and
   only inside the active `with unit_of_work:` block.
5. Invoke the resulting `CommandHandler` with exactly
   `(CommandEnvelope, CommandUnitOfWork)`.
6. Preserve existing UnitOfWork cleanup, primary-exception priority, rollback,
   Session close, and `FAILED` semantics for cleanup double failures.
7. Add synthetic factory and synthetic repository-binding tests only.
8. Add regression coverage proving the ADR-016 probe remains unchanged.
9. Permit the explicit static-only `TYPE_CHECKING` dependency on
   `sqlalchemy.orm.Session` in `dispatch/models.py`; no runtime SQLAlchemy
   import may be introduced there.

## Authorized File Boundary

Only the following files may be changed by the ADR-017 authorized platform
implementation package:

- `apps/api/src/yarvis_api/dispatch/models.py`
- `apps/api/src/yarvis_api/dispatch/dispatcher.py`
- `apps/api/src/yarvis_api/dispatch/registry.py`
- `apps/api/tests/test_handler_registry.py`
- `apps/api/tests/test_dispatcher.py`
- `apps/api/tests/test_unit_of_work.py`
- `apps/api/tests/test_dispatch_mechanics_probe.py`

These test files may change only to demonstrate the authorized models,
Registry, Dispatcher, UnitOfWork interaction, and unchanged ADR-016 probe.

The following are expressly outside the authorized file boundary:

- `apps/api/src/yarvis_api/persistence/unit_of_work.py`
- `apps/api/src/yarvis_api/bootstrap.py`, absent later specific authorization
- all business services
- all business Repositories
- HTTP routes
- canonical or application contracts
- persistent models
- migrations and database changes
- configuration
- deployment artifacts

If implementation cannot proceed without changing an excluded file, work must
stop and request an ADR amendment. It must not infer an exception.

## Explicit Prohibitions

This ADR does not authorize:

- `ArchiveDocumentHandler`, `SqlDocumentRepository`, or any business
  Repository;
- any change to `DocumentRegistryService`;
- resolving or changing ArchiveDocument concurrency or idempotency;
- a second UnitOfWork inside a Handler;
- wiring any of the 56 business Command contracts;
- HTTP route migration or public API behavior changes;
- DI-002 migration or canonical-contract modification;
- database, schema, or migration changes;
- authentication, Founder Bootstrap, sessions, secrets, or deployment changes;
- authorization of any adjacent command, Repository, route, or work package by
  implication.

The ADR-016 platform probe remains the only Handler registered by the default
runtime composition root unless another separately authorized decision states
otherwise.

## Consequences

### Positive

- Enables future repositories to share Dispatch's active transaction.
- Preserves the two-argument `CommandHandler` contract.
- Preserves explicit constructor injection.
- Avoids `RepositoryBundle` and service-locator behavior.

### Costs and Risks

- Accepts an explicit static `TYPE_CHECKING` dependency on SQLAlchemy
  `Session`.
- Adds a second `HandlerDefinition` resolution mode.
- Provides no business capability by itself.
- Factories could become opaque composition containers if allowed to grow.

### Mitigations

- One explicit factory per separately authorized contract.
- Concrete dependencies remain visible through constructor injection.
- Registry validation and architectural boundary tests are required.
- No business handler may be added without a separate ADR.

## Evidence Gate Before Package Completion

The authorized package is complete only when evidence demonstrates:

1. Focused `HandlerDefinition` and HandlerRegistry validation, including
   rejection of both/neither callable configuration.
2. Positional compatibility of existing static registrations.
3. Factory success with a synthetic Repository bound to the Dispatch-active
   UnitOfWork Session.
4. Factory construction failure before handler invocation.
5. Normal rollback and Session close after factory failure.
6. Existing `FAILED` semantics when factory failure and cleanup failure occur.
7. The Handler is never invoked when factory construction fails.
8. The ADR-016 probe dispatches unchanged.
9. No runtime SQLAlchemy import is added to `dispatch/models.py`; the accepted
   static `TYPE_CHECKING` dependency is explicit and reviewable.
10. Pyright, Ruff, focused Dispatch/UoW/Registry tests, relevant regression
    suite, and `git diff --check` pass.
11. Review confirms no file outside the Authorized File Boundary changed.

## Implementation and Conformance Evidence

The `ADR-017 authorized platform implementation package` was implemented in
commit `1314ef27460ceed30c36770f015b330a1862775b`. The local branch and
`origin/feat/operational-intake-spine` were verified at that same commit.

The final ADR-017 gate returned `PASS` with no accepted exceptions:

| Evidence | Result |
| --- | --- |
| PostgreSQL-backed Dispatch test | `1 passed in 14.35s` |
| Relevant Dispatch/Registry/UnitOfWork/ADR-016 suite | `35 passed in 78.60s` |
| Focused HandlerRegistry tests | `7 passed` |
| Focused Ruff check | PASS |
| Focused Ruff format check | PASS |
| Focused Pyright | `0 errors, 0 warnings` |
| `git diff --check` | PASS |
| Authorized File Boundary review | PASS — no file outside the boundary changed |

The implementation adds no business Handler or Repository and changes no
canonical contract, HTTP route, business service, persistent model, migration,
database schema, authentication, Founder Bootstrap, configuration, deployment,
or default runtime Handler registration. The ADR-016 platform probe remains
the only Handler registered by the default runtime composition root.

This evidence closes only the platform-level Handler-factory composition work
authorized by ADR-017. It does not authorize `ArchiveDocument`,
`SqlDocumentRepository`, any business Repository, any of the 56 business
Commands, or any route migration.

## TD-009 Status

TD-009 was closed on 2026-09-05 after the exact authorized platform-level
package was implemented, tested, independently reviewed, and accompanied by
the conformance evidence above. Closure resolves only the Handler-factory
composition question recorded by TD-009. It grants no implementation authority
for `ArchiveDocument`, a business Repository, a business Command Handler, or an
HTTP route.

## ArchiveDocument Boundary

ArchiveDocument requires a separate, later ADR before any handler,
Repository, route, or Dispatch registration may be implemented. That ADR must
either ratify and test a single-UnitOfWork-compatible resolution for the
concurrent idempotency race, or explicitly accept a named and contained
exception under AR-001.

## Rollback Strategy

If the authorized platform-level package must be reversed, revert only that
package's implementation and tests. Amendments 001 and 002, ADR-016, the
static probe, existing service-owned transactions, and all business handlers
remain intact. No data rollback is required because this ADR authorizes no
schema or persistence change.

## Ratification Record

Guillermo de Hoyos, acting as Architecture Authority, ratified
`DISPATCH-DESIGN-AMENDMENT-003` and accepted ADR-017 on 2026-09-04. The
Authority authorized exclusively the `ADR-017 authorized platform
implementation package` within the Authorized File Boundary and Evidence
Gate, accepted no additional exception, and did not authorize ArchiveDocument,
business Repositories, HTTP routes, migrations, database changes,
authentication, Founder Bootstrap, deployment, or any other contract by
implication.
