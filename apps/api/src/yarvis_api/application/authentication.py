"""Application-layer authentication contracts independent of transport protocols."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping


def _require_nonblank(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must be nonblank")


def _normalize_list(values: tuple[str, ...], *, field_name: str) -> tuple[str, ...]:
    normalized = tuple(item.strip() for item in values if item.strip())
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} entries must be unique")
    return normalized


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    actor_id: str
    organization_id: str | None
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    authority: str
    authentication_method: str
    authenticated_at: datetime
    is_system_actor: bool
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        _require_nonblank("actor_id", self.actor_id)
        _require_nonblank("authority", self.authority)
        _require_nonblank("authentication_method", self.authentication_method)
        if self.organization_id is not None and not self.organization_id.strip():
            raise ValueError("organization_id must be nonblank when provided")
        if self.correlation_id is not None and not self.correlation_id.strip():
            raise ValueError("correlation_id must be nonblank when provided")
        if self.authenticated_at.tzinfo is None or self.authenticated_at.utcoffset() is None:
            raise ValueError("authenticated_at must be timezone-aware")
        object.__setattr__(self, "roles", _normalize_list(tuple(self.roles), field_name="roles"))
        object.__setattr__(self, "permissions", _normalize_list(tuple(self.permissions), field_name="permissions"))


@dataclass(frozen=True, slots=True)
class TransportAuthenticationRequest:
    headers: Mapping[str, str]
    path: str | None = None
    method: str | None = None
    client_host: str | None = None
