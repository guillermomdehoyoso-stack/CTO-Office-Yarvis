from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pytest

from yarvis_api.contract_registry import (
    ContractCriticality,
    ContractDefinition,
    ContractLifecycle,
    ContractOperationalStatus,
    ContractType,
    build_contract_registry,
)
from yarvis_api.dispatch import (
    CommandEnvelope,
    CommandNotDispatchableError,
    Dispatcher,
    HandlerDefinition,
    IncompleteTransactionError,
    InvalidCommandCompletionError,
    build_handler_registry,
)
from yarvis_api.module_registry import ApplicationModule, build_module_registry
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork, UnitOfWorkState


@dataclass
class FakeSession:
    begin_calls: int = 0
    commit_calls: int = 0
    rollback_calls: int = 0
    close_calls: int = 0

    def begin(self) -> None:
        self.begin_calls += 1

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


@dataclass
class FakeRuntime:
    sessions: list[FakeSession]

    def create_session(self) -> FakeSession:
        session = FakeSession()
        self.sessions.append(session)
        return session


@dataclass
class CloseFailingSession(FakeSession):
    def close(self) -> None:
        self.close_calls += 1
        raise RuntimeError("close failure")


@dataclass
class CloseFailingRuntime(FakeRuntime):
    def create_session(self) -> FakeSession:
        session = CloseFailingSession()
        self.sessions.append(session)
        return session


@dataclass
class CleanupFailingSession(FakeSession):
    def rollback(self) -> None:
        self.rollback_calls += 1
        raise RuntimeError("rollback cleanup failure")

    def close(self) -> None:
        self.close_calls += 1
        raise RuntimeError("close cleanup failure")


@dataclass
class CleanupFailingRuntime(FakeRuntime):
    def create_session(self) -> FakeSession:
        session = CleanupFailingSession()
        self.sessions.append(session)
        return session


def contract(status: ContractOperationalStatus = ContractOperationalStatus.IMPLEMENTED) -> ContractDefinition:
    return ContractDefinition(
        interaction_contract_id="IC-TEST-CMD-001",
        version="1.0.0",
        contract_type=ContractType.COMMAND,
        owner_module_id="test.owner",
        owning_context="Test",
        owning_capability="test",
        name="TestCommand",
        semantic_purpose="Test Command",
        lifecycle=ContractLifecycle.PROPOSED,
        operational_status=status,
        criticality=ContractCriticality.CORE,
        primary_consumer_or_use_case="test",
    )


def dispatcher(handler, status: ContractOperationalStatus = ContractOperationalStatus.IMPLEMENTED):
    modules = build_module_registry((ApplicationModule("test.owner", "Test owner"),))
    contracts = build_contract_registry(modules, (contract(status),))
    handlers = build_handler_registry(
        modules,
        contracts,
        (
            HandlerDefinition(
                "IC-TEST-CMD-001",
                "test.owner",
                "Test",
                handler,
                "test_handler",
            ),
        ),
    )
    runtime = FakeRuntime([])
    return Dispatcher(contracts, handlers, cast(PersistenceRuntime, runtime)), runtime


def test_envelope_accepts_immutable_payload_and_snapshots_builtins() -> None:
    envelope = CommandEnvelope("IC-TEST-CMD-001", ("safe", 1))
    snapshot = CommandEnvelope.snapshot("IC-TEST-CMD-001", {"items": [1, 2]})

    assert envelope.payload == ("safe", 1)
    assert snapshot.payload["items"] == (1, 2)  # type: ignore[index]
    with pytest.raises(TypeError):
        CommandEnvelope("IC-TEST-CMD-001", ["unsafe"])


def test_dispatch_requires_commit_releases_result_and_restricts_facade() -> None:
    observed: dict[str, object] = {}

    def handler(command: CommandEnvelope, unit_of_work: object) -> str:
        observed["command"] = command
        observed["facade"] = unit_of_work
        assert hasattr(unit_of_work, "commit")
        assert hasattr(unit_of_work, "rollback")
        assert not hasattr(unit_of_work, "dispose")
        assert not hasattr(unit_of_work, "session")
        unit_of_work.commit()  # type: ignore[attr-defined]
        return "completed"

    subject, runtime = dispatcher(handler)

    assert subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe")) == "completed"
    assert observed["command"].contract_id == "IC-TEST-CMD-001"  # type: ignore[union-attr]
    assert runtime.sessions[0].begin_calls == 1
    assert runtime.sessions[0].commit_calls == 1
    assert runtime.sessions[0].rollback_calls == 0
    assert runtime.sessions[0].close_calls == 1


