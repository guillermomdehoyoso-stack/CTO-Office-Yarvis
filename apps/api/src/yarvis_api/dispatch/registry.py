"""Explicit per-application registry for owner Command handlers."""

from __future__ import annotations

from collections.abc import Iterable

from yarvis_api.contract_registry import ContractRegistry, ContractType
from yarvis_api.dispatch.errors import (
    DuplicateHandlerError,
    HandlerOwnershipError,
    HandlerRegistryError,
    HandlerRegistrySealedError,
    MissingHandlerError,
    UnknownDispatchContractError,
    UnsupportedContractKindError,
)
from yarvis_api.dispatch.models import HandlerDefinition
from yarvis_api.module_registry import ModuleRegistry


class HandlerRegistry:
    """Explicit, sealed mapping from canonical Command IDs to one handler."""

    def __init__(self, module_registry: ModuleRegistry, contract_registry: ContractRegistry) -> None:
        if not module_registry.is_sealed or not contract_registry.is_sealed:
            raise HandlerRegistryError("module and contract registries must be sealed before handler registration")
        self._module_registry = module_registry
        self._contract_registry = contract_registry
        self._handlers: dict[str, HandlerDefinition] = {}
        self._ordered_handlers: tuple[HandlerDefinition, ...] | None = None

    @property
    def is_sealed(self) -> bool:
        return self._ordered_handlers is not None

    def register(self, definition: HandlerDefinition) -> None:
        if self.is_sealed:
            raise HandlerRegistrySealedError("handler registry is sealed")
        contract = self._contract_registry.get(definition.interaction_contract_id)
        if contract is None:
            raise UnknownDispatchContractError(f"unknown interaction contract: {definition.interaction_contract_id}")
        if contract.contract_type != ContractType.COMMAND:
            raise UnsupportedContractKindError(
                f"interaction contract is not a Command: {definition.interaction_contract_id}"
            )
        if not self._module_registry.contains(contract.owner_module_id):
            raise HandlerOwnershipError(f"canonical owner module is unavailable: {contract.owner_module_id}")
        if (
            definition.owner_module_id != contract.owner_module_id
            or definition.owning_context != contract.owning_context
        ):
            raise HandlerOwnershipError(
                f"handler ownership does not match contract: {definition.interaction_contract_id}"
            )
        if definition.interaction_contract_id in self._handlers:
            raise DuplicateHandlerError(f"duplicate Command handler: {definition.interaction_contract_id}")
        self._handlers[definition.interaction_contract_id] = definition

    def register_many(self, definitions: Iterable[HandlerDefinition]) -> None:
        for definition in definitions:
            self.register(definition)

    def get(self, interaction_contract_id: str) -> HandlerDefinition:
        definition = self._handlers.get(interaction_contract_id)
        if definition is None:
            raise MissingHandlerError(f"missing Command handler: {interaction_contract_id}")
        return definition

    def contains(self, interaction_contract_id: str) -> bool:
        return interaction_contract_id in self._handlers

    def list(self) -> tuple[HandlerDefinition, ...]:
        return self._ordered_handlers if self._ordered_handlers is not None else tuple(self._handlers.values())

    def seal(self) -> None:
        if not self.is_sealed:
            self._ordered_handlers = tuple(self._handlers.values())


def build_handler_registry(
    module_registry: ModuleRegistry,
    contract_registry: ContractRegistry,
    handlers: Iterable[HandlerDefinition] = (),
) -> HandlerRegistry:
    """Build and seal an explicit Handler Registry for one application."""

    registry = HandlerRegistry(module_registry, contract_registry)
    registry.register_many(handlers)
    registry.seal()
    return registry
