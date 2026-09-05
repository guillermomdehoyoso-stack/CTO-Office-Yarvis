# YARVIS
# Dispatch Design Amendment 003 (Proposal) — Revision 4

## Status: Engineering Design Proposal — not yet reviewed; creates no runtime code

## 1. Amendment Identity

**Amendment ID:** `DISPATCH-DESIGN-AMENDMENT-003`
**Affected work package:** F-009 — Dispatch (Repository composition)
**Phase:** Design Proposal, Revision 4
**Addresses:** the design question recorded in TD-009
(`YARVIS_ROADMAP_AND_TECHNICAL_DEBT.md`); TD-009 remains unresolved and
unauthorized until a separately ratified and implemented work package
provides conformance evidence.
**Relationship to Amendment 002:** If ratified through an Accepted ADR, this
amendment would supersede *only* Amendment 002's deferral of factories/
dependency injection (the paragraph stating Handler composition is
deferred). It would change no other invariant of Amendment 002:
`CommandHandler`'s two-argument shape, the commit/rollback-only facade,
one-UoW-per-command, and the prohibition on Dispatch deciding business
outcomes all remain exactly as ratified.

## 2. Reason

Prior revisions of this proposal were independently reviewed and
returned `ACCEPT WITH AMENDMENTS` against the real repository state. This revision incorporates
every required correction from that review. See Section 13 for the
observation-by-observation disposition.

## 3. Proposed Ownership Model (extends Amendment 001/002)

| Participant | Canonical responsibility |
| --- | --- |
| Dispatch | Unchanged from Amendment 001/002, plus: for a Handler registered as a factory, calls that factory with the active Unit of Work's `.session` — only after `UnitOfWork.__enter__` has succeeded, only inside the active `with unit_of_work:` block, only before the resulting Handler is invoked — to obtain one ready-to-invoke `CommandHandler`. |
| Handler factory (infrastructure/composition root only) | Receives the active Session, constructs concrete Repository instance(s), and returns a closed-over `CommandHandler`. Never exposed to, or callable by, application/business code. Dispatch stores and invokes this callable; it does not import or know any concrete business Repository type. |
| Handler | Unchanged: a two-argument callable, `(CommandEnvelope, CommandUnitOfWork) -> object \| None`. Never receives a Session, a concrete Unit of Work, a factory, or any service-locator-like object. A factory-built Handler receives its Repository dependencies through its own constructor/closure. |
| Unit of Work | Unchanged. `.session` remains the only sanctioned Repository-construction seam, reachable only by a registered Handler factory. |
| Repository | Unchanged: persistence operations only. Receives an already-active Session; must not acquire, commit, rollback, close, or dispose it. |

## 4. `HandlerDefinition` Change (positional-compatible)

`CommandHandler` (`dispatch/models.py`) is **not changed**:

```python
CommandHandler = Callable[[CommandEnvelope, CommandUnitOfWork], object | None]
```

`HandlerDefinition` gains one new field, placed **after** `handler_name` to
preserve every existing positional call site:

```python
@dataclass(frozen=True, slots=True)
class HandlerDefinition:
    interaction_contract_id: str
    owner_module_id: str
    owning_context: str
    handler: CommandHandler | None = None
    handler_name: str = ""
    handler_factory: HandlerFactory | None = None
```

`handler_name` preserves its existing positional location and its existing
non-empty-string validation. Existing static registrations (e.g. the
ADR-016 probe, and every current test call site such as
`HandlerDefinition(contract_id, owner, context, handler, "name")`) remain
valid without modification.

Registration validation (`HandlerRegistry.register()`) is extended to reject
a definition unless **exactly one** of `handler` or `handler_factory` is a
synchronous callable — neither set, or both set, is a registration error.

## 5. Dispatch Sequence and Factory Invocation