def test_active_and_rolled_back_normal_returns_are_rejected_without_duplicate_rollback() -> None:
    def active_handler(_command: CommandEnvelope, _unit_of_work: object) -> str:
        return "not complete"

    active_dispatcher, active_runtime = dispatcher(active_handler)
    with pytest.raises(IncompleteTransactionError):
        active_dispatcher.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe"))
    assert active_runtime.sessions[0].rollback_calls == 1

    def rollback_handler(_command: CommandEnvelope, unit_of_work: object) -> str:
        unit_of_work.rollback()  # type: ignore[attr-defined]
        return "must not escape"

    rollback_dispatcher, rollback_runtime = dispatcher(rollback_handler)
    with pytest.raises(InvalidCommandCompletionError):
        rollback_dispatcher.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe"))
    assert rollback_runtime.sessions[0].rollback_calls == 1


def test_handler_exception_preserves_primary_failure_and_dispatchability_is_checked() -> None:
    expected = RuntimeError("handler failure")

    def failing_handler(_command: CommandEnvelope, _unit_of_work: object) -> None:
        raise expected

    subject, runtime = dispatcher(failing_handler)
    with pytest.raises(RuntimeError, match="handler failure"):
        subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe"))
    assert runtime.sessions[0].rollback_calls == 1

    inactive, inactive_runtime = dispatcher(failing_handler, ContractOperationalStatus.PLANNED)
    with pytest.raises(CommandNotDispatchableError):
        inactive.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe"))
    assert inactive_runtime.sessions == []


def test_facade_is_invalid_after_dispatch_lifecycle() -> None:
    retained: list[object] = []

    def handler(_command: CommandEnvelope, unit_of_work: object) -> None:
        retained.append(unit_of_work)
        unit_of_work.commit()  # type: ignore[attr-defined]

    subject, _runtime = dispatcher(handler)
    subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe"))

    with pytest.raises(InvalidCommandCompletionError):
        retained[0].commit()  # type: ignore[attr-defined]


def test_disposal_failure_after_commit_withholds_the_handler_result() -> None:
    def handler(_command: CommandEnvelope, unit_of_work: object) -> str:
        unit_of_work.commit()  # type: ignore[attr-defined]
        return "must not be released"

    modules = build_module_registry((ApplicationModule("test.owner", "Test owner"),))
    contracts = build_contract_registry(modules, (contract(),))
    handlers = build_handler_registry(
        modules,
        contracts,
        (
            HandlerDefinition(
                "IC-TEST-CMD-001",
                "test.owner",
                "Test",
                handler,
                "test_handler",
            ),
        ),
    )
    runtime = CloseFailingRuntime([])
    subject = Dispatcher(contracts, handlers, cast(PersistenceRuntime, runtime))

    with pytest.raises(RuntimeError, match="close failure"):
        subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe"))
    assert runtime.sessions[0].commit_calls == 1


def test_factory_receives_the_active_unit_of_work_session_and_its_handler_commits() -> None:
    observed: dict[str, object] = {}

    def handler(command: CommandEnvelope, unit_of_work: object) -> str:
        observed["command"] = command
        assert not hasattr(unit_of_work, "session")
        unit_of_work.commit()  # type: ignore[attr-defined]
        return "factory-completed"

    def factory(session: object):
        observed["session"] = session
        return handler

    modules = build_module_registry((ApplicationModule("test.owner", "Test owner"),))
    contracts = build_contract_registry(modules, (contract(),))
    handlers = build_handler_registry(
        modules,
        contracts,
        (
            HandlerDefinition(
                "IC-TEST-CMD-001",
                "test.owner",
                "Test",
                None,
                "factory_handler",
                factory,
            ),
        ),
    )
    runtime = FakeRuntime([])
    subject = Dispatcher(contracts, handlers, cast(PersistenceRuntime, runtime))

    assert subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe")) == "factory-completed"
    assert observed["command"].contract_id == "IC-TEST-CMD-001"  # type: ignore[union-attr]
    assert observed["session"] is runtime.sessions[0]
    assert runtime.sessions[0].begin_calls == 1
    assert runtime.sessions[0].commit_calls == 1
    assert runtime.sessions[0].close_calls == 1


