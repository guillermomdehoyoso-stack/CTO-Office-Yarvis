"""ADR-016 integration evidence for the zero-persistence Dispatch probe."""

from collections.abc import Callable

import pytest

from yarvis_api.dispatch import (
    CommandEnvelope,
    CommandUnitOfWork,
    Dispatcher,
    HandlerDefinition,
    IncompleteTransactionError,
    build_handler_registry,
)
from yarvis_api.main import app
from yarvis_api.persistence import OperationScope, UnitOfWork, UnitOfWorkState


PROBE_CONTRACT_ID = "IC-PLATFORM-CMD-DISPATCH-PROBE"
ProbeHandler = Callable[[CommandEnvelope, CommandUnitOfWork], object | None]


def _dispatcher_with_test_handler(handler: ProbeHandler) -> tuple[Dispatcher, list[UnitOfWork]]:
    state = app.state.yarvis
    handler_registry = build_handler_registry(
        state.module_registry,
        state.contract_registry,
        (
            HandlerDefinition(
                interaction_contract_id=PROBE_CONTRACT_ID,
                owner_module_id="platform",
                owning_context="Platform",
                handler=handler,
                handler_name="dispatch_mechanics_probe_test_variant",
            ),
        ),
    )
    observed_unit_of_work: list[UnitOfWork] = []

    def unit_of_work_factory(persistence, scope: OperationScope) -> UnitOfWork:
        unit_of_work = UnitOfWork(persistence, scope)
        observed_unit_of_work.append(unit_of_work)
        return unit_of_work

    return (
        Dispatcher(
            state.contract_registry,
            handler_registry,
            state.persistence,
            unit_of_work_factory=unit_of_work_factory,
        ),
        observed_unit_of_work,
    )


def test_default_application_registers_only_the_adr016_probe_and_commits_explicitly() -> None:
    state = app.state.yarvis

    assert tuple(handler.interaction_contract_id for handler in state.handler_registry.list()) == (PROBE_CONTRACT_ID,)
    assert state.dispatcher.dispatch(CommandEnvelope(PROBE_CONTRACT_ID, None)) is None


def test_probe_explicit_rollback_preserves_failure_and_disposes_deterministically() -> None:
    expected = RuntimeError("explicit rollback")

    def handler(_command: CommandEnvelope, unit_of_work: CommandUnitOfWork) -> None:
        unit_of_work.rollback()
        raise expected

    dispatcher, observed = _dispatcher_with_test_handler(handler)

    with pytest.raises(RuntimeError, match="explicit rollback"):
        dispatcher.dispatch(CommandEnvelope(PROBE_CONTRACT_ID, None))

    assert observed[0].state == UnitOfWorkState.DISPOSED


def test_probe_active_return_is_rejected_and_disposed_deterministically() -> None:
    def handler(_command: CommandEnvelope, _unit_of_work: CommandUnitOfWork) -> None:
        return None

    dispatcher, observed = _dispatcher_with_test_handler(handler)

    with pytest.raises(IncompleteTransactionError):
        dispatcher.dispatch(CommandEnvelope(PROBE_CONTRACT_ID, None))

    assert observed[0].state == UnitOfWorkState.DISPOSED


def test_probe_pre_commit_failure_preserves_failure_and_disposes_deterministically() -> None:
    expected = RuntimeError("pre-commit failure")

    def handler(_command: CommandEnvelope, _unit_of_work: CommandUnitOfWork) -> None:
        raise expected

    dispatcher, observed = _dispatcher_with_test_handler(handler)

    with pytest.raises(RuntimeError, match="pre-commit failure"):
        dispatcher.dispatch(CommandEnvelope(PROBE_CONTRACT_ID, None))

    assert observed[0].state == UnitOfWorkState.DISPOSED


def test_probe_post_commit_failure_preserves_failure_and_disposes_deterministically() -> None:
    expected = RuntimeError("post-commit failure")

    def handler(_command: CommandEnvelope, unit_of_work: CommandUnitOfWork) -> None:
        unit_of_work.commit()
        raise expected

    dispatcher, observed = _dispatcher_with_test_handler(handler)

    with pytest.raises(RuntimeError, match="post-commit failure"):
        dispatcher.dispatch(CommandEnvelope(PROBE_CONTRACT_ID, None))

    assert observed[0].state == UnitOfWorkState.DISPOSED