```text
Dispatch validates command and resolves exactly one owner HandlerDefinition
        ↓
Dispatch creates one OperationScope and one Unit of Work
        ↓
Dispatch enters the Unit of Work (__enter__ succeeds)
        ↓
If handler_factory is set: Dispatch calls handler_factory(unit_of_work.session)
  to obtain one CommandHandler                                  [factory boundary]
        ↓
Dispatch invokes the resolved Handler with (command, facade)
        ↓
Handler performs application behavior and explicit commit/rollback
        ↓
Handler returns
        ↓
Dispatch verifies a terminal transactional state
        ↓
Dispatch disposes and returns the handler result
```

The factory call happens strictly inside the existing `with unit_of_work:`
block, so any exception it raises is handled by the same cleanup path as any
other Handler exception — no new error-handling code path is introduced.

## 6. Factory Failure Semantics (precise, no guaranteed disposal)

If `handler_factory(...)` raises:

- The factory's exception is preserved as primary.
- The existing `UnitOfWork` cleanup path (triggered by `__exit__` on an
  active Unit of Work) attempts exactly one rollback and one Session close,
  identically to a Handler-raised exception today.
- If that rollback and close succeed, the Unit of Work reaches `DISPOSED`
  and the factory's exception propagates.
- If cleanup itself fails, the Unit of Work follows its existing `FAILED`
  lifecycle path (per `unit_of_work.py`'s current behavior) — this proposal
  does **not** promise `DISPOSED` unconditionally. `FAILED` is an accepted,
  pre-existing outcome of double failure, not a new case this amendment
  introduces.
- The Handler is never invoked if the factory raised.

## 7. `HandlerFactory` Typing — Zero Runtime Coupling, Explicit Static Dependency

```python
from __future__ import annotations  # already present in dispatch/models.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

HandlerFactory = Callable[["Session"], "CommandHandler"]
```

**Correction from Revision 3:** the mechanism that prevents a `NameError` at
import time here is **not** `from __future__ import annotations` (PEP 563).
PEP 563 only defers evaluation of annotations in annotation position
(function parameters/return types, variable annotations); it has no effect
on the right-hand side of a plain alias assignment like the one above. What
actually prevents the `NameError` is that `"Session"` and `"CommandHandler"`
are written as quoted forward-reference strings (the PEP 484 mechanism,
independent of PEP 563) — `typing.Callable[...]` accepts string forward
references as ordinary values and does not resolve them at assignment time.
This was verified directly: the identical alias, written with the same
quoted strings, behaves identically whether or not
`from __future__ import annotations` is present; removing the quotes (not
the future-import) is what produces a real `NameError`.

Given that, two separate claims must be kept distinct and stated honestly:

- **Runtime coupling: zero.** The `if TYPE_CHECKING:` block never executes
  outside static analysis; `dispatch/models.py` imports no SQLAlchemy symbol
  at runtime, in production or otherwise. This was verified empirically:
  `mypy --strict` against this exact pattern correctly resolved `"Session"`
  to the real type and rejected a factory typed against the wrong parameter
  type as a genuine type error — this is a fully checked type, not `Any` or
  an unchecked cast.
- **Static/architectural coupling: real, and accepted, not hidden.** The
  `TYPE_CHECKING` import is a visible, real dependency edge
  (`dispatch/models.py → sqlalchemy.orm.Session`) for any type checker,
  linter, or human reading the file. This proposal does not claim "zero
  coupling" in absolute terms — only zero *runtime* coupling. The static
  dependency is judged acceptable because it exists solely to name a type
  for a composition-time contract, not to use SQLAlchemy's behavior, and it
  is confined to one alias declaration.

**Contract vs. implementation, made explicit:** `HandlerFactory` the *type
alias* (the contract shape: "a callable from a Session to a CommandHandler")
is declared in `dispatch/models.py` and carries the static dependency above.
Concrete factory *implementations* — actual functions like the illustrative
`build_archive_document_handler` in Section 8 — live in
infrastructure/persistence-adjacent modules, never in `dispatch/`, and do
import SQLAlchemy at runtime there, which is expected and unremarkable for
infrastructure code. Dispatch stores and invokes a registered
`HandlerFactory`-typed callable; it never imports or knows any concrete
business Repository type.

## 8. Illustrative Pseudocode (not existing code; not authorized by this proposal)

```python
# Illustrative only. ArchiveDocumentRepositoryPort and SqlDocumentRepository
# do not exist today and are not created by this proposal.

class ArchiveDocumentHandler:
    def __init__(self, documents: ArchiveDocumentRepositoryPort) -> None:
        self._documents = documents

    def __call__(self, envelope: CommandEnvelope, transaction: CommandUnitOfWork) -> object | None:
        self._documents.archive(envelope.payload)
        transaction.commit()
        return None


def build_archive_document_handler(session: Session) -> CommandHandler:
    return ArchiveDocumentHandler(SqlDocumentRepository(session))
```

## 9. Non-goals

This proposal does not:

- Change `CommandHandler`'s signature or `CommandUnitOfWork`.
- Introduce a `RepositoryBundle`, a type-keyed map, or any Service Locator.
- Have Dispatch import, construct, or know any concrete business Repository
  type.
- Use constructor-shape introspection; every factory is an explicitly
  registered function.
- Migrate `DocumentRegistryService` or any other existing service.
- Wire any of the 56 existing business Command contracts, or authorize any
  HTTP route migration, by implication. (There are 57 Command contracts
  total today: 56 business contracts plus the ADR-016 platform probe.)
- Guarantee the Unit of Work reaches `DISPOSED` when both the Handler/factory
  and cleanup fail — see Section 6.
- Claim, as an absolute language-level guarantee, that a Handler can never
  reach a Session by any path. The guarantee is structural: no sanctioned
  API exposes it, and Handler classes depend only on typed Protocols, never
  on SQLAlchemy.

## 10. ArchiveDocument as Review Vertical Slice — Not Yet Authorized

`IC-DOCUMENT-CMD-004` is named as the candidate first slice for a *future,
separately authorized* implementation ADR — this proposal authorizes no
implementation of it. Its actual current semantics
(`services/document_registry.py::archive`, tested in
`test_document_archive.py`) must be preserved exactly, not simplified by
analogy:

| Case | Current behavior |
| --- | --- |
| Success | Archives, increments version, records `document.archived`, writes an idempotency receipt, commits. |
| Expected-version conflict | Rejected if `expected_aggregate_version` does not match the current version. |
| Already-archived conflict | Rejected if `lifecycle_status` is already `archived`. |
| Matching idempotency replay | Same idempotency key and same request fingerprint returns the already-archived result without re-executing. |
| Mismatched-fingerprint conflict | Same idempotency key with a different fingerprint is rejected as a conflict. |
| Concurrent race | The current implementation catches a unique-constraint violation and opens a **second** Unit of Work to re-read the winning receipt. |

**Open design question, not resolved by this proposal:** the concurrent-race
case's second-UnitOfWork re-read cannot be carried over into a single-UoW
Dispatch model without a separate, explicit design. This proposal does not
authorize a second Unit of Work inside a dispatched Handler, and does not
propose a replacement mechanism.

**Ratification condition:** this proposal itself may be ratified with this
question left open — it does not block the design's approval. What it does
block is stated explicitly: **no implementation ADR for `ArchiveDocument`
(or any other Command relying on this factory mechanism with equivalent
concurrent-idempotency semantics) may be accepted while the concurrent-race
re-read remains unresolved and untested.** An implementation ADR must either
(a) present and ratify a specific single-UoW-compatible resolution, with a
test proving it, or (b) explicitly carry the gap forward as a named,
accepted exception with its own authority and containment, per AR-001's
ratification-gate requirement for "zero unresolved BLOCKER or MAJOR findings,
unless the ADR explicitly accepts a named exception." Silence on this point
in a future implementation ADR is not acceptable; the gap must be addressed
by name.

Dispatch/Unit-of-Work rollback tests (Section 11) validate Dispatch
mechanics — they are not a stand-in for, and must not be presented as, an
`ArchiveDocument` business-level rollback outcome, which does not exist in
the current service.

## 11. Test Requirements

An implementation must test: `HandlerRegistry.register()` rejects a
definition with both `handler` and `handler_factory` set, and rejects one
with neither; existing static registrations (positional or keyword) remain
valid unmodified; a factory-backed Handler receives a Repository instance
bound to the dispatch-active Session; the ADR-016 probe dispatches
unchanged; a factory that raises during construction surfaces as a
dispatch-time error before the Handler is invoked, with cleanup behavior
exactly as described in Section 6 (including the `FAILED`-on-double-failure
case); and, only once a separate implementation ADR authorizes it, the
`ArchiveDocument` vertical slice reproduces every case in Section 10's table
except the concurrent-race case, which remains explicitly open.

## 12. Implementation Readiness

This design requires independent engineering review and ratification before
any implementation-authority ADR may cite it, per AR-001's ratification
gate. It creates no runtime code, tests, Repository classes, or bootstrap
changes. It does not authorize implementation, a Repository, a real
Handler, an HTTP route migration, a service migration, any other contract,
or an implementation ADR.

## 13. Disposition of Prior Review Observations

| Observation (prior review) | Disposition |
| --- | --- |
| `CommandHandler` must stay two-argument | RESOLVED — unchanged, Section 3/4. |
| ADR-016 probe must remain functional unmodified | RESOLVED — untouched, uses `handler`, not `handler_factory`. |
| `HandlerDefinition` field order must preserve positional compatibility | RESOLVED — `handler_factory` placed after `handler_name`, Section 4. |
| `handler_name: str = ...` is not a valid default | RESOLVED — corrected to `handler_name: str = ""`, existing validation unchanged. |
| Exactly one of `handler`/`handler_factory` required | RESOLVED — Section 4/5. |
| Factory must run inside an active Unit of Work | RESOLVED — Section 5. |
| Cleanup guarantee was overstated (must allow `FAILED`) | RESOLVED — Section 6 now states `FAILED` as an accepted outcome. |
| `dispatch/models.py` must not runtime-couple to SQLAlchemy | RESOLVED for runtime coupling (verified empirically with `mypy --strict`); static/architectural coupling via the `TYPE_CHECKING` import is real and now stated explicitly, not claimed as "zero" — Section 7. Revision 3's attribution of the mechanism to `from __future__ import annotations` was corrected: the operative mechanism is quoted forward-reference strings (PEP 484), independent of PEP 563. |
| Section 7 apparent contradiction (alias in `dispatch/models.py` vs. "factories live in infrastructure") | RESOLVED — Section 7 now explicitly distinguishes the factory *contract* (type alias, in `dispatch/models.py`, static-only dependency) from concrete factory *implementations* (in infrastructure, real runtime SQLAlchemy import there). |
| Sections 10/11 tension: open concurrency question vs. test requirements | RESOLVED — Section 10 now states explicitly that this proposal may be ratified with the question open, but no `ArchiveDocument` implementation ADR may be accepted until it is resolved and tested, per AR-001's named-exception requirement. |
| `SqlDocumentRepository`/port must not be implied to exist | RESOLVED — explicitly labeled illustrative-only, Sections 7–8. |
| ArchiveDocument semantics must match real service, not analogy | RESOLVED — Section 10 table sourced from actual service/tests. |
| Concurrent-race re-read cannot be silently authorized | RESOLVED as an explicit open question — Section 10; no second UoW authorized. |
| Rollback tests must not invent an ArchiveDocument business result | RESOLVED — Section 10/11 distinguish Dispatch mechanics from business semantics. |
| Contract count (56 vs 57) must be accurate | RESOLVED — Section 9 states 57 total (56 business + 1 probe). |
| No HTTP route or other contract authorized by implication | RESOLVED — Section 9/12. |
