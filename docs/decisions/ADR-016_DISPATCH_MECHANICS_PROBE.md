# ADR-016: Authorize a zero-persistence Dispatch mechanics probe (TD-005, first slice)

- Status: Accepted
- Decision authority: Guillermo, Architecture Authority
- Date: 2026-09-05
- Implementation authorization: exactly the 6 items listed under "Decision"
  below — no other scope. See "Explicit non-goals."

## Context

TD-005 (`YARVIS_ROADMAP_AND_TECHNICAL_DEBT.md`) records that `Dispatcher`
(`apps/api/src/yarvis_api/dispatch/dispatcher.py`) has zero registered
handlers, and `main.py`/`bootstrap.py` compose the application with an empty
`handlers` tuple. 56 Command contracts exist in `canonical_contracts.py`; none
are wired.

`DISPATCH_DESIGN_AMENDMENT_001.md` (F-009) already defines the ratified
ownership model for Dispatch, Handler, Unit of Work, and Repository, and
states the amendment "creates no runtime code, tests, handlers, repositories,
or bootstrap changes." No prior ADR has granted implementation authority for
any of it.

An initial attempt to scope a first slice around an existing verified
contract (`IC-DOCUMENT-CMD-004`, `ArchiveDocument`) surfaced a real
incompatibility: `DocumentRegistryService.archive()` opens and commits its
own internal `UnitOfWork`, which conflicts with F-009's model where Dispatch
owns Unit-of-Work construction and the Handler only expresses commit/rollback
intent through the narrow `CommandUnitOfWork` port. Wiring any of the 56
existing Command contracts as-is would require first resolving how a Handler
obtains a Repository bound to the Dispatch-created Session — F-009 assigns
Repository "persistence operations only; no Session acquisition," but no
ratified mechanism yet exists for constructing or injecting that Repository
into a Handler. That resolution is out of scope here and is registered below
as follow-on debt, not solved by this ADR.

## Decision

Authorize a single, isolated, zero-persistence-write implementation slice
whose sole purpose is to prove the Dispatch → Handler → Unit-of-Work
mechanics described in `DISPATCH_DESIGN_AMENDMENT_001.md` Section 7, using no
new or existing business Command contract and no Repository.

Specifically, this ADR authorizes:

1. **Amendment to this ADR's original constraint:** none of the 12 existing
   modules in `canonical_modules.py` (`identity`, `governance`,
   `relationship`, `observation_evidence`, `knowledge`,
   `decision_intelligence`, `execution`, `operational_execution`,
   `document_registry`, `automation`, `mission_control`,
   `netpay_merchant_operations`) is a technical/infrastructure bounded
   context — all 12 are genuine business domains. Attributing a dispatch
   mechanics probe to any of them would misattribute ownership, the exact
   failure this ADR exists to avoid. This ADR therefore authorizes exactly
   one new `ApplicationModule`: `module_id="platform"`,
   `display_name="Platform"`. This module is scoped to technical/dispatch
   infrastructure concerns only — it owns no business capability, Task,
   Document, or domain event, now or by implication for future work. Any
   future contract placed under `platform` requires its own authorization;
   this ADR authorizes only the one probe contract below.
2. One new Command contract, `IC-PLATFORM-CMD-DISPATCH-PROBE`, registered in
   `canonical_contracts.py` under `owner_module_id="platform"`,
   `owning_context="Platform"`, `lifecycle = RATIFIED`,
   `operational_status = VERIFIED`, scoped only to this probe.
3. One `HandlerDefinition` for that contract. The handler receives
   `(CommandEnvelope, CommandUnitOfWork)`, performs **no persistence
   operation of any kind** (no session access, no repository, no model
   writes), and either calls `facade.commit()` unconditionally, or — in a
   second, test-only variant — raises before calling commit, to exercise
   both paths.
4. Registration of that single handler in the `handlers` tuple passed to
   `build_handler_registry` in `bootstrap.py`/`main.py`. The tuple must
   contain only this one handler; no other contract may be wired under this
   ADR.
5. Integration tests covering the F-009 Section 7 requirements: explicit
   commit, explicit rollback, active-return rejection
   (`IncompleteTransactionError`), pre-commit and post-commit handler
   failure, and deterministic disposal.
6. A documentation update to TD-005 in
   `YARVIS_ROADMAP_AND_TECHNICAL_DEBT.md`, marking it "mechanism proven,
   zero business handlers wired," and a new TD entry (next available ID)
   recording that Repository/Session-injection design for real Command
   handlers remains unresolved and unauthorized.

## Explicit non-goals

This ADR does not authorize, and Codex must not implement:

- Any of the 56 existing Command contracts' handlers.
- Any change to `DocumentRegistryService` or any other existing service.
- Any new Repository class or Session-injection mechanism for handlers.
- Any HTTP route migration to use `dispatcher.dispatch()`.
- Closing TD-005.

## Consequences

- Provides real, tested evidence that the Dispatch mechanism works before any
  business logic depends on it.
- Surfaces the Repository/Session-injection gap as its own named, scoped
  decision to make later, instead of solving it implicitly inside a
  business-contract handler.
- Keeps the blast radius at zero for any currently running production route.
