from __future__ import annotations

from collections import deque
from typing import cast

import pytest
from sqlalchemy import text

from yarvis_api.config import Settings
from yarvis_api.persistence import (
    NestedUnitOfWorkError,
    OperationScope,
    RepositoryOwnershipError,
    UnitOfWork,
    UnitOfWorkDisposedError,
    UnitOfWorkLifecycleError,
    UnitOfWorkState,
    build_persistence_runtime,
)
from yarvis_api.persistence.runtime import PersistenceRuntime


class FakeSession:
    def __init__(
        self,
        *,
        begin_error: BaseException | None = None,
        commit_error: BaseException | None = None,
        rollback_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.begin_error = begin_error
        self.commit_error = commit_error
        self.rollback_error = rollback_error
        self.close_error = close_error
        self.begin_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    def begin(self) -> None:
        self.begin_calls += 1
        if self.begin_error is not None:
            raise self.begin_error

    def commit(self) -> None:
        self.commit_calls += 1
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self) -> None:
        self.rollback_calls += 1
        if self.rollback_error is not None:
            raise self.rollback_error

    def close(self) -> None:
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error


class FakeRuntime:
    def __init__(self, *sessions: FakeSession | BaseException) -> None:
        self.sessions = deque(sessions)
        self.create_session_calls = 0

    def create_session(self) -> FakeSession:
        self.create_session_calls += 1
        item = self.sessions.popleft()
        if isinstance(item, BaseException):
            raise item
        return item


def build_uow(runtime: FakeRuntime, scope: OperationScope | None = None) -> UnitOfWork:
    return UnitOfWork(cast(PersistenceRuntime, runtime), scope or OperationScope())


def test_construction_owns_no_session_and_disposal_from_new_is_idempotent() -> None:
    runtime = FakeRuntime(FakeSession())
    unit_of_work = build_uow(runtime)

    assert unit_of_work.state == UnitOfWorkState.NEW
    with pytest.raises(RepositoryOwnershipError):
        _ = unit_of_work.session
    unit_of_work.dispose()
    unit_of_work.dispose()

    assert runtime.create_session_calls == 0
    assert unit_of_work.state == UnitOfWorkState.DISPOSED


def test_enter_acquires_one_session_and_explicitly_begins_one_transaction() -> None:
    session = FakeSession()
    runtime = FakeRuntime(session)
    unit_of_work = build_uow(runtime)

    with unit_of_work as active:
        assert active is unit_of_work
        assert active.session is session
        assert active.state == UnitOfWorkState.ACTIVE
        assert session.begin_calls == 1
        assert session.commit_calls == 0

    assert session.rollback_calls == 1
    assert session.close_calls == 1
    assert unit_of_work.state == UnitOfWorkState.DISPOSED


def test_reentry_and_repository_access_after_disposal_are_rejected() -> None:
    unit_of_work = build_uow(FakeRuntime(FakeSession()))

    unit_of_work.__enter__()
    with pytest.raises(UnitOfWorkLifecycleError):
        unit_of_work.__enter__()
    unit_of_work.dispose()
    with pytest.raises(UnitOfWorkDisposedError):
        _ = unit_of_work.session


def test_activation_failures_enter_failed_and_release_operation_scope() -> None:
    acquisition_error = RuntimeError("acquisition failed")
    scope = OperationScope()
    failed_acquisition = build_uow(FakeRuntime(acquisition_error), scope)

    with pytest.raises(RuntimeError, match="acquisition failed"):
        failed_acquisition.__enter__()
    assert failed_acquisition.state == UnitOfWorkState.FAILED

    session = FakeSession(begin_error=RuntimeError("begin failed"))
    failed_begin = build_uow(FakeRuntime(session), scope)
    with pytest.raises(RuntimeError, match="begin failed"):
        failed_begin.__enter__()

    assert failed_begin.state == UnitOfWorkState.FAILED
    assert session.close_calls == 1


def test_commit_succeeds_once_then_disposal_only_closes_session() -> None:
    session = FakeSession()
    unit_of_work = build_uow(FakeRuntime(session))

    unit_of_work.__enter__()
    unit_of_work.commit()

    assert unit_of_work.state == UnitOfWorkState.COMMITTED
    assert session.commit_calls == 1
    with pytest.raises(UnitOfWorkLifecycleError):
        unit_of_work.commit()
    with pytest.raises(UnitOfWorkLifecycleError):
        unit_of_work.rollback()
    unit_of_work.dispose()
    assert session.rollback_calls == 0
    assert session.close_calls == 1


