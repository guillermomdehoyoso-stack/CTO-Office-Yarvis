from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from yarvis_api.contract_registry import (
    ContractCriticality,
    ContractDefinition,
    ContractLifecycle,
    ContractOperationalStatus,
    ContractRegistry,
    ContractRegistrySealedError,
    ContractType,
    DuplicateContractError,
    InvalidContractDefinitionError,
    UnknownContractOwnerError,
    build_contract_registry,
)
from yarvis_api.module_registry import ApplicationModule, build_module_registry


def module_registry():
    return build_module_registry(
        (
            ApplicationModule(module_id="test.owner", display_name="Test Owner"),
            ApplicationModule(module_id="test.other", display_name="Test Other"),
        )
    )


def contract(
    interaction_contract_id: str = "IC-TEST-CMD-001",
    owner_module_id: str = "test.owner",
    contract_type: ContractType | str = ContractType.COMMAND,
    **overrides: object,
) -> ContractDefinition:
    values: dict[str, object] = {
        "interaction_contract_id": interaction_contract_id,
        "version": "1.0.0",
        "contract_type": contract_type,
        "owner_module_id": owner_module_id,
        "owning_context": "Test",
        "owning_capability": "test capability",
        "name": "TestContract",
        "semantic_purpose": "test governed metadata",
        "lifecycle": ContractLifecycle.PROPOSED,
        "operational_status": ContractOperationalStatus.PLANNED,
        "criticality": ContractCriticality.CORE,
        "primary_consumer_or_use_case": "test use case",
    }
    values.update(overrides)
    return ContractDefinition(**values)  # type: ignore[arg-type]


def test_contract_definition_is_immutable_and_normalizes_optional_traceability() -> None:
    definition = contract(traceability_references=["ADT-CONTRACT-001"])

    assert definition.traceability_references == ("ADT-CONTRACT-001",)
    assert definition.architectural_steward is None
    with pytest.raises(FrozenInstanceError):
        definition.name = "Changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("interaction_contract_id", "invalid"),
        ("version", "1.0"),
        ("owning_context", " "),
        ("contract_type", "Invalid"),
        ("lifecycle", "Invalid"),
        ("operational_status", "Proposed"),
        ("criticality", "Invalid"),
        ("architectural_steward", " "),
        ("traceability_references", (" ",)),
    ),
)
def test_contract_definition_rejects_invalid_ratified_metadata(field_name: str, value: object) -> None:
    with pytest.raises(InvalidContractDefinitionError):
        contract(**cast(Any, {field_name: value}))


def test_registry_registers_retrieves_filters_and_preserves_explicit_order() -> None:
    registry = ContractRegistry(module_registry())
    first = contract("IC-TEST-CMD-001")
    second = contract("IC-TEST-QRY-002", owner_module_id="test.other", contract_type=ContractType.QUERY)
    registry.register_many((first, second))
    registry.seal()

    assert registry.get("IC-TEST-CMD-001") is first
    assert registry.get("IC-TEST-EVT-999") is None
    assert registry.contains("IC-TEST-QRY-002") is True
    assert tuple(item.interaction_contract_id for item in registry.list()) == ("IC-TEST-CMD-001", "IC-TEST-QRY-002")
    assert registry.list_by_kind(ContractType.QUERY) == (second,)
    assert registry.list_by_owner("test.owner") == (first,)


def test_registry_rejects_duplicate_unknown_owner_and_mutation_after_sealing() -> None:
    modules = module_registry()
    registry = ContractRegistry(modules)
    registry.register(contract())
    with pytest.raises(DuplicateContractError):
        registry.register(contract())
    with pytest.raises(UnknownContractOwnerError):
        registry.register(contract("IC-TEST-EVT-002", owner_module_id="test.absent", contract_type=ContractType.EVENT))

    registry.seal()
    with pytest.raises(ContractRegistrySealedError):
        registry.register(contract("IC-TEST-NTF-003", contract_type=ContractType.NOTIFICATION))


def test_empty_and_multiple_contract_registries_are_sealed_and_isolated() -> None:
    modules = module_registry()
    empty = build_contract_registry(modules)
    populated = build_contract_registry(modules, (contract(),))

    assert empty.is_sealed is True
    assert empty.list() == ()
    assert populated.is_sealed is True
    assert populated.list() == (contract(),)
    assert empty is not populated
