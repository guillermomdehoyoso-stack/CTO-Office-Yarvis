from __future__ import annotations

import asyncio
import inspect
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
    DuplicateHandlerError,
    HandlerDefinition,
    HandlerOwnershipError,
    HandlerRegistry,
    HandlerRegistrySealedError,
    InvalidHandlerDefinitionError,
    MissingHandlerError,
    UnknownDispatchContractError,
    UnsupportedContractKindError,
    build_handler_registry,
)
from yarvis_api.module_registry import ApplicationModule, build_module_registry


def command_contract(**overrides: object) -> ContractDefinition:
    values: dict[str, object] = {
        "interaction_contract_id": "IC-TEST-CMD-001",
        "version": "1.0.0",
        "contract_type": ContractType.COMMAND,
        "owner_module_id": "test.owner",
        "owning_context": "Test",
        "owning_capability": "test",
        "name": "TestCommand",
        "semantic_purpose": "Test Command",
        "lifecycle": ContractLifecycle.PROPOSED,
        "operational_status": ContractOperationalStatus.PLANNED,
        "criticality": ContractCriticality.CORE,
        "primary_consumer_or_use_case": "test",
    }
    values.update(overrides)
    return ContractDefinition(**values)  # type: ignore[arg-type]


def registries(contract: ContractDefinition | None = None):
    modules = build_module_registry((ApplicationModule("test.owner", "Test owner"),))
    contracts = build_contract_registry(modules, (() if contract is None else (contract,)))
    return modules, contracts


def handler(_command: object, _unit_of_work: object) -> None:
    return None


def definition(**overrides: object) -> HandlerDefinition:
    values: dict[str, object] = {
        "interaction_contract_id": "IC-TEST-CMD-001",
        "owner_module_id": "test.owner",
        "owning_context": "Test",
        "handler": handler,
        "handler_name": "test_handler",
    }
    values.update(overrides)
    return HandlerDefinition(**values)  # type: ignore[arg-type]


def test_registry_registers_inactive_structurally_valid_command_and_seals() -> None:
    modules, contracts = registries(command_contract())
    registry = build_handler_registry(modules, contracts, (definition(),))

    assert registry.is_sealed is True
    assert registry.get("IC-TEST-CMD-001") == definition()
    assert registry.list() == (definition(),)


def test_registry_rejects_unknown_non_command_owner_mismatch_duplicate_and_post_seal_mutation() -> None:
    modules, contracts = registries(command_contract())
    registry = HandlerRegistry(modules, contracts)

    with pytest.raises(UnknownDispatchContractError):
        registry.register(definition(interaction_contract_id="IC-TEST-CMD-999"))
    query = command_contract(
        interaction_contract_id="IC-TEST-QRY-001",
        contract_type=ContractType.QUERY,
    )
    query_contracts = build_contract_registry(modules, (query,))
    with pytest.raises(UnsupportedContractKindError):
        build_handler_registry(
            modules,
            query_contracts,
            (definition(interaction_contract_id=query.interaction_contract_id),),
        )
    with pytest.raises(HandlerOwnershipError):
        registry.register(definition(owner_module_id="other.owner"))

    registry.register(definition())
    with pytest.raises(DuplicateHandlerError):
        registry.register(definition())
    registry.seal()
    with pytest.raises(HandlerRegistrySealedError):
        registry.register(definition(interaction_contract_id="IC-TEST-CMD-002"))
    with pytest.raises(MissingHandlerError):
        registry.get("IC-TEST-CMD-999")


def test_handler_definition_rejects_coroutine_functions() -> None:
    async def async_handler(_command: object, _unit_of_work: object) -> None:
        await asyncio.sleep(0)

    modules, contracts = registries(command_contract())
    with pytest.raises(Exception, match="synchronous callable"):
        build_handler_registry(modules, contracts, (definition(handler=async_handler),))


def test_handler_definition_preserves_static_positional_compatibility() -> None:
    positional = HandlerDefinition("IC-TEST-CMD-001", "test.owner", "Test", handler, "test_handler")

    assert positional.handler is handler
    assert positional.handler_name == "test_handler"
    assert positional.handler_factory is None


def test_handler_definition_requires_exactly_one_synchronous_resolution_mode() -> None:
    def factory(_session: object):
        return handler

    async def async_factory(_session: object):
        return handler

    modules, contracts = registries(command_contract())
    with pytest.raises(InvalidHandlerDefinitionError, match="exactly one"):
        build_handler_registry(modules, contracts, (definition(handler=None),))
    with pytest.raises(InvalidHandlerDefinitionError, match="exactly one"):
        build_handler_registry(modules, contracts, (definition(handler_factory=factory),))
    with pytest.raises(InvalidHandlerDefinitionError, match="synchronous callable"):
        build_handler_registry(modules, contracts, (definition(handler=None, handler_factory=async_factory),))
    with pytest.raises(InvalidHandlerDefinitionError, match="synchronous callable"):
        build_handler_registry(modules, contracts, (definition(handler=cast(object, "not callable")),))

    factory_definition = definition(handler=None, handler_factory=factory)
    factory_registry = build_handler_registry(modules, contracts, (factory_definition,))
    assert factory_definition.handler is None
    assert factory_definition.handler_factory is factory
    assert factory_registry.get("IC-TEST-CMD-001") is factory_definition


def test_handler_registry_rejects_async_callable_instances_and_accepts_sync_callable_instances() -> None:
    class AsyncCallable:
        async def __call__(self, *_arguments: object) -> None:
            return None

    class SyncCallable:
        def __call__(self, *_arguments: object) -> None:
            return None

    modules, contracts = registries(command_contract())
    with pytest.raises(InvalidHandlerDefinitionError, match="synchronous callable"):
        build_handler_registry(modules, contracts, (definition(handler=AsyncCallable()),))
    with pytest.raises(InvalidHandlerDefinitionError, match="synchronous callable"):
        build_handler_registry(modules, contracts, (definition(handler=None, handler_factory=AsyncCallable()),))

    synchronous_definition = definition(handler=SyncCallable())
    synchronous_registry = build_handler_registry(modules, contracts, (synchronous_definition,))
    assert synchronous_registry.get("IC-TEST-CMD-001") is synchronous_definition


def test_dispatch_models_has_no_runtime_sqlalchemy_import() -> None:
    import yarvis_api.dispatch.models as models

    source = inspect.getsource(models)
    sqlalchemy_import = "    from sqlalchemy.orm import Session"
    import_index = source.splitlines().index(sqlalchemy_import)

    assert source.splitlines()[import_index - 1] == "if TYPE_CHECKING:"
