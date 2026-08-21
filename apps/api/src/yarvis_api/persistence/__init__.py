"""Application-owned synchronous persistence infrastructure."""

from yarvis_api.persistence.application_trace_store import ApplicationTraceStore
from yarvis_api.persistence.runtime import (
    PersistenceRuntime,
    PersistenceRuntimeDisposedError,
    PersistenceRuntimeOwnershipError,
    build_persistence_runtime,
    sqlalchemy_url,
)
from yarvis_api.persistence.unit_of_work import (
    NestedUnitOfWorkError,
    OperationScope,
    RepositoryOwnershipError,
    UnitOfWork,
    UnitOfWorkDisposedError,
    UnitOfWorkError,
    UnitOfWorkLifecycleError,
    UnitOfWorkState,
)

__all__ = [
    "PersistenceRuntime",
    "ApplicationTraceStore",
    "PersistenceRuntimeDisposedError",
    "PersistenceRuntimeOwnershipError",
    "build_persistence_runtime",
    "sqlalchemy_url",
    "NestedUnitOfWorkError",
    "OperationScope",
    "RepositoryOwnershipError",
    "UnitOfWork",
    "UnitOfWorkDisposedError",
    "UnitOfWorkError",
    "UnitOfWorkLifecycleError",
    "UnitOfWorkState",
]
