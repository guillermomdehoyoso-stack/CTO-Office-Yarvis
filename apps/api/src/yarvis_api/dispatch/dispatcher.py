"""Canonical synchronous owner-Command execution orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from yarvis_api.contract_registry import (
    ContractLifecycle,
    ContractOperationalStatus,
    ContractRegistry,
    ContractType,
)
from yarvis_api.dispatch.errors import (
    CommandNotDispatchableError,
    HandlerOwnershipError,
    IncompleteTransactionError,
    InvalidCommandCompletionError,
    UnknownDispatchContractError,
    UnsupportedContractKindError,
)
from yarvis_api.dispatch.models import CommandEnvelope
from yarvis_api.dispatch.registry import HandlerRegistry
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork, UnitOfWorkState

UnitOfWorkFactory = Callable[[PersistenceRuntime, OperationScope], UnitOfWork]
_DISPATCHABLE_STATUSES = frozenset(
    {
        ContractOperationalStatus.IMPLEMENTED,
        ContractOperationalStatus.VERIFIED,
        ContractOperationalStatus.PRODUCTION,
    }
)


@dataclass(slots=True)
class _CommandUnitOfWorkFacade:
    """Restricted transaction-intent facade valid only during one dispatch."""

    _unit_of_work: UnitOfWork
    _is_active: bool = field(default=True, init=False)

    def commit(self) -> None:
        self._require_active()
        self._unit_of_work.commit()

    def rollback(self) -> None:
        self._require_active()
        self._unit_of_work.rollback()

    def invalidate(self) -> None:
        self._is_active = False

    def _require_active(self) -> None:
        if not self._is_active:
            raise InvalidCommandCompletionError("command Unit of Work facade is no longer active")


@dataclass(frozen=True, slots=True)
class Dispatcher:
    """Immutable per-application dispatcher with no retained execution state."""

    contract_registry: ContractRegistry
    handler_registry: HandlerRegistry
    persistence: PersistenceRuntime
    unit_of_work_factory: UnitOfWorkFactory = UnitOfWork

    def __post_init__(self) -> None:
        if not self.contract_registry.is_sealed or not self.handler_registry.is_sealed:
            raise ValueError("dispatch registries must be sealed")

    def dispatch(self, command: CommandEnvelope) -> object | None:
        """Synchronously execute one owner Command through one local Unit of Work."""

        if not isinstance(command, CommandEnvelope):
            raise TypeError("dispatch requires a CommandEnvelope")
        contract = self.contract_registry.get(command.contract_id)
        if contract is None:
            raise UnknownDispatchContractError(f"unknown interaction contract: {command.contract_id}")
        if contract.contract_type != ContractType.COMMAND:
            raise UnsupportedContractKindError(f"interaction contract is not a Command: {command.contract_id}")
        if not self._is_dispatchable(contract.lifecycle, contract.operational_status):
            raise CommandNotDispatchableError(f"Command is not dispatchable: {command.contract_id}")
        handler_definition = self.handler_registry.get(command.contract_id)
        if (
            handler_definition.owner_module_id != contract.owner_module_id
            or handler_definition.owning_context != contract.owning_context
        ):
            raise HandlerOwnershipError(f"handler ownership does not match contract: {command.contract_id}")

        scope = OperationScope()
        unit_of_work = self.unit_of_work_factory(self.persistence, scope)
        facade: _CommandUnitOfWorkFacade | None = None
        try:
            with unit_of_work:
                facade = _CommandUnitOfWorkFacade(unit_of_work)
                handler = handler_definition.handler
                if handler is None:
                    handler_factory = handler_definition.handler_factory
                    assert handler_factory is not None
                    handler = handler_factory(unit_of_work.session)
                result = handler(command, facade)
                self._verify_terminal_state(unit_of_work.state)
                return result
        finally:
            if facade is not None:
                facade.invalidate()

    @staticmethod
    def _is_dispatchable(
        lifecycle: ContractLifecycle | str,
        operational_status: ContractOperationalStatus | str,
    ) -> bool:
        return (
            ContractLifecycle(lifecycle) != ContractLifecycle.RETIRED
            and ContractOperationalStatus(operational_status) in _DISPATCHABLE_STATUSES
        )

    @staticmethod
    def _verify_terminal_state(state: UnitOfWorkState) -> None:
        if state == UnitOfWorkState.COMMITTED:
            return
        if state == UnitOfWorkState.ACTIVE:
            raise IncompleteTransactionError("handler returned with an active Unit of Work")
        raise InvalidCommandCompletionError(f"handler returned with Unit of Work state {state.value}")
