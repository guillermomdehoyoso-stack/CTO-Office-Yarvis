from __future__ import annotations

import asyncio

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

    with pytest.raises(Exception, match="synchronous callable"):
        definition(handler=async_handler)