def test_commit_failure_preserves_primary_error_and_attempts_one_cleanup_rollback() -> None:
    session = FakeSession(commit_error=RuntimeError("commit failed"), rollback_error=RuntimeError("cleanup failed"))
    unit_of_work = build_uow(FakeRuntime(session))
    unit_of_work.__enter__()

    with pytest.raises(RuntimeError, match="commit failed") as error:
        unit_of_work.commit()

    assert unit_of_work.state == UnitOfWorkState.FAILED
    assert session.rollback_calls == 1
    assert any("rollback cleanup failed" in note for note in error.value.__notes__)
    with pytest.raises(UnitOfWorkLifecycleError):
        unit_of_work.rollback()
    unit_of_work.dispose()
    assert session.rollback_calls == 1
    assert session.close_calls == 1


def test_rollback_succeeds_once_and_failure_is_not_retried() -> None:
    successful = FakeSession()
    completed = build_uow(FakeRuntime(successful))
    completed.__enter__()
    completed.rollback()
    assert completed.state == UnitOfWorkState.ROLLED_BACK
    with pytest.raises(UnitOfWorkLifecycleError):
        completed.rollback()
    completed.dispose()

    failed_session = FakeSession(rollback_error=RuntimeError("rollback failed"))
    failed = build_uow(FakeRuntime(failed_session))
    failed.__enter__()
    with pytest.raises(RuntimeError, match="rollback failed"):
        failed.rollback()
    assert failed.state == UnitOfWorkState.FAILED
    failed.dispose()
    assert failed_session.rollback_calls == 1
    assert failed_session.close_calls == 1


def test_disposal_close_failure_remains_failed_until_safe_retry_succeeds() -> None:
    session = FakeSession(close_error=RuntimeError("close failed"))
    unit_of_work = build_uow(FakeRuntime(session))
    unit_of_work.__enter__()
    unit_of_work.commit()

    with pytest.raises(RuntimeError, match="close failed"):
        unit_of_work.dispose()
    assert unit_of_work.state == UnitOfWorkState.FAILED
    session.close_error = None
    unit_of_work.dispose()
    assert unit_of_work.state == UnitOfWorkState.DISPOSED
    assert session.close_calls == 2


def test_nested_scope_is_rejected_and_separate_scopes_are_concurrent_safe() -> None:
    shared_scope = OperationScope()
    outer = build_uow(FakeRuntime(FakeSession()), shared_scope)
    nested = build_uow(FakeRuntime(FakeSession()), shared_scope)
    outer.__enter__()
    with pytest.raises(NestedUnitOfWorkError):
        nested.__enter__()
    outer.dispose()

    first_session = FakeSession()
    second_session = FakeSession()
    first = build_uow(FakeRuntime(first_session), OperationScope())
    second = build_uow(FakeRuntime(second_session), OperationScope())
    first.__enter__()
    second.__enter__()
    assert first.session is first_session
    assert second.session is second_session
    first.dispose()
    second.dispose()


def test_one_session_cannot_be_owned_by_two_unit_of_work_instances() -> None:
    shared_session = FakeSession()
    first = build_uow(FakeRuntime(shared_session), OperationScope())
    first.__enter__()
    second = build_uow(FakeRuntime(shared_session), OperationScope())

    with pytest.raises(RepositoryOwnershipError):
        second.__enter__()

    assert second.state == UnitOfWorkState.FAILED
    first.dispose()


def test_context_manager_preserves_body_error_over_cleanup_error() -> None:
    session = FakeSession(rollback_error=RuntimeError("rollback failed"))
    unit_of_work = build_uow(FakeRuntime(session))

    with pytest.raises(ValueError, match="body failed") as error:
        with unit_of_work:
            raise ValueError("body failed")

    assert any("cleanup failed" in note for note in error.value.__notes__)
    assert unit_of_work.state == UnitOfWorkState.FAILED
    unit_of_work.dispose()
    assert unit_of_work.state == UnitOfWorkState.DISPOSED


def test_persistence_runtime_integration_uses_one_postgresql_session(test_database: None) -> None:
    runtime = build_persistence_runtime(Settings(environment="test"))
    owner_token = object()
    runtime.transfer_ownership(owner_token)
    unit_of_work = UnitOfWork(runtime, OperationScope())

    with unit_of_work as active:
        assert active.session.scalar(text("SELECT 1")) == 1
        active.rollback()

    assert unit_of_work.state == UnitOfWorkState.DISPOSED
    runtime.dispose(owner_token)
