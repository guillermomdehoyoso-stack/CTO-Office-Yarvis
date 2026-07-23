"""Immutable Command Dispatch declarations and restricted handler contracts."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, fields, is_dataclass
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from yarvis_api.dispatch.errors import InvalidHandlerDefinitionError


def _freeze_payload(value: object) -> object:
    """Create an isolated immutable snapshot for supported built-in payload values."""

    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if isinstance(value, tuple):
        return tuple(_freeze_payload(item) for item in value)
    if isinstance(value, frozenset):
        return frozenset(_freeze_payload(item) for item in value)
    if isinstance(value, MappingProxyType):
        return MappingProxyType({_freeze_payload(key): _freeze_payload(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_payload(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_payload(item) for item in value)
    if isinstance(value, dict):
        return MappingProxyType({_freeze_payload(key): _freeze_payload(item) for key, item in value.items()})
    if is_dataclass(value) and getattr(type(value), "__dataclass_params__").frozen:
        for field_definition in fields(value):
            _freeze_payload(getattr(value, field_definition.name))
        return value
    raise TypeError("payload must be immutable or use CommandEnvelope.snapshot")


def is_isolated_payload(value: object) -> bool:
    """Return whether a payload satisfies the F-009 ownership contract."""

    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return True
    if isinstance(value, tuple):
        return all(is_isolated_payload(item) for item in value)
    if isinstance(value, frozenset):
        return all(is_isolated_payload(item) for item in value)
    if isinstance(value, MappingProxyType):
        return all(is_isolated_payload(key) and is_isolated_payload(item) for key, item in value.items())
    if is_dataclass(value) and getattr(type(value), "__dataclass_params__").frozen:
        return all(is_isolated_payload(getattr(value, field_definition.name)) for field_definition in fields(value))
    return False


@dataclass(frozen=True, slots=True)
class CommandEnvelope:
    """Transport-neutral Command identity and isolated payload."""

    contract_id: str
    payload: object

    def __post_init__(self) -> None:
        if not isinstance(self.contract_id, str) or not self.contract_id.strip():
            raise ValueError("command contract identifier must be nonblank")
        if not is_isolated_payload(self.payload):
            raise TypeError("payload must be immutable or explicitly isolated")

    @classmethod
    def snapshot(cls, contract_id: str, payload: object) -> CommandEnvelope:
        """Build an envelope using the explicit built-in immutable snapshot mechanism."""

        return cls(contract_id=contract_id, payload=_freeze_payload(payload))


@runtime_checkable
class CommandUnitOfWork(Protocol):
    """The narrow transaction-intent port available to a Command handler."""

    def commit(self) -> None:
        """Request explicit transaction commit through the owned Unit of Work."""

    def rollback(self) -> None:
        """Request explicit transaction rollback through the owned Unit of Work."""


CommandHandler = Callable[[CommandEnvelope, CommandUnitOfWork], object | None]


@dataclass(frozen=True, slots=True)
class HandlerDefinition:
    """Immutable composition declaration for exactly one synchronous Command handler."""

    interaction_contract_id: str
    owner_module_id: str
    owning_context: str
    handler: CommandHandler
    handler_name: str

    def __post_init__(self) -> None:
        for field_name in ("interaction_contract_id", "owner_module_id", "owning_context", "handler_name"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidHandlerDefinitionError(f"{field_name} must be nonblank")
        if not callable(self.handler) or inspect.iscoroutinefunction(self.handler):
            raise InvalidHandlerDefinitionError("handler must be a synchronous callable")