def test_factory_failure_prevents_handler_invocation_and_uses_existing_cleanup() -> None:
    observed = {"handler_invoked": False}

    def handler(_command: CommandEnvelope, _unit_of_work: object) -> None:
        observed["handler_invoked"] = True

    def factory(_session: object):
        raise RuntimeError("factory failure")

    modules = build_module_registry((ApplicationModule("test.owner", "Test owner"),))
    contracts = build_contract_registry(modules, (contract(),))
    handlers = build_handler_registry(
        modules,
        contracts,
        (HandlerDefinition("IC-TEST-CMD-001", "test.owner", "Test", None, "factory_handler", factory),),
    )
    runtime = FakeRuntime([])
    observed_unit_of_work: list[UnitOfWork] = []

    def unit_of_work_factory(persistence: PersistenceRuntime, scope: OperationScope) -> UnitOfWork:
        unit_of_work = UnitOfWork(persistence, scope)
        observed_unit_of_work.append(unit_of_work)
        return unit_of_work

    subject = Dispatcher(
        contracts,
        handlers,
        cast(PersistenceRuntime, runtime),
        unit_of_work_factory=unit_of_work_factory,
    )

    with pytest.raises(RuntimeError, match="factory failure"):
        subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe"))

    assert observed["handler_invoked"] is False
    assert runtime.sessions[0].rollback_calls == 1
    assert runtime.sessions[0].close_calls == 1
    assert observed_unit_of_work[0].state == UnitOfWorkState.DISPOSED


def test_factory_failure_preserves_primary_error_when_cleanup_double_fails() -> None:
    def factory(_session: object):
        raise RuntimeError("factory failure")

    modules = build_module_registry((ApplicationModule("test.owner", "Test owner"),))
    contracts = build_contract_registry(modules, (contract(),))
    handlers = build_handler_registry(
        modules,
        contracts,
        (HandlerDefinition("IC-TEST-CMD-001", "test.owner", "Test", None, "factory_handler", factory),),
    )
    runtime = CleanupFailingRuntime([])
    observed_unit_of_work: list[UnitOfWork] = []

    def unit_of_work_factory(persistence: PersistenceRuntime, scope: OperationScope) -> UnitOfWork:
        unit_of_work = UnitOfWork(persistence, scope)
        observed_unit_of_work.append(unit_of_work)
        return unit_of_work

    subject = Dispatcher(
        contracts,
        handlers,
        cast(PersistenceRuntime, runtime),
        unit_of_work_factory=unit_of_work_factory,
    )

    with pytest.raises(RuntimeError, match="factory failure") as error:
        subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe"))

    assert any("cleanup failed" in note for note in error.value.__notes__)
    assert runtime.sessions[0].rollback_calls == 1
    assert runtime.sessions[0].close_calls == 1
    assert observed_unit_of_work[0].state == UnitOfWorkState.FAILED


def test_separate_dispatches_create_separate_sessions() -> None:
    def handler(_command: CommandEnvelope, unit_of_work: object) -> None:
        unit_of_work.commit()  # type: ignore[attr-defined]

    subject, runtime = dispatcher(handler)
    subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "one"))
    subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "two"))

    assert len(runtime.sessions) == 2
    assert runtime.sessions[0] is not runtime.sessions[1]
    assert UnitOfWorkState.COMMITTED.value == "COMMITTED"


def test_dispatch_uses_the_postgresql_backed_application_runtime() -> None:
    from yarvis_api.main import app

    def handler(_command: CommandEnvelope, unit_of_work: object) -> str:
        unit_of_work.commit()  # type: ignore[attr-defined]
        return "committed"

    modules = build_module_registry((ApplicationModule("test.owner", "Test owner"),))
    contracts = build_contract_registry(modules, (contract(),))
    handlers = build_handler_registry(
        modules,
        contracts,
        (HandlerDefinition("IC-TEST-CMD-001", "test.owner", "Test", handler, "postgres_handler"),),
    )
    subject = Dispatcher(contracts, handlers, app.state.yarvis.persistence)

    assert subject.dispatch(CommandEnvelope("IC-TEST-CMD-001", "safe")) == "committed"
