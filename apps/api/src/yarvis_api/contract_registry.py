"""Explicit, validated technical registry for Yarvis interaction contracts."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from yarvis_api.module_registry import ModuleRegistry

INTERACTION_CONTRACT_ID_PATTERN = re.compile(r"^IC-[A-Z0-9]+(?:-[A-Z0-9]+)*-(?:CMD|QRY|EVT|NTF)-\d{3}$")
SEMANTIC_VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ContractRegistryError(ValueError):
    """Base error for deterministic, safe Contract Registry failures."""


class InvalidContractDefinitionError(ContractRegistryError):
    """A contract definition violates the ratified F-006 metadata model."""


class DuplicateContractError(ContractRegistryError):
    """A registry already contains the supplied stable contract identifier."""


class UnknownContractOwnerError(ContractRegistryError):
    """A contract owner is absent from the supplied Module Registry."""


class ContractRegistrySealedError(ContractRegistryError):
    """A sealed Contract Registry cannot accept further registrations."""


class ContractType(StrEnum):
    """The four ratified Interaction Contract classifications."""

    COMMAND = "Command"
    QUERY = "Query"
    EVENT = "Event"
    NOTIFICATION = "Notification"


class ContractLifecycle(StrEnum):
    """Architectural governance state, independent from operational status."""

    DRAFT = "Draft"
    PROPOSED = "Proposed"
    RATIFIED = "Ratified"
    DEPRECATED = "Deprecated"
    RETIRED = "Retired"


class ContractOperationalStatus(StrEnum):
    """Operational availability state, independent from lifecycle."""

    PLANNED = "Planned"
    IMPLEMENTED = "Implemented"
    VERIFIED = "Verified"
    PRODUCTION = "Production"
    SUSPENDED = "Suspended"
    REMOVED = "Removed"


class ContractCriticality(StrEnum):
    """Ratified architectural and operational impact classification."""

    CRITICAL = "Critical"
    CORE = "Core"
    OPERATIONAL = "Operational"
    INFORMATIONAL = "Informational"


def _require_nonblank_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise InvalidContractDefinitionError(f"{field_name} must be nonblank")


def _normalize_enum[T: StrEnum](field_name: str, value: T | str, enum_type: type[T]) -> T:
    try:
        return enum_type(value)
    except ValueError as error:
        allowed_values = ", ".join(member.value for member in enum_type)
        raise InvalidContractDefinitionError(
            f"invalid {field_name}: {value!r}; expected one of {allowed_values}"
        ) from error


@dataclass(frozen=True, slots=True)
class ContractDefinition:
    """Immutable F-006 projection of one governed Interaction Contract."""

    interaction_contract_id: str
    version: str
    contract_type: ContractType | str
    owner_module_id: str
    owning_context: str
    owning_capability: str
    name: str
    semantic_purpose: str
    lifecycle: ContractLifecycle | str
    operational_status: ContractOperationalStatus | str
    criticality: ContractCriticality | str
    primary_consumer_or_use_case: str
    architectural_steward: str | None = None
    traceability_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not INTERACTION_CONTRACT_ID_PATTERN.fullmatch(self.interaction_contract_id):
            raise InvalidContractDefinitionError(
                f"invalid interaction contract identifier: {self.interaction_contract_id!r}"
            )
        if not SEMANTIC_VERSION_PATTERN.fullmatch(self.version):
            raise InvalidContractDefinitionError(f"invalid semantic version: {self.version!r}")

        for field_name in (
            "owner_module_id",
            "owning_context",
            "owning_capability",
            "name",
            "semantic_purpose",
            "primary_consumer_or_use_case",
        ):
            _require_nonblank_text(field_name, getattr(self, field_name))

        if self.architectural_steward is not None:
            _require_nonblank_text("architectural_steward", self.architectural_steward)
        if isinstance(self.traceability_references, str):
            raise InvalidContractDefinitionError("traceability_references must be an immutable collection")
        normalized_traceability_references = tuple(self.traceability_references)
        for reference in normalized_traceability_references:
            _require_nonblank_text("traceability reference", reference)

        object.__setattr__(
            self,
            "contract_type",
            _normalize_enum("contract type", self.contract_type, ContractType),
        )
        object.__setattr__(
            self,
            "lifecycle",
            _normalize_enum("contract lifecycle", self.lifecycle, ContractLifecycle),
        )
        object.__setattr__(
            self,
            "operational_status",
            _normalize_enum(
                "contract operational status",
                self.operational_status,
                ContractOperationalStatus,
            ),
        )
        object.__setattr__(
            self,
            "criticality",
            _normalize_enum("contract criticality", self.criticality, ContractCriticality),
        )
        object.__setattr__(self, "traceability_references", normalized_traceability_references)


class ContractRegistry:
    """Per-application Contract Registry with explicit registration and sealing."""

    def __init__(self, module_registry: ModuleRegistry) -> None:
        self._module_registry = module_registry
        self._contracts: dict[str, ContractDefinition] = {}
        self._ordered_contracts: tuple[ContractDefinition, ...] | None = None

    @property
    def is_sealed(self) -> bool:
        return self._ordered_contracts is not None

    def register(self, definition: ContractDefinition) -> None:
        if self.is_sealed:
            raise ContractRegistrySealedError("contract registry is sealed")
        if definition.interaction_contract_id in self._contracts:
            raise DuplicateContractError(
                f"duplicate interaction contract identifier: {definition.interaction_contract_id}"
            )
        if not self._module_registry.contains(definition.owner_module_id):
            raise UnknownContractOwnerError(
                f"contract {definition.interaction_contract_id!r} has unknown owner module "
                f"{definition.owner_module_id!r}"
            )
        self._contracts[definition.interaction_contract_id] = definition

    def register_many(self, definitions: Iterable[ContractDefinition]) -> None:
        for definition in definitions:
            self.register(definition)

    def get(self, interaction_contract_id: str) -> ContractDefinition | None:
        return self._contracts.get(interaction_contract_id)

    def contains(self, interaction_contract_id: str) -> bool:
        return interaction_contract_id in self._contracts

    def list(self) -> tuple[ContractDefinition, ...]:
        if self._ordered_contracts is not None:
            return self._ordered_contracts
        return tuple(self._contracts.values())

    def list_by_kind(self, contract_type: ContractType | str) -> tuple[ContractDefinition, ...]:
        normalized_contract_type = _normalize_enum("contract type", contract_type, ContractType)
        return tuple(definition for definition in self.list() if definition.contract_type == normalized_contract_type)

    def list_by_owner(self, owner_module_id: str) -> tuple[ContractDefinition, ...]:
        return tuple(definition for definition in self.list() if definition.owner_module_id == owner_module_id)

    def seal(self) -> None:
        if self.is_sealed:
            return
        self._ordered_contracts = tuple(self._contracts.values())


def build_contract_registry(
    module_registry: ModuleRegistry,
    contracts: Iterable[ContractDefinition] = (),
) -> ContractRegistry:
    """Build and seal one explicit Contract Registry for a single application."""

    registry = ContractRegistry(module_registry)
    registry.register_many(contracts)
    registry.seal()
    return registry
