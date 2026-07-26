"""Shared application metadata contracts for WS-001."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class ActorType(StrEnum):
    HUMAN = "human"
    SYSTEM = "system"
    AGENT = "agent"
    CONNECTOR = "connector"


def _require_nonblank(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must be nonblank")


@dataclass(frozen=True, slots=True)
class ActorContext:
    actor_id: str
    actor_type: ActorType
    display_name: str | None = None

    def __post_init__(self) -> None:
        _require_nonblank("actor_id", self.actor_id)
        if self.display_name is not None and not self.display_name.strip():
            raise ValueError("display_name must be nonblank when provided")


@dataclass(frozen=True, slots=True)
class AuthorityContext:
    authority_scope: str
    organization_id: str | None = None
    requires_human_approval: bool = False
    delegated_by_actor_id: str | None = None

    def __post_init__(self) -> None:
        _require_nonblank("authority_scope", self.authority_scope)
        if self.organization_id is not None and not self.organization_id.strip():
            raise ValueError("organization_id must be nonblank when provided")
        if self.delegated_by_actor_id is not None and not self.delegated_by_actor_id.strip():
            raise ValueError("delegated_by_actor_id must be nonblank when provided")


@dataclass(frozen=True, slots=True)
class RequestMetadata:
    requested_at: datetime
    correlation_id: str
    command_id: str | None = None
    query_id: str | None = None
    causation_id: str | None = None
    idempotency_key: str | None = None
    expected_aggregate_version: int | None = None

    def __post_init__(self) -> None:
        _require_nonblank("correlation_id", self.correlation_id)
        if self.command_id is not None and not self.command_id.strip():
            raise ValueError("command_id must be nonblank when provided")
        if self.query_id is not None and not self.query_id.strip():
            raise ValueError("query_id must be nonblank when provided")
        if self.causation_id is not None and not self.causation_id.strip():
            raise ValueError("causation_id must be nonblank when provided")
        if self.idempotency_key is not None and not self.idempotency_key.strip():
            raise ValueError("idempotency_key must be nonblank when provided")
        if self.command_id is not None and self.query_id is not None:
            raise ValueError("command_id and query_id cannot both be set")
        if self.expected_aggregate_version is not None and self.expected_aggregate_version < 0:
            raise ValueError("expected_aggregate_version must be non-negative")
        if self.requested_at.tzinfo is None or self.requested_at.utcoffset() is None:
            raise ValueError("requested_at must be timezone-aware")


def utc_now_metadata(correlation_id: str) -> RequestMetadata:
    return RequestMetadata(requested_at=datetime.now(tz=timezone.utc), correlation_id=correlation_id)
