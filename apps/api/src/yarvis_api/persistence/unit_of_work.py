"""Canonical synchronous transactional boundary for one Yarvis operation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from sqlalchemy.orm import Session

from yarvis_api.persistence.runtime import PersistenceRuntime

_SESSION_OWNER_ATTRIBUTE = "_yarvis_unit_of_work_owner"


class UnitOfWorkError(RuntimeError):
    """Base error for Unit of Work architectural misuse."""


class UnitOfWorkLifecycleError(UnitOfWorkError):
    """Raised when an operation is invalid for the current lifecycle state."""

    def __init__(self, operation: str, state: UnitOfWorkState) -> None:
        super().__init__(f"unit of work cannot {operation} while {state.value}")
        self.operation = operation
        self.state = state


class UnitOfWorkDisposedError(UnitOfWorkLifecycleError):
    """Raised when an operation requires a disposed Unit of Work."""


class NestedUnitOfWorkError(UnitOfWorkError):
    """Raised when an operation scope already has an active Unit of Work."""


class RepositoryOwnershipError(UnitOfWorkError):
    """Raised when repository access is requested outside its owned lifecycle."""


class UnitOfWorkState(StrEnum):
    """Lifecycle states ratified by the Unit of Work design."""

    NEW = "NEW"
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"
    DISPOSED = "DISPOSED"


@dataclass(slots=True)
class OperationScope:
    """Explicit, per-operation nesting guard with no ambient process state."""

    _active_unit_of_work: object | None = field(default=None, init=False, repr=False)

    def activate(self, unit_of_work: object) -> None:
        if self._active_unit_of_work is not None:
            raise NestedUnitOfWorkError("operation scope already has an active unit of work")
        self._active_unit_of_work = unit_of_work

    def release(self, unit_of_work: object) -> None:
        if self._active_unit_of_work is unit_of_work:
            self._active_unit_of_work = None


@dataclass(slots=True)
class UnitOfWork:
    """Own one explicit Session and transaction for one context-local operation."""

    persistence: PersistenceRuntime
    operation_scope: OperationScope
    _state: UnitOfWorkState = field(default=UnitOfWorkState.NEW, init=False)
    _session: Session | None = field(default=None, init=False, repr=False)
    _rollback_attempted: bool = field(default=False, init=False, repr=False)

    @property
    def state(self) -> UnitOfWorkState:
        """Expose the safe lifecycle state for application and conformance checks."""

        return self._state

    @property
    def session(self) -> Session:
        """Return the owned active Session for explicit context infrastructure wiring."""

        if self._state == UnitOfWorkState.DISPOSED:
            raise UnitOfWorkDisposedError("access repository session", self._state)
        if self._state != UnitOfWorkState.ACTIVE or self._session is None:
            raise RepositoryOwnershipError("repository session requires an active unit of work")
        return self._session

    def __enter__(self) -> Self:
        """Acquire one Session and explicitly activate its transaction."""

        self._require_new("enter")
        self.operation_scope.activate(self)
        try:
            self._session = self.persistence.create_session()
        except BaseException:
            self._state = UnitOfWorkState.FAILED
            self.operation_scope.release(self)
            raise
        try:
            self._claim_session(self._session)
        except RepositoryOwnershipError:
            self._session = None
            self._state = UnitOfWorkState.FAILED
            self.operation_scope.release(self)
            raise
        try:
            self._session.begin()
        except BaseException as activation_error:
            self._state = UnitOfWorkState.FAILED
            self._close_preserving(activation_error)
            self.operation_scope.release(self)
            raise
        self._state = UnitOfWorkState.ACTIVE
        return self

    def __exit__(self, exc_type: object, exc: BaseException | None, traceback: object) -> bool:
        """Never commit implicitly; preserve a body exception over cleanup failure."""

        if exc is not None:
            try:
                self.dispose()
            except BaseException as cleanup_error:
                exc.add_note(f"unit of work cleanup failed: {cleanup_error.__class__.__name__}")
            return False
        self.dispose()
        return False

    def commit(self) -> None:
        """Commit the owned active transaction exactly once."""

        self._require_active("commit")
        try:
            self.session.commit()
        except BaseException as commit_error:
            self._state = UnitOfWorkState.FAILED
            self._rollback_for_cleanup(commit_error)
            raise
        self._state = UnitOfWorkState.COMMITTED

    def rollback(self) -> None:
        """Roll back the owned active transaction exactly once."""

        self._require_active("rollback")
        self._rollback_attempted = True
        try:
            self.session.rollback()
        except BaseException:
            self._state = UnitOfWorkState.FAILED
            raise
        self._state = UnitOfWorkState.ROLLED_BACK

    def dispose(self) -> None:
        """Release owned resources without implicit commit and with idempotent disposal."""

        if self._state == UnitOfWorkState.DISPOSED:
            return
        if self._state == UnitOfWorkState.NEW:
            self._state = UnitOfWorkState.DISPOSED
            self.operation_scope.release(self)
            return

        cleanup_error: BaseException | None = None
        if self._state == UnitOfWorkState.ACTIVE:
            try:
                self._rollback_for_disposal()
            except BaseException as error:
                cleanup_error = error
                self._state = UnitOfWorkState.FAILED

        try:
            self._close_session()
        except BaseException as error:
            if cleanup_error is not None:
                cleanup_error.add_note(f"unit of work close failed: {error.__class__.__name__}")
            else:
                cleanup_error = error
            self._state = UnitOfWorkState.FAILED

        self.operation_scope.release(self)
        if cleanup_error is not None:
            raise cleanup_error
        self._state = UnitOfWorkState.DISPOSED

    def _require_new(self, operation: str) -> None:
        if self._state == UnitOfWorkState.DISPOSED:
            raise UnitOfWorkDisposedError(operation, self._state)
        if self._state != UnitOfWorkState.NEW:
            raise UnitOfWorkLifecycleError(operation, self._state)

    def _require_active(self, operation: str) -> None:
        if self._state == UnitOfWorkState.DISPOSED:
            raise UnitOfWorkDisposedError(operation, self._state)
        if self._state != UnitOfWorkState.ACTIVE:
            raise UnitOfWorkLifecycleError(operation, self._state)

    def _rollback_for_cleanup(self, primary_error: BaseException) -> None:
        if self._session is None or self._rollback_attempted:
            return
        self._rollback_attempted = True
        try:
            self._session.rollback()
        except BaseException as cleanup_error:
            primary_error.add_note(f"unit of work rollback cleanup failed: {cleanup_error.__class__.__name__}")

    def _rollback_for_disposal(self) -> None:
        if self._session is None or self._rollback_attempted:
            return
        self._rollback_attempted = True
        self._session.rollback()
        self._state = UnitOfWorkState.ROLLED_BACK

    def _close_preserving(self, primary_error: BaseException) -> None:
        try:
            self._close_session()
        except BaseException as cleanup_error:
            primary_error.add_note(f"unit of work close cleanup failed: {cleanup_error.__class__.__name__}")

    def _close_session(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

    def _claim_session(self, session: Session) -> None:
        owner = getattr(session, _SESSION_OWNER_ATTRIBUTE, None)
        if owner is not None and owner is not self:
            raise RepositoryOwnershipError("a Session cannot belong to more than one unit of work")
        setattr(session, _SESSION_OWNER_ATTRIBUTE, self)
