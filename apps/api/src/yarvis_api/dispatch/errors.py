"""Typed, deterministic failures for synchronous Command Dispatch."""

from __future__ import annotations


class DispatchError(ValueError):
    """Base error for structural Dispatch failures."""


class DispatchContractError(DispatchError):
    """A requested interaction contract cannot be dispatched."""


class UnknownDispatchContractError(DispatchContractError):
    """The requested interaction contract is not registered."""


class UnsupportedContractKindError(DispatchContractError):
    """The requested contract is not a Command."""


class CommandNotDispatchableError(DispatchContractError):
    """A Command is structurally known but operationally unavailable."""


class HandlerRegistryError(DispatchError):
    """Base error for Handler Registry lifecycle and validation failures."""


class InvalidHandlerDefinitionError(HandlerRegistryError):
    """A handler declaration is incomplete or unsupported."""


class DuplicateHandlerError(HandlerRegistryError):
    """A Command already has an authoritative handler."""


class MissingHandlerError(HandlerRegistryError):
    """A dispatchable Command has no registered handler."""


class HandlerRegistrySealedError(HandlerRegistryError):
    """A sealed Handler Registry cannot accept additional definitions."""


class HandlerOwnershipError(DispatchError):
    """Handler ownership does not match the canonical contract owner."""


class IncompleteTransactionError(DispatchError):
    """A handler returned without completing its active transaction."""


class InvalidCommandCompletionError(DispatchError):
    """A handler returned from an invalid Unit of Work terminal state."""
