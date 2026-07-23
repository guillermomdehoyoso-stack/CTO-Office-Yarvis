"""Canonical public interfaces for synchronous Yarvis Command Dispatch."""

from yarvis_api.dispatch.dispatcher import Dispatcher
from yarvis_api.dispatch.errors import (
    CommandNotDispatchableError,
    DispatchContractError,
    DispatchError,
    DuplicateHandlerError,
    HandlerOwnershipError,
    HandlerRegistryError,
    HandlerRegistrySealedError,
    IncompleteTransactionError,
    InvalidCommandCompletionError,
    InvalidHandlerDefinitionError,
    MissingHandlerError,
    UnknownDispatchContractError,
    UnsupportedContractKindError,
)
from yarvis_api.dispatch.models import CommandEnvelope, CommandUnitOfWork, HandlerDefinition
from yarvis_api.dispatch.registry import HandlerRegistry, build_handler_registry

__all__ = [
    "CommandEnvelope",
    "CommandNotDispatchableError",
    "CommandUnitOfWork",
    "DispatchContractError",
    "DispatchError",
    "Dispatcher",
    "DuplicateHandlerError",
    "HandlerDefinition",
    "HandlerOwnershipError",
    "HandlerRegistry",
    "HandlerRegistryError",
    "HandlerRegistrySealedError",
    "IncompleteTransactionError",
    "InvalidCommandCompletionError",
    "InvalidHandlerDefinitionError",
    "MissingHandlerError",
    "UnsupportedContractKindError",
    "UnknownDispatchContractError",
    "build_handler_registry",
]
