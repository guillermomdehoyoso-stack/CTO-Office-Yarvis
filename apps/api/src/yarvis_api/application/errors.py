"""Stable application error model for WS-001 contract boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ApplicationErrorCode(StrEnum):
    VALIDATION_FAILED = "VALIDATION_FAILED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    TRANSIENT_FAILURE = "TRANSIENT_FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
    STALE_PROJECTION = "STALE_PROJECTION"
    UNCERTAIN_RESULT = "UNCERTAIN_RESULT"
    COMMAND_REJECTED = "COMMAND_REJECTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"


@dataclass(slots=True)
class ApplicationError(Exception):
    code: ApplicationErrorCode
    message: str
    details: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message must be nonblank")
        for key, value in self.details.items():
            if not key.strip():
                raise ValueError("details keys must be nonblank")
            if not value.strip():
                raise ValueError("details values must be nonblank")
